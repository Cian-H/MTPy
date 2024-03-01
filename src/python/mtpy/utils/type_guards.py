from typing import Any, Callable, Dict, Iterable, Sized, Tuple, TypeGuard, TypeVar

from dask import dataframe as dd

from .types import SizedIterable


T = TypeVar("T")


def is_str_key_dict(d: Any) -> TypeGuard[Dict[str, Any]]:
    """Type guard for a dictionary with string keys and any values.

    Args:
        d (Dict): the dictionary to check

    Returns:
        TypeGuard[Dict[str, Any]]: True if the dictionary has string keys, False otherwise
    """
    if not isinstance(d, dict):
        return False
    else:
        return all(isinstance(key, str) for key in d.keys())


def guarded_str_key_dict(d: Any) -> Dict[str, Any]:
    """A function for type guarding a dictionary with string keys and any values.

    Args:
        d (Any): the dictionary to check

    Returns:
        Dict[str, Any]: the dictionary if it has string keys
    """
    if not is_str_key_dict(d):
        raise TypeError("Expected a dictionary with string keys")
    return d


def is_float_pair_tuple(t: Any) -> TypeGuard[Tuple[float, float]]:
    """Type guard for a tuple of two floats.

    Args:
        t (Any): the tuple to check

    Returns:
        TypeGuard[Tuple[float, float]]: True if the tuple has two floats, False otherwise
    """
    if not isinstance(t, tuple):
        return False
    if len(t) != 2:
        return False
    if not all(isinstance(x, float) for x in t):
        return False
    return True


def is_dask_dataframe(df: Any) -> TypeGuard[dd.DataFrame]:
    """Type guard for a dask dataframe.

    Args:
        df (Any): the dataframe to check

    Returns:
        TypeGuard[dd.DataFrame]: True if the dataframe is a dask dataframe, False otherwise
    """
    return isinstance(df, dd.DataFrame)


def guarded_dask_dataframe(df: Any) -> dd.DataFrame:
    """A function for type guarding a dask dataframe.

    Args:
        df (Any): the dataframe to check

    Returns:
        dd.DataFrame: the dataframe if it is a dask dataframe
    """
    if not is_dask_dataframe(df):
        raise TypeError("Expected a dask dataframe")
    return df


def is_iterable(t: Any) -> TypeGuard[Iterable[T]]:
    """Type guard for an iterable.

    Args:
        t (Any): the iterable to check

    Returns:
        TypeGuard[Iterable[T]]: True if the object is an iterable, False otherwise
    """
    return isinstance(t, Iterable)


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

    Returns:
        Callable: the object if it is callable
    """
    if not is_callable(t):
        raise TypeError("Expected a callable")
    return t


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
