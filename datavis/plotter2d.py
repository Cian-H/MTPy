from itertools import chain
from typing import Iterable
from pathlib import Path
import json

from dash.dash import Dash
import dask
import holoviews as hv
from holoviews import opts
import holoviews.operation.datashader as hd
import datashader as ds
from datashader.reductions import Reduction

from .plotter_base import PlotterBase
from .dispatchers2d import plot_dispatch
from ..utils.apply_defaults import apply_defaults

# NOTES: Matplotlib and plotly clearly arent up to the job alone here. Implement holoviews + datashading
# to give interactive, dynamically updating plots
# Added bonus: holoviews also makes possible to create interactive dashboards from plots
# See:
#   - https://holoviews.org/user_guide/Large_Data.html and ../mtpy_test/MTPy_Test.ipynb
#   - https://medium.com/plotly/introducing-dash-holoviews-6a05c088ebe5

# TODO: replace dash with holoviz panels
#   - https://panel.holoviz.org/index.html

# Currently implemented plot kinds:
#   - scatter

hv.extension("plotly")

config_path = "config/plotter2d.json"
with open(Path(f"{Path(__file__).parents[0].resolve()}/{config_path}"), "r") as f:
    config = json.load(f)


class Plotter2D(PlotterBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def plot2d(
        self,
        kind: str,
        filename: None | str = None,
        add_to_dashboard: bool = False,
        samples: int | Iterable | None = None,
        xrange: tuple[float | None, float | None] | None = None,
        yrange: tuple[float | None, float | None] | None = None,
        zrange: tuple[float | None, float | None] | None = None,
        groupby: str | list[str] | None = None,
        aggregator: Reduction | None = None,
        *args,
        **kwargs,
    ):
        chunk = self.data

        # Filter to relevant samples
        if "sample" in chunk:
            if isinstance(samples, int):
                chunk = chunk.loc[chunk["sample"].eq(samples)]
            elif isinstance(samples, Iterable):
                chunk = chunk.loc[chunk["sample"].isin(samples)]

        # If z is given for range values, peel off from kwargs
        if "z" in kwargs:
            z_col = kwargs["z"]
            del kwargs["z"]
        else:
            z_col = None

        # filter dataframe based on ranges given
        for axis, axis_range in zip(
            (kwargs["x"], kwargs["y"], z_col), (xrange, yrange, zrange)
        ):
            if axis_range is None:
                continue
            else:
                axis_min, axis_max = axis_range
                if axis_min is not None:
                    chunk = chunk.loc[chunk[axis].ge(axis_min)]
                elif axis_max is not None:
                    chunk = chunk.loc[chunk[axis].le(axis_max)]

        # Then group if groupby is present (NOTE: NOT TESTED YET!)
        if groupby is not None:
            chunk = chunk.groupby(groupby)

        # generate a view id string for caching views
        view_id = f"plot2D_{kind}"

        if samples is not None:
            view_id += f"_s{str(samples)}"
        view_id += f"_{kwargs['x']}"
        if xrange is not None:
            view_id += f"{str(xrange)}"
        view_id += f"_{kwargs['y']}"
        if yrange is not None:
            view_id += f"{str(yrange)}"
        view_id += f"_{kwargs['w']}"
        if zrange is not None:
            view_id += f"{str(zrange)}"
        if groupby is not None:
            view_id += f"_g{str(groupby)}"
        
        f_list, kwargs_list, opts = plot_dispatch(kind, chunk, aggregator, **kwargs)

        plot = chunk
        for f, kwargs in zip(f_list, kwargs_list):
            plot = f(plot, **kwargs)
        plot = plot.opts(**opts)

        self.views[view_id] = plot

        # If filename is given, save to that file
        if filename is not None:
            self._qprint(f"Saving to {filename}...")
            hv.save(plot, filename)
            self._qprint(f"{filename} saved!")
        
        # If adding to dashboard, add this plot to the dashboard
        if add_to_dashboard and self.dashboard:
            self.add_to_dashboard(plot)
        
        # Finally, return the plot for viewing, e.g. in jupyter notebook
        return plot

    def scatter2d(self, *args, **kwargs):
        return self.plot2d(*args, **apply_defaults(kwargs, config["scatter2d"]))
