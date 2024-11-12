# ruff: noqa: ANN401 # Disable ANN401 since the module is a collection of type guards

"""A module containing type guards for enforcing type safety.

Developer note: because they are prevalent throughout the program when using these type
guarding functions it is advisable to defer their imports. This helps avoid accidental
circular imports since these will be imported at many different points during class
composition.
"""

from itertools import repeat
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    Sized,
    Tuple,
    Type,
    TypeGuard,
    TypeVar,
)

from dask import array as da
from dask import dataframe as dd
import dask_expr as dx

from mtpy.utils.types import (
    PathMetadata,
    PathMetadataTree,
    SizedIterable,
    TOMLData,
    TOMLDict,
    TOMLList,
    TOMLValue,
    TypedSizedIterable,
)

T = TypeVar("T")
TWO = 2


def create_type_guard(
    _type: Type[T],
) -> Tuple[Callable[[object], TypeGuard[T]], Callable[[object], T]]:
    """Create type guards (`is_<type>` and `guarded_<type>`) for a given type.

    Args:
        _type (Type[T]): the type to create guards for

    Returns:
        Tuple[Callable[[object], TypeGuard[T]], Callable[[object], T]]: the type guards
    """
    if not TYPE_CHECKING:

        def is_type(t: object) -> TypeGuard[T]:
            return True

        def guarded_type(t: object) -> T:
            return t

    else:

        def is_type(t: object) -> TypeGuard[T]:
            return isinstance(t, _type)

        def guarded_type(t: object) -> T:
            if not is_type(t):
                msg = f"Expected {_type}"
                raise TypeError(msg)
            return t

    is_type.__name__ = f"is_{_type.__name__}"
    is_type.__doc__ = f"""Type guard for {_type}.

    Args:
        t (object): the object to check

    Returns:
        TypeGuard[{_type}]: True if the object is {_type}, False otherwise
    """

    guarded_type.__name__ = f"guarded_{_type.__name__}"
    guarded_type.__doc__ = f"""A function for type guarding {_type}.

    Args:
        t (object): the object to check

    Returns:
        {_type}: the object if it is {_type}
    """

    return is_type, guarded_type


is_int, guarded_int = create_type_guard(int)
is_dask_dataframe, guarded_dask_dataframe = create_type_guard(dd.DataFrame)
is_dask_array, guarded_dask_array = create_type_guard(da.Array)
is_dask_series, guarded_dask_series = create_type_guard(dd.Series)
is_dask_number, guarded_dask_number = create_type_guard(dx.Number)
is_bytes, guarded_bytes = create_type_guard(bytes)
is_bytearray, guarded_bytearray = create_type_guard(bytearray)
is_tomldict, guarded_tomldict = create_type_guard(TOMLDict)
is_tomllist, guarded_tomllist = create_type_guard(TOMLList)
is_pathmetadata, guarded_pathmetadata = create_type_guard(PathMetadata)
is_pathmetadatatree, guarded_pathmetadatatree = create_type_guard(PathMetadataTree)


# The following are type guards that need a bit more of a custom implementation
def is_str_key_dict(t: object) -> TypeGuard[Dict[str, Any]]:
    """Type guard for a dictionary with string keys.

    Args:
        t (object): the object to check

    Returns:
        TypeGuard[Dict[str, Any]]: True if the object is a dictionary with string keys,
            False otherwise
    """
    if not TYPE_CHECKING:
        return True
    return isinstance(t, dict) and all(isinstance(k, str) for k in t)


def guarded_str_key_dict(t: object) -> Dict[str, Any]:
    """A function for type guarding a dictionary with string keys.

    Args:
        t (object): the object to check

    Raises:
        TypeError: if the type fails the guard check

    Returns:
        Dict[str, Any]: the object if it is a dictionary with string keys
    """
    if not TYPE_CHECKING:
        return t
    if not is_str_key_dict(t):
        msg = "Expected a dictionary with string keys"
        raise TypeError(msg)
    return t


def is_float_pair_tuple(t: object) -> TypeGuard[Tuple[float, float]]:
    """Type guard for a tuple of two floats.

    Args:
        t (object): the tuple to check

    Returns:
        TypeGuard[Tuple[float, float]]: True if the tuple has two floats, False otherwise
    """
    if not TYPE_CHECKING:
        return True
    return isinstance(t, tuple) and (len(t) == TWO) and all(isinstance(x, float) for x in t)


