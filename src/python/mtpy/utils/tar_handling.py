from __future__ import annotations

from math import ceil


class FastSeek:
    """A class for fast seeking in files."""

    _instances = {}

    def __new__(cls, fs, *args, **kwargs):
        """A function for creating a new instance of the FastSeek class.

        Args:
            fs (filesystem): an fsspec filesystem

        Raises:
            IOError: File was closed before seeking could be performed

        Returns:
            self: a FastSeek instance
        """
        try:
            self = FastSeek._instances[(fs, args, tuple(kwargs.items()))]
            if self.fopen.closed:
                raise IOError
        except (KeyError, IOError):
            self = FastSeek._instances[(fs, args, tuple(kwargs.items()))] = super(
                FastSeek, cls
            ).__new__(cls)
            cls.cursor = 0
            cls.fopen = fs.open(*args, **kwargs)
            cls.fopen._seek = cls.fopen.seek
            cls.fopen.seek = cls.seek
            cls.fopen._read = cls.fopen.read
            cls.fopen.read = cls.read
        return self

    @staticmethod
    def close_all():
        """A function for closing all open FastSeek instances."""
        for buffer in FastSeek._instances.values():
            buffer.close()

    def seek(self, cursor: int, *args, **kwargs):
        """A function for seeking to a position in a file.

        Args:
            cursor (int): the position to seek to
        """
        change = cursor - self.cursor
        self.cursor = cursor
        self.fopen._seek(change, 1, *args, **kwargs)

    def read(self, read_length: int, *args, **kwargs) -> any:
        """A function for reading a number of bytes from a file.

        Args:
            read_length (int): the number of bytes to read

        Returns:
            any: the bytes read from the file
        """
        self.cursor += read_length
        return self.fopen._read(read_length, *args, **kwargs)


def uncompressed_tarfile_size(tree_metadata: dict, blocksize: int = 512) -> int:
    """A function for calculating the size of the tarfile before compression.

    Args:
        tree_metadata (dict): the metadata of the tree to calculate the size of
        blocksize (int, optional): the blocksize to use for the tarfile. Defaults to 512.

    Returns:
        int: the size of the tarfile before compression
    """
    size = blocksize  # header block for root of archive
    for item in tree_metadata.values():
        size += blocksize  # header block for entry
        if not item["is_dir"]:
            size += entry_size(item["size"], blocksize)  # entry data
    size += 2 * blocksize  # tarfile ends with 2 blocks of zeroes
    return size


def parse_header(header) -> dict:
    """A function for parsing a tarfile header.

    Args:
        header: the header to parse

    Returns:
        dict: a dict containing header data
    """
    return {
        "name": header[:100].decode("utf-8").rstrip("\0"),
        "mode": header[100:108].decode("utf-8").rstrip("\0"),
        "uid": header[108:116].decode("utf-8").rstrip("\0"),
        "gid": header[116:124].decode("utf-8").rstrip("\0"),
        "size": int(header[124:136].decode("utf-8").rstrip("\0")),
        "mtime": header[136:148].decode("utf-8").rstrip("\0"),
        "chksum": header[148:156].decode("utf-8").rstrip("\0"),
        "typeflag": header[156],
        "linkname": header[157:257].decode("utf-8").rstrip("\0"),
        "magic": header[257:263].decode("utf-8").rstrip("\0"),
        "version": header[263:265].decode("utf-8").rstrip("\0"),
        "uname": header[265:297].decode("utf-8").rstrip("\0"),
        "gname": header[297:329].decode("utf-8").rstrip("\0"),
        "devmajor": header[329:337].decode("utf-8").rstrip("\0"),
        "devminor": header[337:345].decode("utf-8").rstrip("\0"),
        "prefix": header[345:500].decode("utf-8").rstrip("\0"),
    }


def open_as_fast_seekable(fs, *args, **kwargs):
    """opens a file as a fast seekable file

    Args:
        fs (filesystem): an fsspec filesystem

    Returns:
        file: a fast seekable file
    """
    fopen = FastSeek(fs, *args, **kwargs)
    return fopen


def unpack_file(tarball_fs, tarball, unpack_fs, filename, start, size):
    """A function for unpacking a file from a tarfile.

    Args:
        tarball_fs: the fsspec filesystem of the tarball
        tarball: the path to the tarball
        unpack_fs: the fsspec filesystem to unpack the file to
        filename: the name of the file to unpack to
        start: the start position of the file in the tarball
        size: the size of the file in the tarball

    Returns:
        int: the size of the file unpacked
    """
    t = open_as_fast_seekable(tarball_fs, tarball, mode="rb", compression="gzip")
    t.seek(start)
    with unpack_fs.open(filename, mode="wb") as f:
        f.write(t.read(size))
    return size


def entry_size(filesize, blocksize):
    """A function for calculating the size of a tarfile entry.

    Args:
        filesize: the size of the file
        blocksize: the blocksize of the tarfile

    Returns:
        int: the size of the entry
    """
    return blocksize * ceil(filesize / blocksize)
