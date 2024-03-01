from typing import Any, TypeVar

from .type_guards import is_iterable, is_sized_iterable
from .types import SizedIterable


T = TypeVar("T")


def ensure_sized_iterable(obj: Any) -> SizedIterable[T]:
    """Ensures that an object is an iterable.

    Args:
        obj (Any): the object to ensure is an iterable

    Returns:
        Iterable[T]: the object as an iterable
    """
    if is_sized_iterable(obj):
        return obj
    elif is_iterable(obj):
        return list(obj)
    else:
        return [obj]
