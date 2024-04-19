from dataclasses import dataclass
import io
from lib2to3.pgen2.token import SLASH
import os
import struct
import zlib
import pyparsing as pp
from typing import ByteString, Callable
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
Chunk = tuple[int, ChunkID, ByteString]

# Writer is a function that takes the code (as encoded in latin-1 to bytes) and
# returns the "estimated" size of the cart with this code & a function that
# actually writes the cart to a file.
#
# All the cart saving functions take the data chunks and return a Writer, so
# that we can layout the data sections only once and regenerate only the code
# section when estimating the final size of the cart during optimization
Writer = Callable[[bytes], tuple[int, Callable[[typing.BinaryIO], int]]]


@dataclass
class Cart:
    # code, encoded in latin-1 (because latin-1 is guaranteed to have all byte values 0-255)
    code: bytes
    data: list[Chunk]


def write_tic(data: list[Chunk], pedantic: bool, compress: Callable[[bytes], bytes]) -> Writer:
    """
    Write a .tic cart to a file
        Parameters:
            cart (dict): A dictionary with (bank,chunkId) keys and ByteStrings values
            file (BinaryIO): File to which write the cart
            pedantic (bool): If True, will raise an exception if the cart is too large
            compress (Callable[[bytes],bytes]): Function to compress the code chunk
        Returns:
            filesize (int): Size of the just-written cart on disk
    """
    # Write the data chunks
    databytes = io.BytesIO()
    for i, (bank, chunk, bytes) in enumerate(data):
        # if this the last chunk and it's a DEFAULT chunk and we're not being pedantic
        if not pedantic and chunk == ChunkID.DEFAULT and i == len(data) - 1:
            databytes.write(struct.pack("<B", ChunkID.DEFAULT))
            break
        if chunk not in (ChunkID.CODE_ZIP, ChunkID.CODE, ChunkID.BINARY):
            # it's safe to strip trailing null bytes from the chunks as the TIC-80 loader initializes carts to 0s
            bytes = bytes.rstrip(b'\0')
        if chunk != ChunkID.DEFAULT and len(bytes) == 0:
            continue
        _write_tic_chunk(databytes, chunk, bank, bytes)
    return _TicWriter(compress, databytes.getvalue())


# These used to be lambdas with closures BUT lambdas could not be pickled for
# multiprocessing so had to do like this. The multiprocess library uses dill
# instead of pickle, which can serialize lambdas, but it's not a standard
# library and dill was slower than pickle

@dataclass
class _TicWriter:
    compress: Callable[[bytes], bytes]
    data: bytes

    def __call__(self, code: bytes):
        if self.compress is not None:
            compressed = self.compress(code)[0:-4]
            return len(compressed)+4+len(self.data), _TicCompressedOutput(compressed, self.data)
        return _codelen(code) + len(self.data), _TicUncompressedOutput(code, self.data)


@dataclass
class _TicCompressedOutput:
    compressed: bytes
    data: bytes

    def __call__(self, file: typing.BinaryIO) -> int:
        return _write_tic_chunk(file, ChunkID.CODE_ZIP, 0, self.compressed) + file.write(self.data)


@dataclass
class _TicUncompressedOutput:
    code: bytes
    data: bytes

    def __call__(self, file: typing.BinaryIO) -> int:
        return _write_tic_code(file, self.code) + file.write(self.data)


def _codelen(code: bytes) -> int:
    """Estimates the size of code after it is splitted into chunks"""
    return len(code)+(len(code)+65535)//65536*4


