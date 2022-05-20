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


def main():
    sys.setrecursionlimit(100000)  # TODO: find out why the parser recurses so heavily and reduce that

    version = pkg_resources.get_distribution('pakettic').version
    argparser = argparse.ArgumentParser(
        prog='pakettic', description=f'Minify and compress TIC-80 fantasy console carts. v{version}')
    argparser.add_argument('input', nargs='+', help='Input file(s). * and ** work for wildcards and recursion.')
    argparser.add_argument('-o', '--output', default=os.getcwd(), metavar='output', help='Output file or directory.')
    argparser.add_argument('-u', '--uncompressed', action='store_const', const=True,
                           help='Leave code chunks uncompressed, even when outputting a .tic file.')
    argparser.add_argument('-t', '--target-size', type=int, default=0,
                           help='When target size is reached, stop compressing prematurely. Default value: 0')
    argparser.add_argument('-i', '--iterations', type=int, default=10000,
                           help='Number of steps in the optimization algorithm')
    argparser.add_argument('-l', '--lua', action='store_const', const=True,
                           help='Output .lua carts instead of .tic carts.')
    argparser.add_argument('-c', '--chunks',
                           default='code,default', metavar='chunk', help='Chunks to include and their order. Valid values: ALL, ALL_EXCEPT_DEFAULT, or a comma separated list of chunk types without spaces (BINARY,CODE,COVER_DEP,DEFAULT,FLAGS,MAP,MUSIC,PALETTE,PATTERNS_DEP,PATTERNS,SAMPLES,SCREEN,SPRITES,TILES,WAVEFORM). Default value: CODE,DEFAULT.',
                           type=_parse_chunks_arg)
    args = argparser.parse_args()
    if args.lua:
        args.uncompressed = True  # Outputting LUA and compressing are mutually exclusive
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
        originalSize = os.path.getsize(filepath)
        filepathSliced = filepath[-30:] if len(filepath) > 30 else filepath
        filepbar.set_description(f"Reading       {filepathSliced}")
        try:
            cart = ticfile.read(filepath)
        except Exception as e:
            filepbar.write(f"Error reading {filepath}: {e}, skipping...")
            error = True
            continue
        filepbar.set_description(f"Decompressing {filepathSliced}")
        cart.update([((k[0], ticfile.ChunkID.CODE), zlib.decompress(v[2:], -15))
                    for k, v in cart.items() if k[1] == ticfile.ChunkID.CODE_ZIP])  # decompress zipped chunks
        cart[(0, ticfile.ChunkID.DEFAULT)] = b''  # add default chunk if it's missing
        cart = dict(c for i in args.chunks for c in cart.items() if c[0][1] == i)  # only include the chunks listed in args
        filepbar.set_description(f"Compressing   {filepathSliced}")
        codeChunks = [c for c in cart if c[1] == ticfile.ChunkID.CODE]
        for c in codeChunks:
            code = cart[c].decode("ascii")
            ast = parser.parse_string(code)
            ast = optimize.loads_to_funcs(ast)
            if not args.uncompressed:
                del cart[c]

            finalSize = 0

            def _best_func(root):
                nonlocal finalSize, cart
                bytes = printer.format(root).encode("ascii")
                if not args.uncompressed:
                    zlibcompressors = (zlib.compressobj(level, zlib.DEFLATED, 15, 9, strategy)
                                       for level in range(0, 10) for strategy in range(0, 5))
                    zopflicompressors = [zopfli.ZopfliCompressor(zopfli.ZOPFLI_FORMAT_ZLIB, block_splitting=False)]
                    data = (c.compress(bytes) + c.flush() for c in itertools.chain(zlibcompressors, zopflicompressors))
                    deflated = min(*data, key=len)[: -4]
                    cart[c[0], ticfile.ChunkID.CODE_ZIP] = deflated
                else:
                    cart[c] = bytes
                cart = dict(sorted(cart.items(), key=lambda x: args.chunks.index(ticfile.ChunkID.CODE)
                                   if x[0][1] == ticfile.ChunkID.CODE_ZIP else args.chunks.index(x[0][1])))
                _, filename = os.path.split(os.path.splitext(filepath)[0])
                ext = '.lua' if args.lua else '.tic'
                outfile = os.path.join(args.output, filename + '.packed' + ext) if os.path.isdir(args.output) else args.output
                finalSize = ticfile.write(cart, outfile)
                return finalSize <= args.target_size
            ast = optimize.anneal(ast, iterations=args.iterations, best_func=_best_func)
        filepbar.write(f"{filepathSliced:<30} Original: {originalSize} bytes. Packed: {finalSize} bytes.")
    sys.exit(1 if error else 0)


if __name__ == '__main__':
    main()
