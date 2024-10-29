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

from mtpy.base.feedback.protocol import ProgressBarProtocol
from mtpy.loaders.protocol import LoaderProtocol
from mtpy.utils.types import (
    JSONData,
    JSONDict,
    JSONList,
    JSONValue,
    PathMetadata,
    PathMetadataTree,
    SizedIterable,
    TypedSizedIterable,
)
from mtpy.vis.protocol import PlotterProtocol

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
is_dask_number, guarded_dask_number = create_type_guard(dd.dd.Number)
is_bytes, guarded_bytes = create_type_guard(bytes)
is_bytearray, guarded_bytearray = create_type_guard(bytearray)
is_json_dict, guarded_json_dict = create_type_guard(JSONDict)
is_json_list, guarded_json_list = create_type_guard(JSONList)
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
    if not isinstance(t, tuple):
        return False
    if len(t) != TWO:
        return False
    return all(isinstance(x, float) for x in t)


def is_callable(t: object, _type: Type[T]) -> TypeGuard[Callable[..., T]]:
    """Type guard for a callable.

    Args:
        t (object): the object to check
        _type (Type[T]): the type that the callable returns

    Returns:
        TypeGuard[Callable[..., T]]: True if the object is a callable, False otherwise
    """
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
    return isinstance(t, Iterable)


def is_sized(t: object) -> TypeGuard[Sized]:
    """Type guard for a sized object.

    Args:
        t (object): the object to check

    Returns:
        TypeGuard[Sized]: True if the object is sized, False otherwise
    """
    return isinstance(t, Sized)


def is_sizediterable(t: object) -> TypeGuard[SizedIterable[T]]:
    """Type guard for a sized iterable.

    Args:
        t (object): the object to check

    Returns:
        TypeGuard[SizedIterable[T]]: True if the object is a sized iterable, False otherwise
    """
    return is_iterable(t) and is_sized(t)


def is_typedsizediterable(t: object, _type: Type[T]) -> TypeGuard[TypedSizedIterable[T]]:
    """Type guard for a sized iterable.

    Args:
        t (object): the object to check
        _type (Type[T]): the type of the elements inside the SizedIterable

    Returns:
        TypeGuard[TypedSizedIterable[T]]: True if the object is a sized iterable, False otherwise
    """
    if not is_sizediterable(t):
        return False
    if TYPE_CHECKING:
        return all(map(isinstance, t, repeat(_type)))
    return True


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
    if not is_typedsizediterable(t, _type):
        msg = f"Expected a TypedSizedIterable[{_type}]"
        raise TypeError(msg)
    return t


def is_json_data(t: object) -> TypeGuard[JSONData]:
    """Type guard for JSON data.

    Args:
        t (object): the object to check

    Returns:
        TypeGuard[JSONData]: True if the object is JSON data, False otherwise
    """
    return isinstance(t, (dict, list))


def guarded_json_data(t: object) -> JSONData:
    """A function for type guarding JSON data.

    Args:
        t (object): the object to check

    Raises:
        TypeError: if the type fails the guard check

    Returns:
        JSONData: the object if it is JSON data
    """
    if not is_json_data(t):
        msg = "Expected JSON data"
        raise TypeError(msg)
    return t


def is_json_value(t: object) -> TypeGuard[JSONValue]:
    """Type guard for JSON values.

    Args:
        t (object): the object to check

    Returns:
        TypeGuard[JSONValue]: True if the object is a JSON value, False otherwise
    """
    return isinstance(t, (str, int, float, bool, dict, list))


def guarded_json_value(t: object) -> JSONValue:
    """A function for type guarding JSON values.

    Args:
        t (object): the object to check

    Raises:
        TypeError: if the type fails the guard check

    Returns:
        JSONValue: the object if it is a JSON value
    """
    if not is_json_value(t):
        msg = "Expected a JSON value"
        raise TypeError(msg)
    return t


def is_plotter_protocol(t: object) -> TypeGuard[PlotterProtocol]:
    """Type guard for plotter protocols.

    Args:
        t (object): the object to check

    Returns:
        TypeGuard[PlotterProtocol]: True if the object is a plotter protocol, False otherwise.
    """
    return isinstance(t, PlotterProtocol)


def guarded_plotter_protocol(t: object) -> PlotterProtocol:
    """A function for type guarding plotter protocols.

    Args:
        t (object): the object to check

    Raises:
        TypeError: if the type fails the guard check

    Returns:
        PlotterProtocol: the object if it is a plotter protocol
    """
    if not is_plotter_protocol(t):
        msg = "Expected a PlotterProtocol"
        raise TypeError(msg)
    return t


def is_loader_protocol(t: object) -> TypeGuard[LoaderProtocol]:
    """Type guard for loader protocols.

    Args:
        t (object): the object to check

    Returns:
        TypeGuard[LoaderProtocol]: True if the object is a loader protocol, False otherwise.
    """
    return isinstance(t, LoaderProtocol)


def guarded_loader_protocol(t: object) -> LoaderProtocol:
    """A function for type guarding loader protocols.

    Args:
        t (object): the object to check

    Raises:
        TypeError: if the type fails the guard check

    Returns:
        LoaderProtocol: the object if it is a loader protocol
    """
    if not is_loader_protocol(t):
        msg = "Expected a LoaderProtocol"
        raise TypeError(msg)
    return t


def is_progressbar_protocol(t: object) -> TypeGuard[ProgressBarProtocol[T]]:
    """Type guard for progressbar protocols.

    Args:
        t (object): the object to check

    Returns:
        TypeGuard[ProgressBarProtocol[T]]: True if the object is a progressbar protocol,
        False otherwise.
    """
    return isinstance(t, ProgressBarProtocol)


def guarded_progressbar_protocol(t: object) -> ProgressBarProtocol[T]:
    """A function for type guarding progressbar protocols.

    Args:
        t (object): the object to check

    Raises:
        TypeError: if the type fails the guard check

    Returns:
        ProgressBarProtocol[T]: the object if it is a progressbar protocol
    """
    if not is_progressbar_protocol(t):
        msg = "Expected a ProgressBarProtocol"
        raise TypeError(msg)
    return t
