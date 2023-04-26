from __future__ import annotations

from math import ceil


class FastSeek():
    _instances = {}
    
    def __new__(cls, fs, *args, **kwargs):
        try:
            self = FastSeek._instances[(fs, args, tuple(kwargs.items()))]
            if self.fopen.closed:
                raise IOError
        except (KeyError, IOError):
            self = FastSeek._instances[(fs, args, tuple(kwargs.items()))] = super(FastSeek, cls).__new__(cls)
            cls.cursor = 0
            cls.fopen = fs.open(*args, **kwargs)
            cls.fopen._seek = cls.fopen.seek
            cls.fopen.seek = cls.seek
            cls.fopen._read = cls.fopen.read
            cls.fopen.read = cls.read
        return self
    
    @staticmethod
    def close_all():
        for buffer in FastSeek._instances.values():
            buffer.close()

    
    def seek(self, cursor, *args, **kwargs):
        change = cursor - self.cursor
        self.cursor = cursor
        self.fopen._seek(change, 1, *args, **kwargs)
    
    def read(self, read_length, *args, **kwargs):
        self.cursor += read_length
        return self.fopen._read(read_length, *args, **kwargs)


def uncompressed_tarfile_size(tree_metadata: dict, blocksize: int = 512):
    size = blocksize  # header block for root of archive
    for item in tree_metadata.values():
        size += blocksize  # header block for entry
        if not item["is_dir"]:
            size += entry_size(item["size"], blocksize)  # entry data
    size += 2 * blocksize  # tarfile ends with 2 blocks of zeroes
    return size


def parse_header(header):
    return {
        "name"     : header[:100].decode("utf-8").rstrip("\0"),
        "mode"     : header[100:108].decode("utf-8").rstrip("\0"),
        "uid"      : header[108:116].decode("utf-8").rstrip("\0"),
        "gid"      : header[116:124].decode("utf-8").rstrip("\0"),
        "size"     : int(header[124:136].decode("utf-8").rstrip("\0")),
        "mtime"    : header[136:148].decode("utf-8").rstrip("\0"),
        "chksum"   : header[148:156].decode("utf-8").rstrip("\0"),
        "typeflag" : header[156],
        "linkname" : header[157:257].decode("utf-8").rstrip("\0"),
        "magic"    : header[257:263].decode("utf-8").rstrip("\0"),
        "version"  : header[263:265].decode("utf-8").rstrip("\0"),
        "uname"    : header[265:297].decode("utf-8").rstrip("\0"),
        "gname"    : header[297:329].decode("utf-8").rstrip("\0"),
        "devmajor" : header[329:337].decode("utf-8").rstrip("\0"),
        "devminor" : header[337:345].decode("utf-8").rstrip("\0"),
        "prefix"   : header[345:500].decode("utf-8").rstrip("\0"),
    }



def open_as_fast_seekable(fs, *args, **kwargs):
    fopen = FastSeek(fs, *args, **kwargs)
    return fopen


def unpack_file(tarball_fs, tarball, unpack_fs, filename, start, size):
    t = open_as_fast_seekable(tarball_fs, tarball, mode="rb", compression="gzip")
    t.seek(start)
    with unpack_fs.open(filename, mode="wb") as f:
        f.write(t.read(size))
    return size
            

def entry_size(filesize, blocksize):
    return blocksize * ceil(filesize / blocksize)