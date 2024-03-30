import argparse
import glob
import io
import os
import re
import struct
import warnings
from typing import BinaryIO, TextIO, Self


class BTXT:
    HEADER_FORMAT = '<IIHH'
    METADATA_FORMAT = '<IBBBB'
    CONTROL = '\u1B01\u1B02\u1C01\u1C02\u1700\u1701\u1800\u1900'

    def __init__(self, magic: int, labels: list[str], text: list[str], *,
                 metadata: list[tuple] = None, label_offsets: list[int] = None, text_offsets: list[int] = None):
        self.magic: int = magic
        self.labels: list[str] = labels
        self.text: list[str] = text

        self.metadata: list[tuple[int, int, int]] = metadata
        self.label_offsets: list[int] = label_offsets
        self.text_offsets: list[int] = text_offsets

    def __eq__(self, other):
        return (
                self.magic == other.magic
                and self.labels == other.labels
                and self.text == other.text
        )

    @classmethod
    def read(cls, f: BinaryIO) -> Self:
        """Read and parse the data from a binary file."""
        h_00, magic, count, count2 = struct.unpack(cls.HEADER_FORMAT, f.read(struct.calcsize(cls.HEADER_FORMAT)))
        if h_00 != 0:
            raise ValueError('invalid header')
        if count != count2:
            raise ValueError('counts not equal')

        metadata = [struct.unpack(cls.METADATA_FORMAT, f.read(8)) for _ in range(count)]
        label_offsets: list[int] = list(struct.unpack(f'<{count}I', f.read(4 * count)))
        text_offsets: list[int] = list(struct.unpack(f'<{count}I', f.read(4 * count)))

        labels = []
        pos = f.tell()
        for offset in label_offsets:
            f.seek(pos + offset, os.SEEK_SET)
            buf = bytearray()
            while value := f.read(1):
                if value == b'\x00':
                    break
                buf += value
            s = buf.decode('ascii')
            labels.append(s)

        text = []
        for i, offset in enumerate(text_offsets):  # type: int, int
            f.seek(pos + offset, os.SEEK_SET)
            buf = bytearray()
            while value := f.read(2):
                if value == b'\x00\x00':
                    break
                buf += value
            s = buf.decode('utf-16-le')
            if metadata[i] != (calc := cls.calculate_metadata(s, i)):
                warnings.warn(f'Expected metadata of {calc!r} but found {metadata[i]!r} instead for string {s!r}', RuntimeWarning)
            text.append(s)

        padding = b'\x00\x00\x00\x00' if f.tell() % 4 == 0 else b'\x00\x00'
        if f.read() != padding:
            warnings.warn('Found unexpected padding at end of file', RuntimeWarning)

        return cls(magic, labels, text,
                   metadata=metadata, label_offsets=label_offsets, text_offsets=text_offsets)

    def write(self, f: BinaryIO):
        """Write the data to a binary file."""
        if self.metadata is None:
            metadata = [self.calculate_metadata(text, index) for index, text in enumerate(self.text)]
        else:
            metadata = self.metadata

        if self.label_offsets is None or self.text_offsets is None:
            label_offsets = []
            text_offsets = []
            offset = 0
            for s in self.labels:
                label_offsets.append(offset)
                offset += len(s) + 1
                if offset % 4 != 0:
                    offset += 4 - (offset % 4)
            for s in self.text:
                text_offsets.append(offset)
                offset += len(s) * 2 + 2
                offset += 4 if offset % 4 == 0 else 2
        else:
            label_offsets = self.label_offsets
            text_offsets = self.text_offsets

        f.write(struct.pack(self.HEADER_FORMAT, 0, self.magic, len(self.labels), len(self.text)))
        for v in metadata:
            f.write(struct.pack(self.METADATA_FORMAT, *v))
        f.write(struct.pack(f'<{len(label_offsets)}I', *label_offsets))
        f.write(struct.pack(f'<{len(text_offsets)}I', *text_offsets))

        pos = f.tell()
        for offset, label in zip(label_offsets, self.labels):  # type: int, str
            if (cur := f.tell() - pos) < offset:
                f.write(b'\x00' * (offset - cur))
            f.write(label.encode('ascii'))
            f.write(b'\x00')

        for offset, text in zip(text_offsets, self.text):  # type: int, str
            if (cur := f.tell() - pos) < offset:
                f.write(b'\x00' * (offset - cur))
            f.write(text.encode('utf-16le'))
            f.write(b'\x00\x00')

        padding = b'\x00\x00\x00\x00' if f.tell() % 4 == 0 else b'\x00\x00'
        f.write(padding)

    @classmethod
    def escape(cls, s: str):
        """Escape the string so that it can be dumped."""
        s = (s.replace('\\', '\\\\')
            .replace('\r', '\\r')
            .replace('\n', '\\n')
            .replace('\t', '\\t')
             )
        s = re.sub(f'[{cls.CONTROL}]', lambda match: f'\\x{ord(match.group(0)[0]):04X}', s)
        return s

    @classmethod
    def unescape(cls, s: str):
        """Unescape the string read from a dump."""
        out: list[str] = []
        i = 0
        while i < len(s):
            c = s[i]; i += 1
            if c != '\\':
                out.append(c)
            else:  # escape sequence
                c = s[i]; i += 1
                match c:
                    case 'r': out.append('\r')
                    case 'n': out.append('\n')
                    case 't': out.append('\t')
                    case 'x': out.append(chr(int(s[i:i+4], 16))); i += 4
                    case _: out.append(c)
        return ''.join(out)

    @classmethod
    def calculate_metadata(cls, s: str, index: int):
        """Calculates the stored metadata for the string."""
        lines = re.sub(f'[{cls.CONTROL}]', '', s).split('\n')  # \r is not counted as part of the line break
        width = max(len(line) for line in lines)
        height = len(lines)
        length = n if (n := len(s)) % 2 == 0 else (n + 1)  # this includes the control characters
        return 1, width, height, length, index % 256

    def dump(self, f: TextIO):
        """Dump to file as plain text."""
        f.write(f'{self.magic:08X}\n')
        for i, (label, text) in enumerate(zip(self.labels, self.text)):  # type: tuple, str, str
            f.write('\t'.join((label, self.escape(text))))
            f.write('\n')

    @classmethod
    def load(cls, f: TextIO):
        """Load from file as plain text."""
        first_line = re.match(r'([0-9A-F]+)\n', f.readline())
        magic = int(first_line.group(1), 16)
        labels: list[str] = []
        text: list[str] = []
        while line := f.readline():
            line_label, line_text = line.removesuffix('\n').split('\t', 1) # type: str, str
            labels.append(line_label)
            text.append(cls.unescape(line_text))
        return cls(magic, labels, text)


