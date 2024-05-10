"""A module for handling tarfiles and their contents."""

from __future__ import annotations

from math import ceil
from typing import ClassVar, Dict, Tuple

from fsspec.spec import AbstractFileSystem

from .types import FileLike, JSONDict


class FastSeek:
    """A class for fast seeking in files."""

    _instances: ClassVar[Dict[Tuple, FastSeek]] = {}
    __key__ = None

    def __new__(cls: "type[FastSeek]", fs: AbstractFileSystem, *args, **kwargs) -> FastSeek:
        """A function for creating a new instance of the FastSeek class.

        Args:
            fs (AbstractFileSystem): an fsspec filesystem
            *args: positional arguments to pass to the filesystem open method
            **kwargs: keyword arguments to pass to the filesystem open method

        Raises:
            IOError: File was closed before seeking could be performed

        Returns:
            FastSeek: a FastSeek instance
        """
        try:
            self = FastSeek._instances[(fs, args, tuple(kwargs.items()))]
            if self.fopen.closed:
                raise IOError
        except (KeyError, IOError):
            self = FastSeek._instances[(fs, args, tuple(kwargs.items()))] = super(
                FastSeek, cls
            ).__new__(cls)
            self.__key__ = (fs, args, tuple(kwargs.items()))
            cls.cursor = 0
            cls.fopen: FileLike = fs.open(*args, **kwargs)
            cls._seek = cls.fopen.seek
            # ! Ignore the type error. Is this janky? Yes. Does it work? Also yes.
            # ! We're exploiting duck typing and the infinite mutability of Python
            # ! here. It may be a pain point in the future, but it works well as
            # ! long as we can trust maintainers to not abuse FastSeek.
            cls.fopen.seek = cls.seek  # type: ignore
            cls._read = cls.fopen.read
            cls.fopen.read = cls.read  # type: ignore
        return self

    def close(self: "FastSeek") -> None:
        """A function for closing the file.

        Args:
            self (FastSeek): the FastSeek instance
        """
        self.fopen.close()
        if hasattr(self, "__key__") and (self.__key__ in FastSeek._instances):
            del FastSeek._instances[self.__key__]

    @staticmethod
    def close_all() -> None:
        """A function for closing all open FastSeek instances."""
        for buffer in FastSeek._instances.values():
            buffer.close()

    def seek(self: "FastSeek", cursor: int, *args, **kwargs) -> int:
        """A function for seeking to a position in a file.

        Args:
            cursor (int): the position to seek to
            *args: additional arguments to pass to the seek method
            **kwargs: additional keyword arguments to pass to the seek method

        Returns:
            int: the new position in the file
        """
        change = cursor - self.cursor
        self.cursor = cursor
        return self._seek(change, 1, *args, **kwargs)

    def read(self: "FastSeek", read_length: int, *args, **kwargs) -> str | bytes:
        """A function for reading a number of bytes from a file.

        Args:
            read_length (int): the number of bytes to read
            *args: additional arguments to pass to the read method
            **kwargs: additional keyword arguments to pass to the read method

        Returns:
            str | bytes: the data read from the file
        """
        self.cursor += read_length
        return self._read(read_length, *args, **kwargs)


def uncompressed_tarfile_size(tree_metadata: JSONDict, blocksize: int = 512) -> int:
    """A function for calculating the size of the tarfile before compression.

    Args:
        tree_metadata (JSONDict): the metadata of the tree to calculate the size of
        blocksize (int, optional): the blocksize to use for the tarfile. Defaults to 512.

    Returns:
        int: the size of the tarfile before compression
    """
    size = blocksize  # header block for root of archive
    for item in tree_metadata.values():
        if not isinstance(item, Dict):
            continue
        size += blocksize  # header block for entry
        if not item["is_dir"]:
            item_size = item["size"]
            if not isinstance(item_size, int):
                msg = f"Invalid size for {item['name']}"
                raise ValueError(msg)
            size += entry_size(item_size, blocksize)  # entry data
    size += 2 * blocksize  # tarfile ends with 2 blocks of zeroes
    return size


def parse_header(header: bytes) -> Dict[str, str | int]:
    """A function for parsing a tarfile header.

    Args:
        header (bytes): the header to parse

    Returns:
        Dict[str, str]: a dict containing header data
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


def open_as_fast_seekable(fs: AbstractFileSystem, *args, **kwargs) -> FastSeek:
    """Opens a file as a fast seekable file.

    Args:
        fs (AbstractFileSystem): an fsspec filesystem
        *args: positional arguments to pass to the filesystem open method
        **kwargs: keyword arguments to pass to the filesystem open method

    Returns:
        file: a fast seekable file
    """
    return FastSeek(fs, *args, **kwargs)


def unpack_file(
    tarball_fs: AbstractFileSystem,
    tarball: str,
    unpack_fs: AbstractFileSystem,
    filename: str,
    start: int,
    size: int,
) -> int:
    """A function for unpacking a file from a tarfile.

    Args:
        tarball_fs (AbstractFileSystem): the fsspec filesystem of the tarball
        tarball (str): the path to the tarball
        unpack_fs (AbstractFileSystem): the fsspec filesystem to unpack the file to
        filename (str): the name of the file to unpack to
        start (int): the start position of the file in the tarball
        size (int): the size of the file in the tarball

    Returns:
        int: the size of the file unpacked
    """
    t = open_as_fast_seekable(tarball_fs, tarball, mode="rb", compression="gzip")
    t.seek(start)
    with unpack_fs.open(filename, mode="wb") as f:
        f.write(t.read(size))
    return size


def entry_size(filesize: int, blocksize: int) -> int:
    """A function for calculating the size of a tarfile entry.

    Args:
        filesize (int): the size of the file
        blocksize (int): the blocksize of the tarfile

    Returns:
        int: the size of the entry
    """
    return blocksize * ceil(filesize / blocksize)
