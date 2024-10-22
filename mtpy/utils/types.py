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
