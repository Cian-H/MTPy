"""This module contains type definitions for the mtpy package."""

from typing import Callable, Dict, Iterable, List, Protocol, Sized, TypedDict, TypeVar, Union

from dask import dataframe as dd

T_co = TypeVar("T_co", covariant=True)


JSONValue = Union[None, str, int, float, bool, "JSONDict", "JSONList"]
JSONDict = Dict[str, JSONValue]
JSONList = List[JSONValue]
JSONData = Union[JSONDict, JSONList]


class PathMetadata(TypedDict):
    """A TypedDict outlining a schema for path metadata."""

    hash: int
    is_dir: bool
    size: int


PathMetadataTree = Dict[str, PathMetadata]

CalibrationFunction = Callable[[dd.Series, dd.Series, dd.Series, dd.Series], dd.Series]


class SizedIterable(Iterable[T_co], Sized, Protocol):
    """A Protocol for an Iterable that also has a size."""

    pass


class FileLike(Protocol):
    """A Protocol for a file-like object."""

    def seek(self: "FileLike", offset: int, whence: int = ...) -> int:
        """Seeks to a position in a file.

        Args:
            self (FileLike): the file-like object
            offset (int): the offset to seek to
            whence (int, optional): the reference point for the seek. Defaults to ...

        Returns:
            Any: the result of the seek operation
        """
        ...

    def read(self: "FileLike", n: int = ...) -> bytes | str:
        """Reads a number of bytes from a file.

        Args:
            self (FileLike): the file-like object
            n (int, optional): the number of bytes to read. Defaults to ...

        Returns:
            Any: the bytes read from the file
        """
        ...

    def close(self: "FileLike") -> None:
        """Closes the file-like object.

        Args:
            self (FileLike): the file-like object
        """
        ...

    @property
    def closed(self: "FileLike") -> bool:
        """A property for whether the file-like object is closed.

        Args:
            self (FileLike): the file-like object

        Returns:
            bool: whether the file-like object is closed
        """
        ...
