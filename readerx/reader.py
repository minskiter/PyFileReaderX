from hashlib import md5
import os
import math
from itertools import takewhile, repeat
from functools import lru_cache
from tqdm import tqdm
import json


class FileReader():
    def __init__(self, file_name, encoding="utf-8", line_mapper=None):
        self.file_name = file_name
        self.encoding = encoding
        self._line_mapper = line_mapper
        self._size = None

    @lru_cache()
    def __repr__(self) -> str:
        attr = {
            "name": os.path.split(self.file_name)[-1],
            "encoding": self.encoding,
            "size": self.size(),
            "line_size": self.line_size(),
            "etag": self.etag()
        }
        return json.dumps(attr, indent=4, ensure_ascii=False)

    @lru_cache()
    def etag(self, buffer_size=5*1024*1024):
        size = self.size()
        md5sum = b""
        parts = math.ceil(size/buffer_size)
        with tqdm(total=size, desc=f"calculate {self.file_name} etag", unit="B", unit_scale=True, unit_divisor=1024) as bar:
            it = self.iter(buffer_size=buffer_size)
            for block in it:
                md5sum += md5(block).digest()
                bar.update(len(block))
        if parts <= 1:
            return md5(md5sum).hexdigest()
        return f"{md5(md5sum).hexdigest()}-{parts}"

    @lru_cache()
    def line_size(self):
        if hasattr(self, "_line_size"):
            return self._line_size
        buffer_size = 1024*1024
        with open(self.file_name, "rb") as file:
            it = takewhile(lambda x: x, (file.read(buffer_size)
                           for _ in repeat(None)))
            with tqdm(desc=f"count line size {self.file_name}",
                      unit="L") as bar:
                for block in it:
                    bar.update(block.count(b'\n'))
                if block[-1] != b'\n':
                    bar.update(1)
                return bar.n

    def line_iter(self):
        with open(self.file_name, "r", encoding=self.encoding) as f:
            for l in f:
                yield l

    def iter(self, buffer_size=5*1024*1024):
        with open(self.file_name, "rb") as file:
            for block in takewhile(lambda x: x, (file.read(buffer_size)
                                                 for _ in repeat(None))):
                yield block

    def __len__(self):
        return self.size()

    def size(self):
        if self._size is not None:
            self._size = os.path.getsize(self.file_name)
        return self._size

    @lru_cache(maxsize=100000)
    def line(self, index: int = 0) -> str:
        lines = self.get_line_mapper()
        if index >= len(lines):
            raise ValueError(f"index out of range")
        length = self.size() - \
            lines[index] if index == len(
                lines)-1 else lines[index+1]-lines[index]
        f = os.open(self.file_name, os.O_RDONLY)
        binary = os.pread(f, length, lines[index])
        os.close(f)
        return str(binary, encoding=self.encoding)

    def get_line_mapper(self):
        if self._line_mapper is not None:
            return self._line_mapper
        lines = []
        buffer_size = 1024*1024
        offset = 0
        with open(self.file_name, "rb") as file:
            it = takewhile(lambda x: x, (file.read(buffer_size)
                           for _ in repeat(None)))
            with tqdm(desc="build line mapper", unit="L") as bar:
                for block in it:
                    bar.update(block.count(b'\n'))
                    b = block.split(b'\n')
                    for i in b[:-1]:
                        if offset == 0:
                            lines.append(offset)
                        offset += len(i)+1
                        lines.append(offset)
                    offset += len(b[-1])
                if block[-1] != b'\n':
                    bar.update(1)
                self._line_size = bar.n
        self._line_mapper = lines
        return lines
