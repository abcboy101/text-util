import argparse
import struct
from typing import BinaryIO, TextIO, Self


class MSG:
    HEADER_FORMAT = '<3sc4sI4s'
    HEADER_00 = b'MSG'
    HEADER_04 = b'\xFE\xFF\x00\x01'
    HEADER_0C = b'\x10\x00\x02\x00'
    BLOCK_HEADER = '<4sI'
    BLOCK_MAGIC_TBL = b'MTBL'
    BLOCK_MAGIC_DAT = b'MDAT'

    def __init__(self, tbl: bytes, dat: bytes, *, language: bytes = b'U', length: int = 0):
        self.tbl = tbl
        self.dat = dat
        self.language = language
        self.length = length
    
    @classmethod
    def read(cls, f: BinaryIO) -> Self:
        h_00, language, h_04, length, h_0c = struct.unpack(cls.HEADER_FORMAT, f.read(struct.calcsize(cls.HEADER_FORMAT)))
        if h_00 != cls.HEADER_00 or h_04 != cls.HEADER_04 or h_0c != cls.HEADER_0C:
            if h_00[0] == 0x10:
                raise ValueError('Expected a MSG file, not an LZ-compressed file. Decompress and extract the archive first.')
            if h_00 + language == b'NARC':
                raise ValueError('Expected a MSG file, not a NARC file. Extract the archive first.')
            raise ValueError('invalid header')

        tbl_magic, tbl_size = struct.unpack(cls.BLOCK_HEADER, f.read(struct.calcsize(cls.BLOCK_HEADER)))
        if tbl_magic != cls.BLOCK_MAGIC_TBL:
            raise ValueError('unrecognized block (expected MTBL)')
        tbl = f.read(tbl_size)

        dat_magic, dat_size = struct.unpack(cls.BLOCK_HEADER, f.read(struct.calcsize(cls.BLOCK_HEADER)))
        if dat_magic != cls.BLOCK_MAGIC_DAT:
            raise ValueError('unrecognized chunk (expected MDAT)')
        dat = f.read(dat_size)

        return cls(tbl, dat, language=language, length=length)

    def write(self, f: BinaryIO):
        length = self.length if self.length > 0 else sum([struct.calcsize(self.HEADER_FORMAT),
                                                          struct.calcsize(self.BLOCK_HEADER) * 2,
                                                          len(self.tbl), len(self.dat)])
        f.write(struct.pack(self.HEADER_FORMAT, self.HEADER_00, self.language, self.HEADER_04, length, self.HEADER_0C))
        f.write(struct.pack(self.BLOCK_HEADER, self.BLOCK_MAGIC_TBL, len(self.tbl)))
        f.write(self.tbl)
        f.write(struct.pack(self.BLOCK_HEADER, self.BLOCK_MAGIC_DAT, len(self.dat)))
        f.write(self.dat)

    def get(self, index: int, table: dict[int, str]):
        offset: int = struct.unpack_from(f'<I', self.tbl, 4 * index)[0] * 4
        if offset >= len(self.dat):
            return None
        length = self.read_u16(offset)
        return ''.join(self.read_char(i, table) for i in range(offset + 2, offset + 2 + length * 2, 2))

    def read_u16(self, offset: int):
        return self.dat[offset] + (self.dat[offset + 1] << 8)

    def read_char(self, offset: int, table: dict[int, str]):
        value = self.read_u16(offset)
        return table.get(value, f'\\x{value:04X}')

    def dump(self, f: TextIO, table: dict[int, str]):
        for index in range(len(self.tbl) // 4):
            s = self.get(index, table)
            if s is not None:
                f.write(s)
                f.write('\n')


def load_table(region: str):
    table: dict[int, str] = {}
    with open(f'table_{region}.tbl', 'r', encoding='utf-8') as tbl_file:
        for line in tbl_file.read().splitlines(keepends=False):
            code, char = line.split('=', 1)
            table[int(code, 16)] = char
    return table


def dump_msg(src: str, dst: str, region: str = 'us'):
    table = load_table(region)
    with open(src, 'rb') as f:
        msg = MSG.read(f)
    with open(dst, 'w', encoding='utf-8') as out:
        msg.dump(out, table)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='trozei.py', description='Dumps text from Pokémon Trozei')
    parser.add_argument('src', help='source path')
    parser.add_argument('dst', help='destination path')
    parser.add_argument('-r', '--region', help='which region table to use',choices=['jp', 'us', 'eu', 'kr'], default='us')
    args = parser.parse_args()
    dump_msg(args.src, args.dst, args.region)
