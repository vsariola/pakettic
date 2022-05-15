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

from pakettic import fileformats, parser, printer, optimize
import tqdm


def main():
    sys.setrecursionlimit(100000)  # TODO: find out why the parser recurses so heavily and reduce that

    version = pkg_resources.get_distribution('crushtic').version
    argparser = argparse.ArgumentParser(
        prog='pakettic', description=f'Minify and compress TIC-80 fantasy console carts. v{version}')
    argparser.add_argument('input', nargs='+', help='Input file(s). * and ** work for wildcards and recursion.')
    argparser.add_argument('-o', '--output', default=os.getcwd(), metavar='output', help='Output file or directory.')
    argparser.add_argument('-u', '--uncompressed', action='store_const', const=True,
                           help='Leave code chunks uncompressed, even when outputting a .tic file.')
    argparser.add_argument('-l', '--lua', action='store_const', const=True,
                           help='Output .lua carts instead of .tic carts.')
    argparser.add_argument('-c', '--chunks',
                           default='code,default', metavar='chunk', help='Chunks to include and their order. Valid values: ALL, ALL_EXCEPT_DEFAULT, or a comma separated list of chunk types without spaces (BINARY,CODE,COVER_DEP,DEFAULT,FLAGS,MAP,MUSIC,PALETTE,PATTERNS_DEP,PATTERNS,SAMPLES,SCREEN,SPRITES,TILES,WAVEFORM). Default value: CODE,DEFAULT.',
                           type=str.upper)
    args = argparser.parse_args()
    input = []
    # use glob to find files matching wildcards
    # if a string does not contain a wildcard, glob will return it as is.
    for arg in args.input:
        input += glob(arg, recursive=True)
    if len(input) > 1 and not os.path.isdir(args.output):
        sys.exit('When multiple input files are defined, the output must be a directory.')
    if args.chunks == 'ALL' or args.chunks == 'ALL_EXCEPT_DEFAULT':
        chunkTypes = [e for e in fileformats.ChunkID if e !=
                      fileformats.ChunkID.CODE_ZIP and e != fileformats.ChunkID.DEFAULT]
        if args.chunks == 'ALL':
            chunkTypes = [fileformats.ChunkID.DEFAULT] + chunkTypes
    else:
        chunkTypes = []
        for chunkIdName in args.chunks.split(','):
            x = getattr(fileformats.ChunkID, chunkIdName.upper())
            if x is None:
                sys.exit(f"Unknown chunk type entered on command line: {chunkIdName}")
            chunkTypes.append(x)
        chunkTypes = list(dict.fromkeys(chunkTypes))  # remove duplicates
    filepbar = tqdm.tqdm(input, leave=False)
    error = False
    for fileName in filepbar:
        path, ext = os.path.splitext(fileName)
        originalSize = os.path.getsize(fileName)
        if ext == '.tic':
            with io.open(fileName, "rb") as file:
                cart = fileformats.read_tic(file)
        elif ext == '.lua':
            with io.open(fileName, "r") as file:
                cart = fileformats.read_lua(file)
        else:
            filepbar.write(f"Unknown file format extension {ext}, skipping {fileName}")
            error = True
            continue
        codeZipChunks = [c for c in cart if c[1] == fileformats.ChunkID.CODE_ZIP]
        for c in codeZipChunks:
            if (c[0], fileformats.ChunkID.CODE) not in cart:
                cart[c[0], fileformats.ChunkID.CODE] = zlib.decompress(cart[c][2:], -15)
                del cart[c]
        cart[(0, fileformats.ChunkID.DEFAULT)] = b''
        cart = dict((c for c in cart.items() if c[0][1] in chunkTypes))
        codeChunks = [c for c in cart if c[1] == fileformats.ChunkID.CODE]
        for c in codeChunks:
            code = cart[c].decode("ascii")
            ast = parser.parse_string(code)
            ast = optimize.loads_to_funcs(ast)
            ast = optimize.funcs_to_loads(ast)
            text = printer.format(ast)
            bytes = text.encode("ascii")
            if not args.uncompressed and not args.lua:
                zlibcompressors = (zlib.compressobj(level, zlib.DEFLATED, 15, 9, strategy)
                                   for level in range(0, 10) for strategy in range(0, 5))
                zopflicompressors = [zopfli.ZopfliCompressor(zopfli.ZOPFLI_FORMAT_ZLIB)]
                data = (c.compress(bytes) + c.flush() for c in itertools.chain(zlibcompressors, zopflicompressors))
                deflated = min(*data, key=len)[: -4]
                cart[c[0], fileformats.ChunkID.CODE_ZIP] = deflated
                del cart[c]
            else:
                cart[c] = bytes
        cart = dict(sorted(cart.items(), key=lambda x: chunkTypes.index(fileformats.ChunkID.CODE)
                    if x[0][1] == fileformats.ChunkID.CODE_ZIP else chunkTypes.index(x[0][1])))
        _, filename = os.path.split(path)
        ext = '.lua' if args.lua else '.tic'
        outfile = os.path.join(args.output, filename + '.packed' + ext) if os.path.isdir(args.output) else args.output
        if args.lua:
            with io.open(outfile, "w", newline='\n') as file:
                finalSize = fileformats.write_lua(cart, file)
        else:
            with io.open(outfile, "wb") as file:
                finalSize = fileformats.write_tic(cart, file)
        fileNameSliced = fileName[-30:] if len(fileName) > 30 else fileName
        filepbar.write(f"{fileNameSliced:<30} Original: {originalSize} bytes. Packed: {finalSize} bytes.")
    sys.exit(1 if error else 0)


if __name__ == '__main__':
    main()
