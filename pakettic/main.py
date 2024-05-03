from cmath import inf
import argparse
import io
import pickle
import struct
from typing import Callable
from pakettic import ast
from glob import glob
import os
import sys
import zlib
import pkg_resources
import zopfli
import time
import datetime

from pakettic import parser, printer, optimize, ticfile
import tqdm


def _parse_chunks_arg(arg: str) -> list[ticfile.ChunkID]:
    """Parse the --chunks command line arugment into a list of chunk types"""
    a = arg.upper()
    if a == 'ALL' or a == 'ALL_EXCEPT_DEFAULT':
        chunk_types = [e for e in ticfile.ChunkID if e !=
                       ticfile.ChunkID.CODE_ZIP and e != ticfile.ChunkID.DEFAULT]
        if a == 'ALL':
            chunk_types = [ticfile.ChunkID.DEFAULT] + chunk_types
    else:
        chunk_types = []
        for chunk_id_name in a.split(','):
            x = getattr(ticfile.ChunkID, chunk_id_name.upper())
            if x is None:
                sys.exit(f"Unknown chunk type entered on command line: {chunk_id_name}")
            chunk_types.append(x)
        chunk_types = list(dict.fromkeys(chunk_types))  # remove duplicates
    return chunk_types


_ZOPFLI_LEVELS = [
    {"iterations": 1, "split": False, "split_max": 0},
    {"iterations": 5, "split": False, "split_max": 0},
    {"iterations": 15, "split": True, "split_max": 1},
    {"iterations": 15, "split": True, "split_max": 3},
    {"iterations": 200, "split": True, "split_max": 0},
    {"iterations": 500, "split": True, "split_max": 0}
]


def _parse_zopfli_level(arg: str) -> dict:
    """Parse the --zopfli-level command line argument into a dictionary containing the zopfli parameters"""
    try:
        level = int(arg)
        if level < 0 or level > 5:
            raise argparse.ArgumentTypeError()
        return _ZOPFLI_LEVELS[level]
    except:
        raise argparse.ArgumentTypeError("Compression level should be an integer 0-5")


def _check_positive(value):
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError("%s is an invalid positive int value" % value)
    return ivalue


