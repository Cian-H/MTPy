"""A module for dispatching 2d plotting functions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple, TypedDict, Unpack

from dask.dataframe import DataFrame
from datashader.reductions import Reduction
from holoviews.element import Chart

from . import hooks


class DispatchParams(TypedDict):
    """Typed parameters for function dispatchers.

    Attributes:
        x (str): The key of the x axis values
        y (str): The key of the y axis values
        w (str): The key of the w axis values
    """

    x: str
    y: str
    w: str


def guarded_dispatchparams(t: object) -> DispatchParams:
    """A type guard for DispatchParams TypeDDicts.

    Args:
        t (object): the object to be type guarded

    Returns:
        DispatchParams: the guarded type

    Raises:
        TypeError: the object being passed is not of type TypeGuard[DispatchParams]
    """
    if not TYPE_CHECKING:
        return t
    if (
        isinstance(t, dict)
        and hasattr(t, "x")
        and isinstance(str, t["x"])
        and hasattr(t, "y")
        and isinstance(str, t["y"])
        and hasattr(t, "w")
        and isinstance(str, t["w"])
    ):
        return DispatchParams(x=t["x"], y=t["y"], w=t["w"])
    msg = "Expected DispatchParams"
    raise TypeError(msg)


def plot_dispatch(
    kind: str, chunk: DataFrame, aggregator: Optional[Reduction], **kwargs: Unpack[DispatchParams]
) -> Tuple[List[Callable[..., Chart]], List[Dict[str, Any]], Dict[str, Any]]:
    """A dispatcher for 2d plotting functions.

    Args:
        kind (str): the kind of plot
        chunk (DataFrame): the chunk of data to plot
        aggregator (Optional[Reduction]): the aggregator function to use
        **kwargs (Unpack[DispatchParams]): keyword arguments to be passed to the plotting function
            for the given plot kind

    Raises:
        ValueError: an unknown kind of 2d plot was given

    Returns:
        Tuple[List[Callable[..., Chart]], List[Dict[str, Any]], Dict[str, Any]]: a tuple
            of (f_list, kwargs_list, opts) for generating a holoviz plot
    """
    if kind == "scatter":
        return scatter(chunk, aggregator, **kwargs)
    if kind == "distribution":
        return distribution(chunk, aggregator, **kwargs)

    msg = f"Unknown 2d plot kind given: {kind}"
    raise ValueError(msg)


def scatter(
    chunk: DataFrame, aggregator: Optional[Reduction], **kwargs: Unpack[DispatchParams]
) -> Tuple[List[Callable[..., Chart]], List[Dict[str, Any]], Dict[str, Any]]:
    """Dispatches a scatter plot.

    Args:
        chunk (DataFrame): the chunk of data to be plotted
        aggregator (Optional[Reduction]): the aggregator function to use
        **kwargs (Unpack[DispatchParams]): keyword arguments to be passed to the scatter plot

    Returns:
        Tuple[List[Callable[..., Chart]], List[Dict[str, Any]], Dict[str, Any]]: a tuple
            of (f_list, kwargs_list, opts) for generating a holoviz plot
    """
    import datashader as ds
    import holoviews as hv
    import holoviews.operation.datashader as hd

    from mtpy.utils.type_guards import guarded_callable, guarded_str_key_dict

    # if no aggregator is given, default to aggregated mean of w
    if aggregator is None:
        aggregator = ds.reductions.mean(kwargs["w"])

    kdims = [kwargs.get("x", "x"), kwargs.get("y", "y")]
    w_col = kwargs.get("w", "t")

    f_list = [
        guarded_callable(hv.Points, hv.Points),
        guarded_callable(hd.rasterize, hd.rasterize),
        guarded_callable(hd.dynspread, hd.dynspread),
    ]
    kwargs_list = [
        guarded_str_key_dict(
            {
                "kdims": kdims,
                "vdims": [w_col] + [x for x in chunk.columns if (x not in kdims) and (x != w_col)],
                "label": f"2D Scatter {' vs '.join(([*kdims, w_col]))}",
            }
        ),
        guarded_str_key_dict({"aggregator": aggregator}),
        guarded_str_key_dict({}),
    ]

    opts = guarded_str_key_dict(
        {
            "colorbar": kwargs.get("colorbar", True),
            "cmap": kwargs.get("cmap", "plasma"),
            "hooks": [hooks.scatter(w_col)],
        }
    )

    return f_list, kwargs_list, opts


def distribution(
    chunk: DataFrame, aggregator: Optional[Reduction], **kwargs: Unpack[DispatchParams]
) -> Tuple[List[Callable[..., Chart]], List[Dict[str, Any]], Dict[str, Any]]:
    """Dispatches a distribution plot.

    Args:
        chunk (DataFrame): the chunk of data to be plotted
        aggregator (Optional[Reduction]): the aggregator function to use
        **kwargs (Unpack[DispatchParams]): keyword arguments to be passed to the distribution plot

    Returns:
        Tuple[List[Callable[..., Chart]], List[Dict[str, Any]], Dict[str, Any]]: a tuple
            of (f_list, kwargs_list, opts) for generating a holoviz plot
    """
    import holoviews as hv

    from mtpy.utils.type_guards import guarded_callable, guarded_str_key_dict

    kdims = [kwargs["x"]]

    f_list = [guarded_callable(hv.Distribution, hv.Distribution)]
    kwargs_list = [guarded_str_key_dict({"kdims": kdims, "label": f"Distribution {kdims[0]}"})]
    opts = guarded_str_key_dict({})

    return f_list, kwargs_list, opts