def is_callable(t: object, _type: Type[T]) -> TypeGuard[Callable[..., T]]:
    """Type guard for a callable.

    Args:
        t (object): the object to check
        _type (Type[T]): the type that the callable returns

    Returns:
        TypeGuard[Callable[..., T]]: True if the object is a callable, False otherwise
    """
    if not TYPE_CHECKING:
        return True
    return callable(t)


def guarded_callable(t: object, _type: Type[T]) -> Callable[..., T]:
    """A function for type guarding a callable.

    Args:
        t (object): the object to check
        _type (Type[T]): the type that the callable returns

    Raises:
        TypeError: if the type fails the guard check

    Returns:
        Callable[..., T]: the object if it is callable
    """
    if not TYPE_CHECKING:
        return t
    if not is_callable(t, _type):
        msg = f"Expected a Callable[{_type}]"
        raise TypeError(msg)
    return t


def is_iterable(t: object) -> TypeGuard[Iterable[T]]:
    """Type guard for an iterable.

    Args:
        t (object): the iterable to check

    Returns:
        TypeGuard[Iterable[T]]: True if the object is an iterable, False otherwise
    """
    if not TYPE_CHECKING:
        return True
    return isinstance(t, Iterable)


def is_sized(t: object) -> TypeGuard[Sized]:
    """Type guard for a sized object.

    Args:
        t (object): the object to check

    Returns:
        TypeGuard[Sized]: True if the object is sized, False otherwise
    """
    if not TYPE_CHECKING:
        return True
    return isinstance(t, Sized)


def is_sizediterable(t: object) -> TypeGuard[SizedIterable[T]]:
    """Type guard for a sized iterable.

    Args:
        t (object): the object to check

    Returns:
        TypeGuard[SizedIterable[T]]: True if the object is a sized iterable, False otherwise
    """
    if not TYPE_CHECKING:
        return True
    return is_iterable(t) and is_sized(t)


def is_typedsizediterable(t: object, _type: Type[T]) -> TypeGuard[TypedSizedIterable[T]]:
    """Type guard for a sized iterable.

    Args:
        t (object): the object to check
        _type (Type[T]): the type of the elements inside the SizedIterable

    Returns:
        TypeGuard[TypedSizedIterable[T]]: True if the object is a sized iterable, False otherwise
    """
    if not TYPE_CHECKING:
        return True
    return is_sizediterable(t) and all(map(isinstance, t, repeat(_type)))


def guarded_typedsizediterable(t: object, _type: Type[T]) -> TypedSizedIterable[T]:
    """A function for type guarding a TypedSizedIterable.

    Args:
        t (object): the object to check
        _type (Type[T]): the type of the elements inside the SizedIterable

    Raises:
        TypeError: if the type fails the guard check

    Returns:
        TypedSizedIterable[T]: the object if it is callable
    """
    if not TYPE_CHECKING:
        return t
    if not is_typedsizediterable(t, _type):
        msg = f"Expected a TypedSizedIterable[{_type}]"
        raise TypeError(msg)
    return t


def is_toml_data(t: object) -> TypeGuard[TOMLData]:
    """Type guard for TOML data.

    Args:
        t (object): the object to check

    Returns:
        TypeGuard[TOMLData]: True if the object is TOML data, False otherwise
    """
    if not TYPE_CHECKING:
        return True
    return isinstance(t, (dict, list))


def guarded_toml_data(t: object) -> TOMLData:
    """A function for type guarding TOML data.

    Args:
        t (object): the object to check

    Raises:
        TypeError: if the type fails the guard check

    Returns:
        TOMLData: the object if it is TOML data
    """
    if not TYPE_CHECKING:
        return t
    if not is_toml_data(t):
        msg = "Expected TOML data"
        raise TypeError(msg)
    return t


def is_toml_value(t: object) -> TypeGuard[TOMLValue]:
    """Type guard for TOML values.

    Args:
        t (object): the object to check

    Returns:
        TypeGuard[TOMLValue]: True if the object is a TOML value, False otherwise
    """
    if not TYPE_CHECKING:
        return True
    return isinstance(t, (str, int, float, bool, dict, list))


def guarded_toml_value(t: object) -> TOMLValue:
    """A function for type guarding TOML values.

    Args:
        t (object): the object to check

    Raises:
        TypeError: if the type fails the guard check

    Returns:
        TOMLValue: the object if it is a JSON value
    """
    if not TYPE_CHECKING:
        return t
    if not is_toml_value(t):
        msg = "Expected a toml value"
        raise TypeError(msg)
    return t
