from __future__ import annotations

from typing import Iterable
from pathlib import Path
import json

import holoviews as hv
from datashader.reductions import Reduction

from .plotter_base import PlotterBase, pn
from .dispatchers2d import plot_dispatch
from ..utils.apply_defaults import apply_defaults

# TEMPORARY FIX FOR WARNINGS
import warnings
warnings.filterwarnings("ignore")
warnings.filterwarnings("ignore", module="bokeh")

# NOTES: Matplotlib and plotly clearly arent up to the job alone here.
#   Implement holoviews + datashading
# to give interactive, dynamically updating plots
# Added bonus: holoviews also makes possible to create interactive dashboards from plots
# See:
#   - https://holoviews.org/user_guide/Large_Data.html and ../mtpy_test/MTPy_Test.ipynb
#   - https://medium.com/plotly/introducing-dash-holoviews-6a05c088ebe5

# TODO: replace dash with holoviz panels
#   - https://panel.holoviz.org/index.html
# NOTE: panels added but itneractivesloders are currently creating an error.
#   Need to diagnose this later
#   - for possible solution see: https://panel.holoviz.org/gallery/simple/save_filtered_df.html

# Currently implemented plot kinds:
#   - scatter
#   - distribution

hv.extension("plotly")

config_path = "config/plotter2d.json"
with open(Path(f"{Path(__file__).parents[0].resolve()}/{config_path}"), "r") as f:
    config = json.load(f)


class Plotter2D(PlotterBase):
    """The 2D plotter class"""

    def __init__(self, **kwargs):
        """initialize the Plotter2D class"""
        super().__init__(**kwargs)

    def init_panel(self, *args, **kwargs):
        """initialize the panel widgets"""
        super().init_panel(*args, **kwargs)
        # Bind 2d plotting functions to the panel
        self.scatter2d_panel = pn.bind(
            self.scatter2d,
            xrange=(self.xmin_slider, self.xmax_slider),
            yrange=(self.ymin_slider, self.ymax_slider),
            zrange=(self.zmin_slider, self.zmax_slider),
            samples=self.sample_slider,
        )
        self.layer_scatter2d_panel = pn.bind(
            self.scatter2d,
            xrange=(self.xmin_slider, self.xmax_slider),
            yrange=(self.ymin_slider, self.ymax_slider),
            zrange=self.layer_slider,
            samples=self.sample_slider,
        )
        self.distribution2d_panel = pn.bind(
            self.distribution2d,
            xrange=(self.xmin_slider, self.xmax_slider),
            yrange=(self.ymin_slider, self.ymax_slider),
            zrange=self.layer_slider,
            samples=self.sample_slider,
        )

    def plot2d(
        self,
        kind: str,
        filename: None | str = None,
        add_to_dashboard: bool = False,
        samples: int | Iterable | None = None,
        xrange: tuple[float | None, float | None] | float | None = None,
        yrange: tuple[float | None, float | None] | float | None = None,
        zrange: tuple[float | None, float | None] | float | None = None,
        groupby: str | list[str] | None = None,
        aggregator: Reduction | None = None,
        *args,
        **kwargs,
    ):
        """creates a 2d plot

        Args:
            kind (str): the kind of plot to produce
            filename (None | str, optional): file path to save plot to, if desired.
                Defaults to None.
            add_to_dashboard (bool, optional): the dashboard to add the plot to, if
                desired Defaults to False.
            samples (int | Iterable | None, optional): the samples to include on the plot.
                Defaults to None.
            xrange (tuple[float  |  None, float  |  None] | float | None, optional): the range of x
                values to plot. Defaults to None.
            yrange (tuple[float  |  None, float  |  None] | float | None, optional): the range of y
                values to plot. Defaults to None.
            zrange (tuple[float  |  None, float  |  None] | float | None, optional): the range of z
                values to plot. Defaults to None.
            groupby (str | list[str] | None, optional): the groupby to apply to the dataframe
                before plotting. Defaults to None.
            aggregator (Reduction | None, optional): the aggregator to apply to the plot.
                Defaults to None.

        Returns:
            Plot: a holoviz plot
        """
        chunk = self.data

        # Filter to relevant samples
        if "sample" in chunk:
            if isinstance(samples, int):
                chunk = chunk.loc[chunk["sample"].eq(samples)]
            elif isinstance(samples, Iterable):
                chunk = chunk.loc[chunk["sample"].isin(samples)]

        # filter dataframe based on ranges given
        for axis, axis_range in zip(
            (kwargs.get("x"), kwargs.get("y"), kwargs.get("z")), (xrange, yrange, zrange)
        ):
            if axis_range is None:
                continue
            elif type(axis_range) is float:
                chunk = chunk.loc[chunk[axis].eq(float(axis_range))]
            else:
                axis_min, axis_max = axis_range
                if axis_min is not None:
                    chunk = chunk.loc[chunk[axis].ge(float(axis_min))]
                elif axis_max is not None:
                    chunk = chunk.loc[chunk[axis].le(float(axis_max))]

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
        view_id += f"_{kwargs.get('y', '')}"
        if yrange is not None:
            view_id += f"{str(yrange)}"
        view_id += f"_{kwargs.get('w', '')}"
        view_id += f"_{kwargs.get('z', '')}"
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

        # # If adding to dashboard, add this plot to the dashboard
        # if add_to_dashboard and self.dashboard:
        #     self.add_to_dashboard(plot)

        # Finally, return the plot for viewing, e.g. in jupyter notebook
        return plot

    def scatter2d(self, *args, **kwargs):
        """creates a 2d scatter plot

        Returns:
            Plot: a holoviz plot
        """
        return self.plot2d(*args, **apply_defaults(kwargs, config["scatter2d"]))

    def distribution2d(self, *args, **kwargs):
        """creates a 2d distribution plot

        Returns:
            Plot: a holoviz plot
        """
        return self.plot2d(*args, **apply_defaults(kwargs, config["distribution2d"]))