def unpack(src: str, dst: str, *, verify: bool = False):
    with open(src, 'rb') as f:
        msg = BTXT.read(f)
    with open(dst, 'w', encoding='utf-8') as out:
        msg.dump(out)

    if verify:
        # Verify loading the dumped text is equivalent to the file read
        with open(dst, 'r', encoding='utf-8') as out:
            dumped = BTXT.load(out)
        if msg != dumped:
            raise RuntimeError('dumped text does not match the file read')

        # Verify written file is equivalent to the file read
        with io.BytesIO() as edited:
            dumped.write(edited)
            out = edited.getvalue()
        with open(src, 'rb') as f:
            original = f.read()
        if original != out:
            raise RuntimeError('written file does not match the file read')


def pack(src: str, dst: str):
    with open(src, 'r', encoding='utf-8') as f:
        msg = BTXT.load(f)
    with open(dst, 'wb') as out:
        msg.write(out)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='btxt.py', description='Converts text from/to the BTXT format used in Touzoku to 1000-biki no Pokémon')
    parser.add_argument('action', choices=['p', 'pack', 'u', 'unpack'])
    parser.add_argument('src', help='source file or directory path')
    parser.add_argument('dst', help='destination file or directory path')
    parser.add_argument('-v', help='verify', default=False)
    args = parser.parse_args()

    if args.action in ['u', 'unpack']:
        if os.path.isdir(args.src):
            for src_fn in glob.glob(os.path.join(args.src, '*.btxt')):
                dst_fn = os.path.join(args.dst, os.path.basename(src_fn).removesuffix('.btxt') + '.txt')
                unpack(src_fn, dst_fn, verify=args.verify)
                print(dst_fn)
        else:
            unpack(args.src, args.dst, verify=args.verify)
    elif args.action in ['p', 'pack']:
        if os.path.isdir(args.src):
            for src_fn in glob.glob(os.path.join(args.src, '*.txt')):
                dst_fn = os.path.join(args.dst, os.path.basename(src_fn).removesuffix('.txt') + '.btxt')
                pack(src_fn, dst_fn)
                print(dst_fn)
        else:
            pack(args.src, args.dst)
