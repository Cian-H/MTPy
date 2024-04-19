# ruff: noqa: ANN401 # Disable ANN401 since the module is a collection of type guards

"""A module containing type guards for enforcing type safety.

Developer note: because they are prevalent throughout the program when using these type
guarding functions it is advisable to defer their imports. This helps avoid accidental
circular imports since these will be imported at many different points during class
composition.
"""

from typing import Any, Callable, Dict, Iterable, Sized, Tuple, TypeGuard, TypeVar

from dask import array as da
from dask import dataframe as dd

from mtpy.base.feedback.protocol import ProgressBarProtocol
from mtpy.loaders.protocol import LoaderProtocol
from mtpy.utils.types import (
    JSONData,
    JSONDict,
    JSONList,
    JSONValue,
    PathMetadataTree,
    SizedIterable,
)
from mtpy.vis.protocol import PlotterProtocol

T = TypeVar("T")
TWO = 2


def create_type_guard(_type: type[T]) -> Tuple[Callable[[Any], TypeGuard[T]], Callable[[Any], T]]:
    """Create type guards (`is_<type>` and `guarded_<type>`) for a given type.

    Args:
        type (T): the type to create guards for

    Returns:
        Tuple[Callable[[Any], TypeGuard[T]], Callable[[Any], T]]: the type guards
    """

    def is_type(t: Any) -> TypeGuard[T]:
        return isinstance(t, _type)

    def guarded_type(t: Any) -> T:
        if not is_type(t):
            msg = f"Expected {_type}"
            raise TypeError(msg)
        return t

    is_type.__name__ = f"is_{_type.__name__}"
    is_type.__doc__ = f"""Type guard for {_type}.

    Args:
        t (Any): the object to check

    Returns:
        TypeGuard[{_type}]: True if the object is {_type}, False otherwise
    """

    guarded_type.__name__ = f"guarded_{_type.__name__}"
    guarded_type.__doc__ = f"""A function for type guarding {_type}.

    Args:
        t (Any): the object to check

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
is_json_dict, guarded_json_dict = create_type_guard(JSONDict)
is_json_list, guarded_json_list = create_type_guard(JSONList)
is_pathmetadatatree, guarded_pathmetadatatree = create_type_guard(PathMetadataTree)


# The following are type guards that need a bit more of a custom implementation
def is_str_key_dict(t: Any) -> TypeGuard[Dict[str, Any]]:
    """Type guard for a dictionary with string keys.

    Args:
        t (Any): the object to check

    Returns:
        TypeGuard[Dict[str, T]]: True if the object is a dictionary with string keys,
            False otherwise
    """
    return isinstance(t, dict) and all(isinstance(k, str) for k in t)


def guarded_str_key_dict(t: Any) -> Dict[str, Any]:
    """A function for type guarding a dictionary with string keys.

    Args:
        t (Any): the object to check

    Raises:
        TypeError: if the type fails the guard check

    Returns:
        Dict[str, T]: the object if it is a dictionary with string keys
    """
    if not is_str_key_dict(t):
        msg = "Expected a dictionary with string keys"
        raise TypeError(msg)
    return t


def is_float_pair_tuple(t: Any) -> TypeGuard[Tuple[float, float]]:
    """Type guard for a tuple of two floats.

    Args:
        t (Any): the tuple to check

    Returns:
        TypeGuard[Tuple[float, float]]: True if the tuple has two floats, False otherwise
    """
    if not isinstance(t, tuple):
        return False
    if len(t) != TWO:
        return False
    if not all(isinstance(x, float) for x in t):
        return False
    return True


def is_callable(t: Any) -> TypeGuard[Callable]:
    """Type guard for a callable.

    Args:
        t (Any): the object to check

    Returns:
        TypeGuard[Callable]: True if the object is a callable, False otherwise
    """
    return callable(t)


def guarded_callable(t: Any) -> Callable:
    """A function for type guarding a callable.

    Args:
        t (Any): the object to check

    Raises:
        TypeError: if the type fails the guard check

    Returns:
        Callable: the object if it is callable
    """
    if not is_callable(t):
        msg = "Expected a callable"
        raise TypeError(msg)
    return t


def is_iterable(t: Any) -> TypeGuard[Iterable[T]]:
    """Type guard for an iterable.

    Args:
        t (Any): the iterable to check

    Returns:
        TypeGuard[Iterable[T]]: True if the object is an iterable, False otherwise
    """
    return isinstance(t, Iterable)


def is_sized(t: Any) -> TypeGuard[Sized]:
    """Type guard for a sized object.

    Args:
        t (Any): the object to check

    Returns:
        TypeGuard[Sized]: True if the object is sized, False otherwise
    """
    return isinstance(t, Sized)


def is_sized_iterable(t: Any) -> TypeGuard[SizedIterable[T]]:
    """Type guard for a sized iterable.

    Args:
        t (Any): the object to check

    Returns:
        TypeGuard[SizedIterable[T]]: True if the object is a sized iterable, False otherwise
    """
    return is_iterable(t) and is_sized(t)


def is_json_data(t: Any) -> TypeGuard[JSONData]:
    """Type guard for JSON data.

    Args:
        t (Any): the object to check

    Returns:
        TypeGuard[JSONData]: True if the object is JSON data, False otherwise
    """
    return isinstance(t, (dict, list))


def guarded_json_data(t: Any) -> JSONData:
    """A function for type guarding JSON data.

    Args:
        t (Any): the object to check

    Raises:
        TypeError: if the type fails the guard check

    Returns:
        JSONData: the object if it is JSON data
    """
    if not is_json_data(t):
        msg = "Expected JSON data"
        raise TypeError(msg)
    return t


def is_json_value(t: Any) -> TypeGuard[JSONValue]:
    """Type guard for JSON values.

    Args:
        t (Any): the object to check

    Returns:
        TypeGuard[JSONValues]: True if the object is a JSON value, False otherwise
    """
    return isinstance(t, (str, int, float, bool, dict, list))


def guarded_json_value(t: Any) -> JSONValue:
    """A function for type guarding JSON values.

    Args:
        t (Any): the object to check

    Raises:
        TypeError: if the type fails the guard check

    Returns:
        JSONValues: the object if it is a JSON value
    """
    if not is_json_value(t):
        msg = "Expected a JSON value"
        raise TypeError(msg)
    return t


def is_plotter_protocol(t: Any) -> TypeGuard[PlotterProtocol]:
    """Type guard for plotter protocols.

    Args:
        t: the object to check

    Returns:
        TypeGuard[PlotterProtocol]: True if the object is a plotter protocol, False otherwise.
    """
    return isinstance(t, PlotterProtocol)


def guarded_plotter_protocol(t: Any) -> PlotterProtocol:
    """A function for type guarding plotter protocols.

    Args:
        t: the object to check

    Raises:
        TypeError: if the type fails the guard check

    Returns:
        PlotterProtocol: the object if it is a plotter protocol
    """
    if not is_plotter_protocol(t):
        msg = "Expected a PlotterProtocol"
        raise TypeError(msg)
    return t


def is_loader_protocol(t: Any) -> TypeGuard[LoaderProtocol]:
    """Type guard for loader protocols.

    Args:
        t: the object to check

    Returns:
        TypeGuard[LoaderProtocol]: True if the object is a loader protocol, False otherwise.
    """
    return isinstance(t, LoaderProtocol)


def guarded_loader_protocol(t: Any) -> LoaderProtocol:
    """A function for type guarding loader protocols.

    Args:
        t: the object to check

    Raises:
        TypeError: if the type fails the guard check

    Returns:
        LoaderProtocol: the object if it is a loader protocol
    """
    if not is_loader_protocol(t):
        msg = "Expected a LoaderProtocol"
        raise TypeError(msg)
    return t


def is_progressbar_protocol(t: Any) -> TypeGuard[ProgressBarProtocol]:
    """Type guard for progressbar protocols.

    Args:
        t: the object to check

    Returns:
        TypeGuard[ProgressBarProtocol]: True if the object is a progressbar protocol,
        False otherwise.
    """
    return isinstance(t, ProgressBarProtocol)


def guarded_progressbar_protocol(t: Any) -> ProgressBarProtocol:
    """A function for type guarding progressbar protocols.

    Args:
        t: the object to check

    Raises:
        TypeError: if the type fails the guard check

    Returns:
        ProgressBarProtocol: the object if it is a progressbar protocol
    """
    if not is_progressbar_protocol(t):
        msg = "Expected a ProgressBarProtocol"
        raise TypeError(msg)
    return t
