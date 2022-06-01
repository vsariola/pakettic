import argparse
from glob import glob
import os
import sys
import zlib
import pkg_resources
import zopfli

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


def _compress(bytes, split, split_max, iterations):
    """Compress a byte string using Zopfli, dropping the check sum"""
    c = zopfli.ZopfliCompressor(zopfli.ZOPFLI_FORMAT_ZLIB, block_splitting=split,
                                block_splitting_max=split_max, iterations=iterations)
    return (c.compress(bytes) + c.flush())[: -4]


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
                           help='output .lua carts instead of .tic carts')
    argparser.add_argument('-u', '--uncompressed', action='store_const', const=True,
                           help='leave code chunks uncompressed, even when outputting a .tic file')
    argparser.add_argument('-p', '--print-best', action='store_const', const=True,
                           help='pretty-print the best solution when found')
    argparser.add_argument('-c', '--chunks',
                           default='code,default', metavar='str', help='chunk types to include and their order. valid: ALL, ALL_EXCEPT_DEFAULT, or comma-separated list without spaces: BINARY,CODE,COVER_DEP,DEFAULT,FLAGS,MAP,MUSIC,PALETTE,PATTERNS_DEP,PATTERNS,SAMPLES,SCREEN,SPRITES,TILES,WAVEFORM. default: %(default)s',
                           type=_parse_chunks_arg)
    argparser.add_argument('--pedantic', action='store_const', const=True, default=False,
                           help='write DEFAULT chunk in full even when it is the last chunk')
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
    zopfligroup = argparser.add_argument_group('optional arguments for tuning zopfli')
    zopfligroup.add_argument('-z', '--zopfli-level', type=_parse_zopfli_level, default=_ZOPFLI_LEVELS[2], metavar='int',
                             help='generic compression level for zopfli, 0-5. default: 2')
    zopfligroup.add_argument('--iterations', type=int, metavar='int',
                             help='number of iterations in zopfli. default: based on compression level')
    zopfligroup.add_argument('--split', action=argparse.BooleanOptionalAction,
                             help='enable or disable block splitting in zopfli. default: based on compression level')
    zopfligroup.add_argument('--split-max', type=int, metavar='int',
                             help='maximum number of block splittings in zopfli (0: infinite). default: based on compression level')
    args = argparser.parse_args()

    if args.lua:
        args.uncompressed = True  # Outputting LUA and compressing are mutually exclusive
    if args.split is None:
        args.split = args.zopfli_level["split"]
    if args.split_max is None:
        args.split_max = args.zopfli_level["split_max"]
    if args.iterations is None:
        args.iterations = args.zopfli_level["iterations"]

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
    total_size = 0
    for filepath in filepbar:
        _, filename = os.path.split(os.path.splitext(filepath)[0])
        ext = '.lua' if args.lua else '.tic'
        outfile = os.path.join(args.output, filename + '.packed' + ext) if os.path.isdir(args.output) else args.output
        original_size = os.path.getsize(filepath)
        filepath_sliced = filepath[-30:] if len(filepath) > 30 else filepath
        filepbar.set_description(f"Reading       {filepath_sliced}")
        try:
            cart = ticfile.read(filepath)
        except Exception as e:
            filepbar.write(f"Error reading {filepath}: {e}, skipping...")
            error = True
            continue
        filepbar.set_description(f"Decompressing {filepath_sliced}")
        cart.update([((k[0], ticfile.ChunkID.CODE), zlib.decompress(v[2:], -15))
                    for k, v in cart.items() if k[1] == ticfile.ChunkID.CODE_ZIP])  # decompress zipped chunks
        cart[(0, ticfile.ChunkID.DEFAULT)] = b''  # add default chunk if it's missing
        cart = dict(c for i in args.chunks for c in cart.items() if c[0][1] == i)  # only include the chunks listed in args
        filepbar.set_description(f"Compressing   {filepath_sliced}")
        outcart = cart.copy() if args.uncompressed else dict((k, v) if k[1] != ticfile.ChunkID.CODE else (
            (k[0], ticfile.ChunkID.CODE_ZIP), _compress(v, args.split, args.split_max, args.iterations)) for k, v in cart.items())
        final_size = ticfile.write(outcart, outfile)
        code_chunks = [c for c in cart if c[1] == ticfile.ChunkID.CODE]
        for c in code_chunks:
            code = cart[c].decode("ascii")
            ast = parser.parse_string(code)
            ast = optimize.loads_to_funcs(ast)

            def _cost_func(root, best_cost):
                nonlocal final_size
                bytes = printer.format(root).encode("ascii")
                key = c
                if not args.uncompressed:
                    key = (c[0], ticfile.ChunkID.CODE_ZIP)
                    bytes = _compress(bytes, args.split, args.split_max, args.iterations)
                diff = len(bytes) - len(outcart[key])
                ret = final_size + diff - args.target_size
                if args.exact:
                    ret = abs(ret)
                if ret < best_cost:
                    outcart[key] = bytes
                    final_size = ticfile.write(outcart, outfile, pedantic=args.pedantic)
                    if args.print_best:
                        filepbar.write(f"{ret} bytes:\n{'-'*40}\n{printer.format(root, pretty=True).strip()}\n{'-'*40}")
                return ret
            if args.algorithm == 'lahc':
                ast = optimize.lahc(ast, steps=args.steps, cost_func=_cost_func,
                                    list_length=args.lahc_history, init_margin=args.margin)
            elif args.algorithm == 'dlas':
                ast = optimize.dlas(ast, steps=args.steps, cost_func=_cost_func,
                                    list_length=args.dlas_history, init_margin=args.margin)
            else:
                ast = optimize.anneal(ast, steps=args.steps, cost_func=_cost_func,
                                      start_temp=args.start_temp, end_temp=args.end_temp)
        total_size += final_size
        filepbar.write(f"{filepath} - Original: {original_size} bytes - Packed: {final_size} bytes")
    if len(input) > 1:
        print("-" * 40 + f"\nTotal packed size: {total_size} bytes")
    sys.exit(1 if error else 0)


if __name__ == '__main__':
    main()
