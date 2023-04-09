import io
from lib2to3.pgen2.token import SLASH
import os
import struct
import pyparsing as pp
from typing import ByteString
from enum import IntEnum
import typing


class ChunkID(IntEnum):
    """
    Enumerates different chunk types in a TIC-80 Cart
    See: https://github.com/nesbox/TIC-80/wiki/.tic-File-Format
    """
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


DATACHUNK_ADDRESSES = {
    ChunkID.TILES: 0x4000,
    ChunkID.SPRITES: 0x6000,
    ChunkID.MAP: 0x8000,
    ChunkID.FLAGS: 0x14404,
    ChunkID.SAMPLES: 0x100E4,
    ChunkID.WAVEFORM: 0x0FFE4,
    ChunkID.PALETTE: 0x3FC0,
    ChunkID.MUSIC: 0x13E64,
    ChunkID.PATTERNS: 0x11164
}

# Each cart may have 1-8 banks, which may or may not be present
Cart = dict[tuple[int, ChunkID], ByteString]


def write_tic(cart: Cart, file: typing.BinaryIO, pedantic=False) -> int:
    """
    Write a .tic cart to a file
        Parameters:
            cart (dict): A dictionary with (bank,chunkId) keys and ByteStrings values
            file (BinaryIO): File to which write the cart
        Returns:
            filesize (int): Size of the just-written cart on disk
    """
    total_size = 0
    for i, bank_chunk in enumerate(cart):
        # if this the last chunk and it's a DEFAULT chunk
        bank, chunk = bank_chunk
        if not pedantic and chunk == ChunkID.DEFAULT and i == len(cart) - 1:
            total_size += file.write(struct.pack("<B", ChunkID.DEFAULT))
            break
        packed_bank_chunk = (bank << 5) + (chunk & 31)
        data = cart[bank_chunk].rstrip(b'\0') if chunk != ChunkID.CODE_ZIP and chunk != ChunkID.CODE else cart[bank_chunk]
        if chunk != ChunkID.DEFAULT and len(data) == 0:
            continue
        header = struct.pack("<BHB", packed_bank_chunk, len(data), 0)  # the last byte is reserved
        total_size += file.write(header)
        total_size += file.write(data)
    return total_size


def read_tic(file: typing.BinaryIO) -> Cart:
    """
    Read a .tic cart from a file
        Parameters:
            file (typing.BinaryIO): File from which to load the cart
        Returns:
            cart (dict): A dictionary with (bank,chunkId) keys and ByteStrings values
    """
    cart = {}
    while True:
        bank_and_chunk_bytes = file.read(1)  # byte, with 3 highest bits bank and 5 lowest bits chunk type
        if len(bank_and_chunk_bytes) == 0:
            return cart
        bank = bank_and_chunk_bytes[0] >> 5
        chunk_id = ChunkID(bank_and_chunk_bytes[0] & 31)
        header = file.read(3)  # sizecoding hackers usually end CHUNK_DEFAULT abruptly without header
        size = struct.unpack("<H", header[:2])[0] if len(header) > 2 else 0
        chunk = file.read(size)
        cart[bank, chunk_id] = chunk
        if len(chunk) < size:
            return cart


def write_lua(cart: Cart, file: typing.TextIO) -> int:
    """
    Write a .lua cart to a file
        Parameters:
            cart (dict): A dictionary with (bank,chunkId) keys and ByteStrings values
            file (TextIO): File to which write the cart
        Returns:
            filesize (int): Size of the just-written cart on disk
    """
    total_size = 0
    total_size += file.write(cart[0, ChunkID.CODE].decode("ascii"))
    for k, v in _TEXTCHUNKS.items():
        num, size, flip, chunk_id = v
        if (0, chunk_id) in cart:
            total_size += file.write(f'\n-- <{k}>')
            for i in range(num):
                part = cart[0, chunk_id][i * size:(i + 1) * size]
                if all(x == 0 for x in part):
                    continue
                hex = part.hex()
                if flip:
                    hex = ''.join([c[1] + c[0] for c in zip(hex[::2], hex[1::2])])
                total_size += file.write(f'\n-- {i:03d}:{hex}')
            total_size += file.write(f'\n-- </{k}>\n')
    return total_size


def read_lua(file: typing.TextIO) -> Cart:
    """
    Read a .lua cart from a file
        Parameters:
            file (TextIO): File from which to load the cart
        Returns:
            cart (dict): A dictionary with (bank,chunkId) keys and ByteStrings values
    """
    code = file.read()
    ret_code = code
    ret = Cart()
    for t, s, e in reversed(list(_tag.scanString(code))):
        num, size, flip, chunk_id = _TEXTCHUNKS[t[0]]
        defined = {int(x[0]): ''.join([c[1] + c[0] for c in zip(x[1][::2], x[1][1::2])]) if flip else x[1] for x in t[1]}
        chunk = b''.join((bytes.fromhex(defined[i]).ljust(size, b'\0')
                         if i in defined else bytes(size) for i in range(num)))
        ret[0, chunk_id] = chunk
        ret_code = ret_code[:s] + ret_code[e:]
    ret_code = ret_code.rstrip()
    ret[0, ChunkID.CODE] = ret_code.encode("ascii")
    return ret


def read(filepath: str) -> Cart:
    """
    Read a tic cart from the disk, detecting the file type based on extension
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


def write(cart: Cart, filepath: str, ext: str = None, pedantic=False) -> int:
    """
    Write a tic cart to the disk
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
            return write_tic(cart, file, pedantic=pedantic)


def data_to_code(cart: Cart):
    codechunks = [c for c in cart if c[1] == ChunkID.CODE]
    for c in codechunks:
        code = cart[c].decode("ascii")
        bank = c[0]
        noncodechunks = [c for c in cart if c[0] == bank and c[1] in DATACHUNK_ADDRESSES]
        for e in noncodechunks:
            addr = DATACHUNK_ADDRESSES[e[1]]
            datastr = cart[e].hex()
            loader = "i=0\nfor m in string.gmatch('" + datastr + "', '%x%x') do\n  poke("+str(addr)+"+i,tonumber('0x'..m))\n  i=i+1\nend\n"
            code = loader + code
            del cart[e]
        cart[c] = code.encode("ascii")


_LANGLE, _RANGLE, _SLASH, _COLON = map(
    pp.Suppress, '<>/:'
)
_COMMENT = pp.Literal('--').suppress()

_tag_first = pp.Word(pp.alphas)
_tag_second = pp.match_previous_literal(_tag_first).suppress()
_new_line = pp.rest_of_line().copy().suppress()
_tag_start = pp.LineStart() + _COMMENT + _LANGLE + _tag_first + _RANGLE
_tag_end = pp.LineStart() + _COMMENT + _LANGLE + _SLASH + _tag_second + _RANGLE
_tag_line = pp.Group(_COMMENT + pp.Word(pp.nums) + _COLON + pp.Word(pp.hexnums))
_tag = _tag_start + pp.Group(pp.ZeroOrMore(_tag_line)) + _tag_end

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
