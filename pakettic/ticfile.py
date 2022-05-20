import io
from lib2to3.pgen2.token import SLASH
import os
import struct
import pyparsing as pp
from typing import IO, ByteString
from enum import IntEnum
import typing

from pakettic.parser import COLON
# https://github.com/nesbox/TIC-80/wiki/.tic-File-Format
#
# Each bank has chunks, which may or may not be present


class ChunkID(IntEnum):
    TILES = 1          # 8 banks, copied to RAM at 0x4000...0x5FFF
    SPRITES = 2        # 8 banks, copied to RAM at 0x6000...0x7FFF
    MAP = 4            # 8 banks, copied to RAM at 0x8000...0xFF7F
    CODE = 5           # 8 banks (PRO only), in ASCII text format
    FLAGS = 6          # 8 banks, sprite flags. copied to RAM at 0x14404...0x14603
    SAMPLES = 9        # 8 banks, copied to RAM at 0x100E4...0x11163
    WAVEFORM = 10      # copied to RAM at 0x0FFE4...0x100E3
    PALETTE = 12       # copied to RAM at 0x3FC0...0x3FEF
    MUSIC = 14         # 8 banks, copied to RAM at 0x13E64...0x13FFB
    PATTERNS = 15      # 8 banks, copied to RAM at 0x11164...0x13E63
    DEFAULT = 17       # flag, no actual content. cart should load default chunk first.
    SCREEN = 18        # 8 banks, 240 x 136 x 4bpp raw buffer. Bank 0 is the cover image.
    BINARY = 19        # 4 banks (?), store binary WASM files.
    COVER_DEP = 3      # deprecated as of 0.90
    PATTERNS_DEP = 13  # 8 banks, deprecated as of 0.80 (copied to RAM at 0x11164...0x13E63)
    CODE_ZIP = 16      # compressed with ZLIB. deprecated as of 1.00, won't be removed.


# Each cart may have 1-8 banks, which may or may not be present
Cart = dict[tuple[int, ChunkID], ByteString]


def write_tic(cart: Cart, file: typing.BinaryIO, chopDefault=True) -> int:
    totalSize = 0
    for i, bankChunk in enumerate(cart):
        # if this the last chunk and it's a DEFAULT chunk
        bank, chunk = bankChunk
        if chopDefault and chunk == ChunkID.DEFAULT and i == len(cart) - 1:
            totalSize += file.write(struct.pack("<B", ChunkID.DEFAULT))
            break
        packedBankChunk = (bank << 5) + (chunk & 31)
        data = cart[bankChunk].rstrip(b'\0') if chunk != ChunkID.CODE_ZIP and chunk != ChunkID.CODE else cart[bankChunk]
        if chunk != ChunkID.DEFAULT and len(data) == 0:
            continue
        header = struct.pack("<BHB", packedBankChunk, len(data), 0)  # the last byte is reserved
        totalSize += file.write(header)
        totalSize += file.write(data)
    return totalSize


def read_tic(file: typing.BinaryIO) -> Cart:
    cart = {}
    while True:
        bankAndChunkBytes = file.read(1)  # byte, with 3 highest bits bank and 5 lowest bits chunk type
        if len(bankAndChunkBytes) == 0:
            return cart
        bank = bankAndChunkBytes[0] >> 5
        chunkID = ChunkID(bankAndChunkBytes[0] & 31)
        header = file.read(3)  # sizecoding hackers usually end CHUNK_DEFAULT abruptly without header
        size = struct.unpack("<H", header[:2])[0] if len(header) > 2 else 0
        chunk = file.read(size)
        cart[bank, chunkID] = chunk
        if len(chunk) < size:
            return cart


