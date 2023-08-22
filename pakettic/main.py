from cmath import inf
import argparse
import io
import struct
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


def main():
    """Main entrypoint for the command line program"""
    sys.setrecursionlimit(100000)  # TODO: find out why the parser recurses so heavily and reduce that

    version = pkg_resources.get_distribution('pakettic').version
    argparser = argparse.ArgumentParser(
        prog='pakettic', description=f'Minify and compress TIC-80 fantasy console carts. v{version}',
        formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=33))
    argparser.add_argument('input', nargs='+', help='input file(s). ?, * and ** wildcards work')
    argparser.add_argument('-o', '--output', default=os.getcwd(), metavar='str', help='output file or directory')
    argparser.add_argument('-l', '--lua', action='store_const', const=True,
                           help='set output format as .lua cart')
    argparser.add_argument('-u', '--uncompressed', action='store_const', const=True,
                           help='set output format as uncompressed .tic cart')
    argparser.add_argument('-g', '--png', action='store_const', const=True,
                           help='set output format as .png cart')
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
                          help='number of steps in the optimization algorithm. default: %(default)d')
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

    def compress(bytes=None, drop_checksum=True):
        c = zopfli.ZopfliCompressor(zopfli.ZOPFLI_FORMAT_ZLIB, block_splitting=args.split,
                                    block_splitting_max=args.split_max, iterations=args.iterations)
        data = (c.compress(bytes) + c.flush())
        return data[0:-4] if drop_checksum else data

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
            output_filepath = os.path.join(args.output, filename + '.packed' + ('.lua' if args.lua else '.tic'))
        else:
            output_filepath = args.output
        original_size = os.path.getsize(input_filepath)
        filepath_sliced = input_filepath[-30:] if len(input_filepath) > 30 else input_filepath
        filepbar.set_description(f"Reading       {filepath_sliced}")
        try:
            cart = ticfile.read(input_filepath)
        except Exception as e:
            filepbar.write(f"Error reading {input_filepath}: {e}, skipping...")
            error = True
            continue
        filepbar.set_description(f"Decompressing {filepath_sliced}")
        if (0, ticfile.ChunkID.CODE_ZIP) in cart:
            cart[(0, ticfile.ChunkID.CODE)] = zlib.decompress(cart[(0, ticfile.ChunkID.CODE_ZIP)][2:], -15)
            del cart[(0, ticfile.ChunkID.CODE_ZIP)]
        cart[(0, ticfile.ChunkID.DEFAULT)] = b''  # add default chunk if it's missing
        cart = dict(c for i in args.chunks for c in cart.items() if c[0][1] == i)  # only include the chunks listed in args
        if args.data_to_code:
            ticfile.data_to_code(cart)
        code = cart[0, ticfile.ChunkID.CODE].decode("ascii")

        filepbar.set_description(f"Compressing   {filepath_sliced}")
        if not args.uncompressed and not args.lua and not args.png:
            bytes = compress(cart[0, ticfile.ChunkID.CODE])
            cart = dict(((0, ticfile.ChunkID.CODE_ZIP), bytes) if i[0][1] == ticfile.ChunkID.CODE else i for i in cart.items())
        with (io.open(output_filepath, "w", newline='\n') if args.lua else io.open(output_filepath, "wb")) as file:
            if args.lua:
                final_size = ticfile.write_lua(cart, file)
            else:
                if args.png:
                    c = lambda b: compress(b, drop_checksum=False)
                else:
                    c = None
                final_size = ticfile.write_tic(cart, file, pedantic=args.pedantic, compress=c)

        root = parser.parse_string(code)
        root = optimize.loads_to_funcs(root)
        root = optimize.minify(root)
        root = ast.Hint(root)

        def _cost_func(root, best_cost):
            nonlocal final_size
            bytes = printer.format(root, no_load=args.no_load).encode("ascii")
            chunkID = ticfile.ChunkID.CODE
            if not args.uncompressed and not args.lua and not args.png:
                bytes = compress(bytes)
                chunkID = ticfile.ChunkID.CODE_ZIP
            if args.png:
                newcart = cart.copy()
                newcart[0, ticfile.ChunkID.CODE] = bytes
                bytesIO = io.BytesIO()
                ticfile.write_tic(newcart, bytesIO, pedantic=args.pedantic, compress=lambda b: compress(b, drop_checksum=False))
                ret = len(bytesIO.getvalue())
            else:
                chunkedlength = lambda l: l + (l - 1) // 65536 * 4 + 4  # length of code after splitted to chunks
                diff = chunkedlength(len(bytes)) - chunkedlength(len(cart[0, chunkID]))
                ret = final_size + diff
            ret -= args.target_size
            if args.exact:
                ret = abs(ret)
            if ret < best_cost:
                cart[0, chunkID] = bytes
                with (io.open(output_filepath, "w", newline='\n') if args.lua else io.open(output_filepath, "wb")) as file:
                    if args.lua:
                        final_size = ticfile.write_lua(cart, file)
                    elif args.png:
                        final_size = file.write(bytesIO.getvalue())
                    else:
                        final_size = ticfile.write_tic(cart, file, pedantic=args.pedantic)
                if args.print_best:
                    filepbar.write(f"-- {ret} bytes:\n{'-'*40}\n{printer.format(root, pretty=True).strip()}\n{'-'*40}")
            return ret
        _cost_func(root, inf)
        minified_size = final_size  # current final_size is the size after minification
        if args.algorithm == 'lahc':
            root = optimize.lahc(root, steps=args.steps, cost_func=_cost_func,
                                 list_length=args.lahc_history, init_margin=args.margin, seed=args.seed)
        elif args.algorithm == 'dlas':
            root = optimize.dlas(root, steps=args.steps, cost_func=_cost_func,
                                 list_length=args.dlas_history, init_margin=args.margin, seed=args.seed)
        else:
            root = optimize.anneal(root, steps=args.steps, cost_func=_cost_func,
                                   start_temp=args.start_temp, end_temp=args.end_temp, seed=args.seed)
        total_original_size += original_size
        total_optimized_size += final_size
        total_minified_size += minified_size
        cart_time_str = '.'.join(str(datetime.timedelta(seconds=int(time.time() - cart_start_time))).split(':'))
        filepbar.write(f"{input_filepath.ljust(maxpathlen)} Time:{cart_time_str} Orig:{original_size:<5} Min:{minified_size:<5} Pack:{final_size:<5}")
    if len(input) > 1:
        total_time_str = str(datetime.timedelta(seconds=int(time.time() - total_start_time)))
        print("-" * 80 + f"\n{'Totals'.ljust(maxpathlen)} Time:{total_time_str} Orig:{total_original_size:<5} Min:{total_minified_size:<5} Pack:{total_optimized_size:<5}")
    sys.exit(1 if error else 0)


if __name__ == '__main__':
    main()
