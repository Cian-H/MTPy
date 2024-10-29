"""A module containing functions for safely coercing types."""

from typing import Any, Type, TypeVar

from .types import TypedSizedIterable

T = TypeVar("T")


def ensure_typedsizediterable(obj: Any, _type: Type[T]) -> TypedSizedIterable[T]:  # noqa: ANN401
    """Ensures that an object is an iterable.

    Args:
        obj (Any): the object to ensure is an iterable
        _type (Type[T]): the type of the elements inside the TypedSizedIterable

    Returns:
        TypedSizedIterable[T]: the object as a TypedSizedIterable

    Raises:
        TypeError: the object cannot be coerced into a valid TypedSizedIterable[T]
    """
    from .type_guards import (
        guarded_typedsizediterable,
        is_iterable,
        is_sizediterable,
        is_typedsizediterable,
    )

    if is_typedsizediterable(obj, _type):
        return obj
    if is_sizediterable(obj):
        return guarded_typedsizediterable(obj, _type)
    if is_iterable(obj):
        return guarded_typedsizediterable(list(obj), _type)
    if isinstance(obj, _type):
        return guarded_typedsizediterable([obj], _type)
    msg = f"Expected `TypedSizedIterable[{_type}]` or `{_type}`"
    raise TypeError(msg)