def write_lua(cart: Cart, file: typing.TextIO) -> int:
    totalSize = 0
    totalSize += file.write(cart[0, ChunkID.CODE].decode("ascii"))
    for k, v in _TEXTCHUNKS.items():
        num, size, flip, chunkId = v
        if (0, chunkId) in cart:
            totalSize += file.write(f'\n-- <{k}>')
            for i in range(num):
                part = cart[0, chunkId][i * size:(i + 1) * size]
                if all(x == 0 for x in part):
                    continue
                hex = part.hex()
                if flip:
                    hex = ''.join([c[1] + c[0] for c in zip(hex[::2], hex[1::2])])
                totalSize += file.write(f'\n-- {i:03d}:{hex}')
            totalSize += file.write(f'\n-- </{k}>\n')
    return totalSize


def read_lua(file: typing.TextIO) -> Cart:
    code = file.read()
    retCode = code
    ret = Cart()
    for t, s, e in reversed(list(_tag.scanString(code))):
        num, size, flip, chunkId = _TEXTCHUNKS[t[0]]
        defined = {int(x[0]): ''.join([c[1] + c[0] for c in zip(x[1][::2], x[1][1::2])]) if flip else x[1] for x in t[1]}
        chunk = b''.join((bytes.fromhex(defined[i]).ljust(size, b'\0')
                         if i in defined else bytes(size) for i in range(num)))
        ret[0, chunkId] = chunk
        retCode = retCode[:s] + retCode[e:]
    retCode = retCode.rstrip()
    ret[0, ChunkID.CODE] = retCode.encode("ascii")
    return ret


def read(filepath: str) -> Cart:
    """Read a tic cart from the disk, detecting the file type based on extension
            Parameters:
                filepath (str): Path of the cart on disk
            Returns:
                cart (dict): A dictionary with (bank,chunkId) keys and ByteStrings values
    """
    _, ext = os.path.splitext(filepath)
    if ext == '.lua':
        with io.open(filepath, "r") as file:
            return read_lua(file)
    else:
        with io.open(filepath, "rb") as file:
            return read_tic(file)


def write(cart: Cart, filepath: str, ext: str = None) -> int:
    """Write a tic cart to the disk
            Parameters:
                cart (dict): A dictionary with (bank,chunkId) keys and ByteStrings values
                filepath (str): Path of the cart on disk
                ext (str): Optional file format extension. If omitted, the format is auto-detected from the filepath.
            Returns:
                filesize (int): Size of the just-written cart on disk
    """
    if ext is None:
        _, ext = os.path.splitext(filepath)
    if ext == '.lua':
        with io.open(filepath, "w", newline='\n') as file:
            return write_lua(cart, file)
    else:
        with io.open(filepath, "wb") as file:
            return write_tic(cart, file)


_LANGLE, _RANGLE, _SLASH, _COLON = map(
    pp.Suppress, '<>/:'
)
_COMMENT = pp.Literal('--').suppress()

_tagFirst = pp.Word(pp.alphas)
_tagSecond = pp.match_previous_literal(_tagFirst).suppress()
_newLine = pp.rest_of_line().copy().suppress()
_tagStart = pp.LineStart() + _COMMENT + _LANGLE + _tagFirst + _RANGLE
_tagEnd = pp.LineStart() + _COMMENT + _LANGLE + _SLASH + _tagSecond + _RANGLE
_tagLine = pp.Group(_COMMENT + pp.Word(pp.nums) + _COLON + pp.Word(pp.hexnums))
_tag = _tagStart + pp.Group(pp.ZeroOrMore(_tagLine)) + _tagEnd

_TEXTCHUNKS = {  # maxnumber, size per row, flip nibbles
    "TILES": (256, 32, True, ChunkID.TILES),
    "SPRITES": (256, 32, True, ChunkID.SPRITES),
    "MAP": (136, 240, True, ChunkID.MAP),
    "WAVES": (16, 16, True, ChunkID.WAVEFORM),
    "SFX": (64, 66, True, ChunkID.SAMPLES),
    "PATTERNS": (60, 64 * 3, True, ChunkID.PATTERNS),
    "TRACKS": (8, 51, True, ChunkID.MUSIC),
    "FLAGS": (2, 256, True, ChunkID.FLAGS),
    "SCREEN": (136, 120, True, ChunkID.SCREEN),
    "PALETTE": (2, 48, False, ChunkID.PALETTE),
}
