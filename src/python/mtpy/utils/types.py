from typing import Any, Dict, Iterable, List, Protocol, Sized, TypeVar, Union


T = TypeVar("T", covariant=True)


JSONValues = Union[str, int, float, bool, "JSONDict", "JSONList"]
JSONDict = Dict[str, JSONValues]
JSONList = List[JSONValues]
JSONData = Union[JSONDict, JSONList]


class SizedIterable(Iterable[T], Sized, Protocol):
    pass


class FileLike(Protocol):
    def seek(self, offset: int, whence: int = ...) -> Any:
        ...

    def read(self, n: int = ...) -> Any:
        ...

    def close(self) -> None:
        ...

    @property
    def closed(self) -> bool:
        ...
