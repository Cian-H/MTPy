"""A module containing functions for safely coercing types."""

from typing import Any, TypeVar

from .types import SizedIterable

T = TypeVar("T")


def ensure_sized_iterable(obj: Any) -> SizedIterable[T]:  # noqa: ANN401
    """Ensures that an object is an iterable.

    Args:
        obj (Any): the object to ensure is an iterable

    Returns:
        SizedIterable[T]: the object as an iterable
    """
    from .type_guards import is_iterable, is_sized_iterable

    if is_sized_iterable(obj):
        return obj
    if is_iterable(obj):
        return list(obj)
    return [obj]
