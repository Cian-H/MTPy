"""A module for dispatching 3d plotting functions."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple, TypedDict

from dask.dataframe import DataFrame
import datashader as ds
from datashader.reductions import Reduction
import holoviews as hv
import holoviews.operation.datashader as hd
from typing_extensions import Unpack

from . import hooks

# This module might be mostly copy/pasted from the 2d version, was busy implementing the 3d version
# when i had to stop to focus on other things.


class DispatchParams(TypedDict):
    """Typed parameters for function dispatchers.

    Attributes:
        x (str): The key of the x axis values
        y (str): The key of the x axis values
        w (str): The key of the x axis values
    """

    x: str
    y: str
    w: str


def plot_dispatch(
    kind: str, chunk: DataFrame, aggregator: Optional[Reduction], **kwargs: Unpack[DispatchParams]
) -> Tuple[List[Callable], List[Dict[str, Any]], Dict[str, Any]]:
    """A dispatcher for 3d plotting functions.

    Args:
        kind (str): the kind of plot
        chunk (DataFrame): the chunk of data to plot
        aggregator (Optional[Reduction]): the aggregator function to use
        **kwargs (Unpack[DispatchParams]): keyword arguments to be passed to the plotting function
            for the given kind

    Raises:
        ValueError: an unknown kind of 2d plot was given

    Returns:
        Tuple[List[Callable], List[Dict[str, Any]], Dict[str, Any]]: a tuple of
            (f_list, kwargs_list, opts) for generating a holoviz plot
    """
    # if no aggregator is given, default to aggregated mean of w
    if aggregator is None:
        aggregator = ds.reductions.mean(kwargs["w"])

    if kind == "scatter":
        return scatter(chunk, aggregator, **kwargs)

    msg = f"Unknown 2d plot kind given: {kind}"
    raise ValueError(msg)


def scatter(
    chunk: DataFrame, aggregator: Optional[Reduction], **kwargs: Unpack[DispatchParams]
) -> Tuple[List[Callable], List[Dict[str, Any]], Dict[str, Any]]:
    """Dispatches a scatter plot.

    Args:
        chunk (DataFrame): the chunk of data to be plotted
        aggregator (Optional[Reduction]): the aggregator function to use
        **kwargs (Unpack[DispatchParams]): keyword arguments to be passed to the scatter plot

    Returns:
        Tuple[List[Callable], List[Dict[str, Any]], Dict[str, Any]]: a tuple of
            (f_list, kwargs_list, opts) for generating a holoviz plot
    """
    kdims = [kwargs.get("x", "x"), kwargs.get("y", "y")]
    w_col = kwargs.get("w", "t")

    from mtpy.utils.type_guards import guarded_callable, guarded_str_key_dict

    f_list = [
        guarded_callable(hv.Points),
        guarded_callable(hd.rasterize),
        guarded_callable(hd.dynspread),
    ]
    kwargs_list = [
        guarded_str_key_dict(
            {
                "kdims": kdims,
                "vdims": [w_col] + [x for x in chunk.columns if (x not in kdims) and (x != w_col)],
                "label": "2D Scatter",
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
) -> Tuple[List[Callable], List[Dict[str, Any]], Dict[str, Any]]:
    """Dispatches a distribution plot.

    Args:
        chunk (DataFrame): the chunk of data to be plotted
        aggregator (Optional[Reduction]): the aggregator function to use
        **kwargs (Unpack[DispatchParams]): keyword arguments to be passed to the distribution plot

    Returns:
        Tuple[List[Callable], List[Dict[str, Any]], Dict[str, Any]]: a tuple of
            (f_list, kwargs_list, opts) for generating a holoviz plot
    """
    from mtpy.utils.type_guards import guarded_callable, guarded_str_key_dict

    f_list = [guarded_callable(hv.Distribution)]
    kwargs_list = [guarded_str_key_dict({})]
    opts = guarded_str_key_dict({})

    return f_list, kwargs_list, opts
