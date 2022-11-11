from . import hooks3d as hooks

from dask.dataframe import DataFrame
from datashader.reductions import Reduction
import datashader as ds
import holoviews as hv
import holoviews.operation.datashader as hd


def plot_dispatch(kind: str, chunk: DataFrame, aggregator: Reduction | None, **kwargs) -> tuple:
    # if no aggregator is given, default to aggregated mean of w
    if aggregator is None:
        aggregator = ds.reductions.mean(kwargs["w"])
    
    if kind == "scatter":
        return scatter(chunk, aggregator, **kwargs)
    else:
        raise ValueError(f"Unknown 2d plot kind given: {kind}")


def scatter(chunk: DataFrame, aggregator: Reduction | None, **kwargs) -> tuple:
    kdims = [kwargs["x"], kwargs["y"]]
    w_col = kwargs.get("w", None)

    f_list = [hv.Points, hd.rasterize, hd.dynspread]
    kwargs_list = [
        {
            "kdims": kdims,
            "vdims": [w_col] + [x for x in chunk.columns if (x not in kdims) and (x != w_col)],
            "label": "2D Scatter"
        },
        {
            "aggregator": aggregator
        },
        {}
    ]
    
    opts = {
        "colorbar": kwargs.get("colorbar", True),
        "cmap": kwargs.get("cmap", "plasma"),
        "hooks": [hooks.scatter(w_col)]
    }
    
    return f_list, kwargs_list, opts


def distribution(chunk: DataFrame, aggregator: Reduction | None, **kwargs) -> tuple:
    kdims = [kwargs["x"]]

    f_list = [hv.Distribution]
    kwargs_list = []
    opts = {}
    
    return f_list, kwargs_list, opts