def main():
    global args
    """Main entrypoint for the command line program"""
    sys.setrecursionlimit(100000)  # TODO: find out why the parser recurses so heavily and reduce that

    version = pkg_resources.get_distribution('pakettic').version
    argparser = argparse.ArgumentParser(
        prog='pakettic', description=f'Minify and compress TIC-80 fantasy console carts. v{version}',
        formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=33))
    argparser.add_argument('input', nargs='+', help='input file(s). ?, * and ** wildcards work')
    argparser.add_argument('-o', '--output', default=os.getcwd(), metavar='str', help='output file or directory')
    argparser.add_argument('-l', '--lua', action='store_const', const=True,
                           help='DEPRECATED: same as -f lua')
    argparser.add_argument('-u', '--uncompressed', action='store_const', const=True,
                           help='DEPRECATED: same as -f unc')
    argparser.add_argument('-f', '--output-format',
                           action='store',
                           type=str.lower,
                           metavar='str',
                           help="output-format, tic (.tic cart with code compressed as CODE_ZIP), unc (.tic cart with uncompressed code), png (.tic cart that looks like PNG, can compress data sections too), lua (.lua text cart). Default: based on output file name or tic.",
                           required=False,
                           choices=["tic", "unc", "lua", "png"])
    argparser.add_argument('-p', '--print-best', action='store_const', const=True,
                           help='pretty-print the best solution when found')
    argparser.add_argument('-c', '--chunks',
                           default='code,default', metavar='str', help='chunk types to include and their order. valid: ALL, ALL_EXCEPT_DEFAULT, or comma-separated list without spaces: BINARY,CODE,COVER_DEP,DEFAULT,FLAGS,MAP,MUSIC,PALETTE,PATTERNS_DEP,PATTERNS,SAMPLES,SCREEN,SPRITES,TILES,WAVEFORM. default: %(default)s',
                           type=_parse_chunks_arg)
    argparser.add_argument('-d', '--data-to-code', action='store_const', const=True, default=False, help='convert data chunks into code, so they can be compressed')
    argparser.add_argument('--pedantic', action='store_const', const=True, default=False,
                           help='write DEFAULT chunk in full even when it is the last chunk')
    argparser.add_argument('--no-load', action='store_const', const=True, default=False,
                           help="disable converting function()end into load''")
    optgroup = argparser.add_argument_group('optional arguments for the optimization algorithm')
    optgroup.add_argument('-a', '--algorithm',
                          action='store',
                          type=str.lower,
                          metavar='str',
                          help="optimization algorithm, LAHC (late acceptance hill climbing), DLAS (diversified late acceptance search) or ANNEAL (simulated annealing). Default: %(default)s",
                          required=False,
                          choices=["lahc", "dlas", "anneal"],
                          default="dlas")
    optgroup.add_argument('-s', '--steps', type=int, default=10000, metavar='int',
                          help='number of steps in the optimization algorithm. 0 = iterate forever (intermediate results saved). default: %(default)d')
    optgroup.add_argument('-q', '--queue-length', type=_check_positive, default=12, metavar='int',
                          help='number of parallel jobs in queue. to use all CPUs, this should be >= number of logical processors. too long queue slows down convergence. default: %(default)d')
    optgroup.add_argument('-P', '--processes', type=_check_positive, default=None, metavar='int',
                          help='number of parallel processes. 1 = no parallel processing. defaults to number of available logical processors.')
    optgroup.add_argument('-H', '--lahc-history', type=int, default=500, metavar='int',
                          help='history length in late acceptance hill climbing. default: %(default)d')
    optgroup.add_argument('-D', '--dlas-history', type=int, default=5, metavar='int',
                          help='history length in diversified late acceptance search. default: %(default)d')
    optgroup.add_argument('-m', '--margin', type=float, default=0, metavar='float',
                          help='initialize the lahc/dlas history with initial_cost + margin (in bytes). Default: %(default).0f')
    optgroup.add_argument('-t', '--start-temp', type=float, default=1, metavar='float',
                          help='starting temperature for simulated annealing, >0. default: %(default).1f')
    optgroup.add_argument('-T', '--end-temp', type=float, default=0.1, metavar='float',
                          help='ending temperature for simulated annealing, >0. default: %(default).1f')
    optgroup.add_argument('--target-size', type=int, default=0, metavar='int',
                          help='stop compression when target size is reached. default: %(default)d')
    optgroup.add_argument('--exact', action='store_const', const=True,
                          help='used with --target-size to indicate that the size should be reached exactly')
    optgroup.add_argument('--seed', type=int, default=0, metavar='int',
                          help='random seed. default: %(default)d')
    zopfligroup = argparser.add_argument_group('optional arguments for tuning zopfli')
    zopfligroup.add_argument('-z', '--zopfli-level', type=_parse_zopfli_level, default=_ZOPFLI_LEVELS[0], metavar='int',
                             help='generic compression level for zopfli, 0-5. default: 0')
    zopfligroup.add_argument('--iterations', type=int, metavar='int',
                             help='number of iterations in zopfli. default: based on compression level')
    zopfligroup.add_argument('--split', action=argparse.BooleanOptionalAction,
                             help='enable or disable block splitting in zopfli. default: based on compression level')
    zopfligroup.add_argument('--split-max', type=int, metavar='int',
                             help='maximum number of block splittings in zopfli (0: infinite). default: based on compression level')
    args = argparser.parse_args()

    if args.split is None:
        args.split = args.zopfli_level["split"]
    if args.split_max is None:
        args.split_max = args.zopfli_level["split_max"]
    if args.iterations is None:
        args.iterations = args.zopfli_level["iterations"]

    # these are deprecated, can be removed when we bump the version
    if args.lua:
        args.output_format = "lua"
    if args.uncompressed:
        args.output_format = "unc"

    # if we still don't have output_format, try to guess it based on the output file extension
    if args.output_format is None:
        if not os.path.isdir(args.output):
            ext = os.path.splitext(args.output)[1].lower()
            if ext == '.lua':
                args.output_format = "lua"
            else:
                args.output_format = "tic"
        else:
            args.output_format = "tic"

    input = []
    # use glob to find files matching wildcards
    # if a string does not contain a wildcard, glob will return it as is.
    for arg in args.input:
        input += glob(arg, recursive=True)
    if len(input) > 1 and not os.path.isdir(args.output):
        sys.exit('When multiple input files are defined, the output must be a directory.')
    if len(input) == 0:
        sys.exit('No input files found.')
    input = sorted(input)  # sort the input files so corpus will be reported in same order
    filepbar = tqdm.tqdm(input, leave=False, smoothing=0.02)
    error = False
    total_original_size = 0
    total_minified_size = 0
    total_optimized_size = 0
    total_start_time = time.time()
    maxpathlen = max(len(p) for p in input)
    for input_filepath in filepbar:
        cart_start_time = time.time()
        _, filename = os.path.split(os.path.splitext(input_filepath)[0])
        if os.path.isdir(args.output):
            if args.output_format == 'lua':
                ext = '.lua'
            else:
                ext = '.tic'
            output_filepath = os.path.join(
                args.output, filename + '.packed' + ext)
        else:
            output_filepath = args.output
        original_size = os.path.getsize(input_filepath)
        try:
            minified_size, optimized_size = _process_file(input_filepath, output_filepath, filepbar)
        except KeyboardInterrupt:
            error = True
            filepbar.write(f"Interrupt processing {input_filepath}")
            break
        total_original_size += original_size
        total_optimized_size += optimized_size
        total_minified_size += minified_size
        cart_time_str = '.'.join(str(datetime.timedelta(seconds=int(time.time() - cart_start_time))).split(':'))
        filepbar.write(f"{input_filepath.ljust(maxpathlen)} Time:{cart_time_str} Orig:{original_size:<5} Min:{minified_size:<5} Pack:{optimized_size:<5}")
    if len(input) > 1:
        total_time_str = str(datetime.timedelta(seconds=int(time.time() - total_start_time)))
        print("-" * 80 + f"\n{'Totals'.ljust(maxpathlen)} Time:{total_time_str} Orig:{total_original_size:<5} Min:{total_minified_size:<5} Pack:{total_optimized_size:<5}")
    sys.exit(1 if error else 0)


