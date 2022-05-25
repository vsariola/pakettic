import argparse
from glob import glob
import io
import itertools
import os
import sys
import warnings
import zlib
import pkg_resources
import zopfli

from pakettic import parser, printer, optimize, ticfile
import tqdm


def _parse_chunks_arg(arg: str) -> list[ticfile.ChunkID]:
    """Parses the chunk type arg (ALL, ALL_EXCEPT_DEFAULT or comma-separated list of chunk types) into a list of chunk types"""
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


_COMPRESSION_LEVELS = [
    {"iterations": 1, "split": False, "split_max": 0},
    {"iterations": 5, "split": False, "split_max": 0},
    {"iterations": 15, "split": True, "split_max": 1},
    {"iterations": 15, "split": True, "split_max": 3},
    {"iterations": 200, "split": True, "split_max": 0},
    {"iterations": 500, "split": True, "split_max": 0}
]


def _parse_compression(arg: str) -> dict:
    try:
        level = int(arg)
        if level < 0 or level > 5:
            raise argparse.ArgumentTypeError()
        return _COMPRESSION_LEVELS[level]
    except:
        raise argparse.ArgumentTypeError("Compression level should be an integer 0-5")


def _compress(bytes, split, split_max, iterations):
    c = zopfli.ZopfliCompressor(zopfli.ZOPFLI_FORMAT_ZLIB, block_splitting=split,
                                block_splitting_max=split_max, iterations=iterations)
    return (c.compress(bytes) + c.flush())[: -4]


def main():
    sys.setrecursionlimit(100000)  # TODO: find out why the parser recurses so heavily and reduce that

    version = pkg_resources.get_distribution('pakettic').version
    argparser = argparse.ArgumentParser(
        prog='pakettic', description=f'Minify and compress TIC-80 fantasy console carts. v{version}',
        formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=33))
    argparser.add_argument('input', nargs='+', help='input file(s). ?, * and ** wildcards work')
    argparser.add_argument('-o', '--output', default=os.getcwd(), help='output file or directory')
    argparser.add_argument('-u', '--uncompressed', action='store_const', const=True,
                           help='leave code chunks uncompressed, even when outputting a .tic file')
    argparser.add_argument('-l', '--lua', action='store_const', const=True,
                           help='output .lua carts instead of .tic carts')
    argparser.add_argument('-t', '--target-size', type=int, default=0, metavar='BYTES',
                           help='when target size is reached, stop compressing prematurely. default: 0')
    argparser.add_argument('--exact', action='store_const', const=True,
                           help='used with target-size to indicate that the target size should be reached exactly')
    argparser.add_argument('-i', '--iterations', type=int, default=10000, metavar='ITERS',
                           help='number of steps in the optimization algorithm. default: 10000')
    argparser.add_argument('-p', '--print-best', action='store_const', const=True,
                           help='pretty print the best solution when found')
    argparser.add_argument('--start-temp', type=float, default=1, metavar='BYTES',
                           help='starting temperature. default: 1')
    argparser.add_argument('--end-temp', type=float, default=0.1, metavar='BYTES',
                           help='ending temperature. default: 0.1')
    argparser.add_argument('-z', '--compression', type=_parse_compression, default=_COMPRESSION_LEVELS[2],
                           help='general zopfli aggressiveness, 0-5. default: 2')
    argparser.add_argument('-s', '--split', action=argparse.BooleanOptionalAction,
                           help='enable/disable block splitting in zopfli')
    argparser.add_argument('-m', '--split-max', type=int, metavar='ITERS',
                           help='maximum number of block splittings in zopfli. 0 = infinite')
    argparser.add_argument('-n', '--zopfli-iterations', type=int, metavar='ITERS',
                           help='how many iterations zopfli uses')
    argparser.add_argument('-c', '--chunks',
                           default='code,default', metavar='CHUNKS', help='chunk types to include and their order. valid: ALL, ALL_EXCEPT_DEFAULT, or comma-separated list without spaces: BINARY,CODE,COVER_DEP,DEFAULT,FLAGS,MAP,MUSIC,PALETTE,PATTERNS_DEP,PATTERNS,SAMPLES,SCREEN,SPRITES,TILES,WAVEFORM. default: CODE,DEFAULT',
                           type=_parse_chunks_arg)
    args = argparser.parse_args()

    if args.lua:
        args.uncompressed = True  # Outputting LUA and compressing are mutually exclusive
    if args.split is None:
        args.split = args.compression["split"]
    if args.split_max is None:
        args.split_max = args.compression["split_max"]
    if args.zopfli_iterations is None:
        args.zopfli_iterations = args.compression["iterations"]

    input = []
    # use glob to find files matching wildcards
    # if a string does not contain a wildcard, glob will return it as is.
    for arg in args.input:
        input += glob(arg, recursive=True)
    if len(input) > 1 and not os.path.isdir(args.output):
        sys.exit('When multiple input files are defined, the output must be a directory.')
    if len(input) == 0:
        sys.exit('No input files found.')
    filepbar = tqdm.tqdm(input, leave=False, smoothing=0.02)
    error = False
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
            (k[0], ticfile.ChunkID.CODE_ZIP), _compress(v, args.split, args.split_max, args.zopfli_iterations)) for k, v in cart.items())
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
                    bytes = _compress(bytes, args.split, args.split_max, args.zopfli_iterations)
                diff = len(bytes) - len(outcart[key])
                ret = final_size + diff - args.target_size
                if args.exact:
                    ret = abs(ret)
                if ret < best_cost:
                    outcart[key] = bytes
                    final_size = ticfile.write(outcart, outfile)
                    if args.print_best:
                        filepbar.write(f"{ret} bytes:\n{'-'*40}\n{printer.format(root, pretty=True).strip()}\n{'-'*40}")
                return ret
            ast = optimize.anneal(ast, iterations=args.iterations, cost_func=_cost_func,
                                  start_temp=args.start_temp, end_temp=args.end_temp)
        filepbar.write(f"{filepath_sliced:<30} Original: {original_size} bytes. Packed: {final_size} bytes.")
    sys.exit(1 if error else 0)


if __name__ == '__main__':
    main()