def _write_tic_code(file: typing.BinaryIO, code: bytes) -> int:
    """Write the code section to a .tic file, splitting it into chunks as needed"""
    total_len = len(code)
    if total_len > 524288:
        raise Exception(
            f"CODE chunk is {total_len} bytes, maximum size 524288 bytes (8 banks of 65536 bytes)")
    total_size = 0
    for i in range((total_len - 1) // 65536, -1, -1):
        if len(code) <= 65536:  # all the remaining code fits in a single chunk
            total_size += _write_tic_chunk(file, ChunkID.CODE, i, code)
            break
        else:  # write a chunk and remove it from the code
            total_size += _write_tic_chunk(file, ChunkID.CODE, i, code[:65536])
            code = code[65536:]
    return total_size


def _write_tic_chunk(file: typing.BinaryIO, chunk_id: ChunkID, bank: int, data: ByteString) -> int:
    """
    Write a chunk to a file
        Parameters:
            file (BinaryIO): File to which write the chunk
            chunk_id (ChunkID): Chunk type
            bank (int): Bank number
            data (ByteString): Chunk data
        Returns:
            filesize (int): Size of the just-written chunk on disk
    """
    size = len(data)
    if chunk_id in (ChunkID.CODE, ChunkID.BINARY):
        if size > 65536:
            raise Exception(
                f"{chunk_id.name} chunk is {size} bytes, maximum size 65536 bytes")
        if size == 65536:
            size = 0
    else:
        if size > 65535:
            raise Exception(
                f"{chunk_id.name} chunk is {size} bytes, maximum size 65535 bytes")
    packed_bank_chunk = (bank << 5) + (chunk_id & 31)
    header = struct.pack("<BHB", packed_bank_chunk, size,
                         0)  # the last byte is reserved
    return file.write(header) + file.write(data)


def read_tic(file: typing.BinaryIO) -> Cart:
    """
    Read a .tic cart from a file
        Parameters:
            file (typing.BinaryIO): File from which to load the cart
        Returns:
            cart (dict): A dictionary with (bank,chunkId) keys and ByteStrings values
    """
    code = ""
    code_chunks = {}
    data = []
    while True:
        # byte, with 3 highest bits bank and 5 lowest bits chunk type
        bank_and_chunk_bytes = file.read(1)
        if len(bank_and_chunk_bytes) == 0:
            break
        bank = bank_and_chunk_bytes[0] >> 5
        chunk_id = ChunkID(bank_and_chunk_bytes[0] & 31)
        # sizecoding hackers usually end CHUNK_DEFAULT abruptly without header
        header = file.read(3)
        size = struct.unpack("<H", header[:2])[0] if len(header) > 2 else 0
        if (chunk_id == ChunkID.CODE or chunk_id == ChunkID.BINARY) and size == 0:
            size = 65536
        chunk = file.read(size)
        if chunk_id == ChunkID.CODE_ZIP:
            code = zlib.decompress(chunk[2:], -15)
        elif chunk_id == ChunkID.CODE:
            code_chunks[bank] = chunk
        else:
            data.append((bank, chunk_id, chunk))
        if len(chunk) < size:
            break
    # join the code chunks into a single string if CODE_ZIP is not present
    if code == "":
        code = b''.join(code_chunks[i]
                        for i in range(7, -1, -1) if i in code_chunks)
    return Cart(code, data)


def write_png(data: list[Chunk], pedantic: bool, compress: Callable[[bytes], bytes]) -> Writer:
    """
    Writes a minimal file that passes the TIC-80 PNG cart check
    """
    # we don't want compress the code chunk when writing the inner cart because the whole cart will be compressed
    inner_writer = write_tic(data, pedantic, compress=None)
    return _PngWriter(inner_writer, compress)


@dataclass
class _PngWriter:
    inner_writer: Callable[[typing.BinaryIO], int]
    compress: Callable[[bytes], bytes]

    def __call__(self, code: bytes):
        bio = io.BytesIO()
        size, finish = self.inner_writer(code)
        assert finish(bio) == size
        compressed = self.compress(bio.getvalue())
        return len(compressed)+16, _PngOutput(compressed)


@dataclass
class _PngOutput:
    compressed: bytes

    def __call__(self, file: typing.BinaryIO) -> int:
        return file.write(b'\x89PNG\x0D\x0A\x1A\x0A') + \
            file.write(len(self.compressed).to_bytes(4, byteorder='big')) + \
            file.write(b'caRt') + \
            file.write(self.compressed)


def read_png(file: typing.BinaryIO) -> Cart:
    """
    Read a .png cart from a file
        Parameters:
            file (BinaryIO): File from which to load the cart
        Returns:
            cart (dict): A dictionary with (bank,chunkId) keys and ByteStrings values
    """
    if file.read(4) != b'\x89PNG':  # TIC-80 only checks first four bytes, so we do the same
        raise Exception("Not a PNG file")
    file.seek(4, os.SEEK_CUR)  # skip rest of header
    while True:
        sizeBytes = file.read(4)
        if len(sizeBytes) == 0:
            raise Exception("No caRt chunk found")
        size = int.from_bytes(sizeBytes, byteorder='big')
        chunkType = file.read(4)
        if len(chunkType) == 0:
            raise Exception("No caRt chunk found")
        if chunkType != b'caRt':
            file.seek(size + 4, os.SEEK_CUR)
            continue
        compressed = file.read(size)
        decompressed = zlib.decompress(compressed[2:], -15)
        return read_tic(io.BytesIO(decompressed))


def write_lua(data: list[Chunk]) -> Writer:
    """
    Write a .lua cart to a file
        Parameters:
            cart (dict): A dictionary with (bank,chunkId) keys and ByteStrings values
            file (TextIO): File to which write the cart
        Returns:
            filesize (int): Size of the just-written cart on disk
    """
    datafile = io.BytesIO()
    for bank, id, bytes in data:
        if id not in _IDCHUNKS:
            continue
        num, size, flip, tag = _IDCHUNKS[id]
        if bank > 0:
            tag += str(bank)
        datafile.write(f'\n-- <{tag}>'.encode('latin-1'))
        for i in range(num):
            part = bytes[i * size:(i + 1) * size]
            if all(x == 0 for x in part):
                continue
            hex = part.hex()
            if flip:
                hex = ''.join([c[1] + c[0] for c in zip(hex[::2], hex[1::2])])
            datafile.write(f'\n-- {i:03d}:{hex}'.encode('latin-1'))
        datafile.write(f'\n-- </{tag}>\n'.encode('latin-1'))
    return _LuaWriter(datafile.getvalue())


@dataclass
class _LuaWriter:
    data: bytes

    def __call__(self, code: bytes):
        return len(code) + len(self.data), _LuaOutput(code, self.data)


@dataclass
class _LuaOutput:
    code: bytes
    data: bytes

    def __call__(self, file: typing.BinaryIO) -> int:
        return file.write(self.code) + file.write(self.data)


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
    data = []
    for t, s, e in reversed(list(_tag.scanString(code))):
        # check if last character is a number, indicating bank
        # if there's no number, bank is 0
        bank = 0
        if t[0][-1] in '0123456789':
            bank = int(t[0][-1])
            t[0] = t[0][:-1]
        num, size, flip, chunk_id = _TEXTCHUNKS[t[0]]
        defined = {int(x[0]): ''.join(
            [c[1] + c[0] for c in zip(x[1][::2], x[1][1::2])]) if flip else x[1] for x in t[1]}
        chunk = b''.join((bytes.fromhex(defined[i]).ljust(size, b'\0')
                          if i in defined else bytes(size) for i in range(num)))
        data.append((bank, chunk_id, chunk))
        ret_code = ret_code[:s] + ret_code[e:]
    ret_code = ret_code.rstrip()
    data.reverse()
    return Cart(ret_code.encode('latin-1'), data)


def read(filepath: str) -> Cart:
    """
    Read a tic cart from the disk, detecting the file type based on magic bytes or extension
        Parameters:
            filepath (str): Path of the cart on disk
        Returns:
            cart (Cart): The code and data for the cart
    """
    _, ext = os.path.splitext(filepath)
    if ext == '.lua':
        with io.open(filepath, "r", encoding="latin-1") as file:
            return read_lua(file)
    else:
        with io.open(filepath, "rb") as file:
            if file.peek(4) == b'\x89PNG' or ext == '.png':
                return read_png(file)
            return read_tic(file)


def data_to_code(cart: Cart) -> Cart:
    """
    Converts the data in bank 0 by prepending code that initializes the data using pokes. Breaks using sync from bank 0.
    """
    # TODO: add support for multibank carts, by replacing the built-in sync function
    # with a custom one that loads/saves the data chunks
    loader = ""
    data = []
    for bank, id, bytes in cart.data:
        if bank == 0 and id in DATACHUNK_ADDRESSES:
            addr = DATACHUNK_ADDRESSES[id]
            datastr = bytes.hex()
            loader += "i=" + str(addr) + "\nfor m in ('" + datastr + \
                "'):gmatch('%x%x') do\n  poke(i,tonumber(m,16))\n  i=i+1\nend\n"
        else:
            data.append((bank, id, bytes))
    return Cart(loader.encode('latin-1') + cart.code, data)


_LANGLE, _RANGLE, _SLASH, _COLON = map(
    pp.Suppress, '<>/:'
)
_COMMENT = pp.Literal('--').suppress()

_tag_first = pp.Combine(pp.Word(pp.alphas) + pp.Optional(pp.Char(pp.nums)))
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

_IDCHUNKS = {
    id: (maxnum, size_per_row, flip, name) for name, (maxnum, size_per_row, flip, id) in _TEXTCHUNKS.items()
}