def _process_file(input_path, output_filepath, pbar) -> tuple[int, int]:
    # These are global for performance reasons. When multiprocessing, globals
    # are not copied to child processes, so we pass them as arguments to the
    # process initialize (_initializer) function, which set the globals for that
    # process
    global args, writer

    input_sliced = input_path[-30:] if len(input_path) > 30 else input_path
    pbar.set_description(f"Processing    {input_sliced}")
    cart = ticfile.read(input_path)
    def_chunk = (0, ticfile.ChunkID.DEFAULT, b'')
    if def_chunk not in cart.data:  # add default chunk if it's missing
        cart.data.append(def_chunk)
    cart.data = [(bank, id, bytes)
                 for bank, id, bytes in cart.data if id in args.chunks]
    if args.data_to_code:
        cart = ticfile.data_to_code(cart)

    pbar.set_description(f"Compressing   {input_sliced}")
    root = parser.parse_string(cart.code.decode('latin-1'))
    root = optimize.loads_to_funcs(root)
    root = optimize.minify(root)
    root = ast.Hint(root)
    # writer caches as much as possible of the data writing so that we don't have to recompute data parts for each optimization step
    writer = _make_writer(cart.data)
    minified_size, finisher = writer(_format(root))
    with open(output_filepath, 'wb') as output_file:
        final_size = finisher(output_file)
    assert final_size == minified_size

    def _best_func(state, cf):
        nonlocal final_size
        cand_size, finisher = cf
        with open(output_filepath, 'wb') as output_file:
            final_size = finisher(output_file)
        assert final_size == cand_size
        if args.print_best:
            pbar.write(f"-- {final_size} bytes:\n{'-'*40}\n{printer.format(pickle.loads(state)[0], pretty=True).strip()}\n{'-'*40}")

    # only PNG carts cab benefit from data chunk order shuffling
    data = cart.data if args.output_format == 'png' else None

    with optimize.Solutions((root, data), args.seed, args.queue_length, args.processes, _cost_func, _best_func, _initializer, (args, writer)) as solutions:
        if args.algorithm == 'lahc':
            optimize.lahc(solutions, steps=args.steps, list_length=args.lahc_history, init_margin=args.margin)
        elif args.algorithm == 'dlas':
            optimize.dlas(solutions, steps=args.steps, list_length=args.dlas_history, init_margin=args.margin)
        else:
            optimize.anneal(solutions, steps=args.steps, start_temp=args.start_temp, end_temp=args.end_temp, seed=args.seed)
    return minified_size, final_size


def _compress(bytes=None):
    global args
    c = zopfli.ZopfliCompressor(zopfli.ZOPFLI_FORMAT_ZLIB, block_splitting=args.split,
                                block_splitting_max=args.split_max, iterations=args.iterations)
    return (c.compress(bytes) + c.flush())


def _format(root: ast.Node) -> bytes:
    global args
    return printer.format(root, no_load=args.no_load).encode('latin-1')


def _make_writer(data) -> ticfile.Writer:
    global args
    if args.output_format == 'lua':
        return ticfile.write_lua(data)
    elif args.output_format == 'png':
        return ticfile.write_png(data, args.pedantic, _compress)
    elif args.output_format == 'unc':
        return ticfile.write_tic(data, args.pedantic, None)
    else:
        return ticfile.write_tic(data, args.pedantic, _compress)


def _initializer(a):
    global args, writer
    args, writer = a


def _cost_func(root_data):
    global args, writer
    root, data = root_data
    if data is not None:  # PNG carts shuffle the data chunks so we cannot cache the data parts & have to regenerate writer for each step
        cand_size, finisher = _make_writer(data)(_format(root))
    else:
        cand_size, finisher = writer(_format(root))
    cand_cost = cand_size - args.target_size
    if args.exact:
        cand_cost = abs(cand_cost)
    return cand_cost, (cand_size, finisher)


if __name__ == '__main__':
    main()
