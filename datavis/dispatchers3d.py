from __future__ import annotations

from . import hooks3d as hooks

from dask.dataframe import DataFrame
from datashader.reductions import Reduction
import datashader as ds
import holoviews as hv
import holoviews.operation.datashader as hd

# This module might be mostly copy/pasted from the 2d version, was busy implementing the 3d version
# when i had to stop to focus on other things.


def plot_dispatch(kind: str, chunk: DataFrame, aggregator: Reduction | None, **kwargs) -> tuple:
    """a dispatcher for 3d plotting functions

    Args:
        kind (str): the kind of plot
        chunk (DataFrame): the chunk of data to plot
        aggregator (Reduction | None): the aggregator function to use

    Raises:
        ValueError: an unknown kind of 2d plot was given

    Returns:
        tuple: a tuple of (f_list, kwargs_list, opts) for generating a holoviz plot
    """
    # if no aggregator is given, default to aggregated mean of w
    if aggregator is None:
        aggregator = ds.reductions.mean(kwargs["w"])

    if kind == "scatter":
        return scatter(chunk, aggregator, **kwargs)
    else:
        raise ValueError(f"Unknown 2d plot kind given: {kind}")


def scatter(chunk: DataFrame, aggregator: Reduction | None, **kwargs) -> tuple:
    """dispatches a scatter plot

    Args:
        chunk (DataFrame): the chunk of data to be plotted
        aggregator (Reduction | None): the aggregator function to use

    Returns:
        tuple: a tuple of (f_list, kwargs_list, opts) for generating a holoviz plot
    """
    kdims = [kwargs["x"], kwargs["y"]]
    w_col = kwargs.get("w", None)

    f_list = [hv.Points, hd.rasterize, hd.dynspread]
    kwargs_list = [
        {
            "kdims": kdims,
            "vdims": [w_col] + [x for x in chunk.columns if (x not in kdims) and (x != w_col)],
            "label": "2D Scatter",
        },
        {"aggregator": aggregator},
        {},
    ]

    opts = {
        "colorbar": kwargs.get("colorbar", True),
        "cmap": kwargs.get("cmap", "plasma"),
        "hooks": [hooks.scatter(w_col)],
    }

    return f_list, kwargs_list, opts


def distribution(chunk: DataFrame, aggregator: Reduction | None, **kwargs) -> tuple:
    """dispatches a distribution plot

    Args:
        chunk (DataFrame): the chunk of data to be plotted
        aggregator (Reduction | None): the aggregator function to use

    Returns:
        tuple: a tuple of (f_list, kwargs_list, opts) for generating a holoviz plot
    """
    [kwargs["x"]]

    f_list = [hv.Distribution]
    kwargs_list = []
    opts = {}

    return f_list, kwargs_list, opts
