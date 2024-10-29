"""This module contains type definitions for the mtpy package."""

from typing import (
    Callable,
    Dict,
    Iterable,
    List,
    Protocol,
    Sized,
    TypedDict,
    TypeVar,
    Union,
)

from dask import dataframe as dd

T_co = TypeVar("T_co", covariant=True)


JSONValue = Union[None, str, int, float, bool, "JSONDict", "JSONList"]
JSONDict = Dict[str, JSONValue]
JSONList = List[JSONValue]
JSONData = Union[JSONDict, JSONList]


class StatsDict(TypedDict):
    """A TypedDict for returning statistics from a dask table."""

    min: float
    max: float
    mean: float
    std: float
    stderr: float
    ci_error: float
    ci_min: float
    ci_max: float


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


class TypedSizedIterable(Iterable[T_co], Sized, Protocol):
    """A Protocol for an Iterable that also has a type and a size."""

    pass
