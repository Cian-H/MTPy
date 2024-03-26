# -*- coding: utf-8 -*-

"""Data visualisation components of the MTPy module."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Optional, Tuple

# TEMPORARY FIX FOR WARNINGS
import warnings

from datashader.reductions import Reduction
import holoviews as hv
from holoviews.element.chart import Chart

from mtpy.utils.type_guards import is_float_pair_tuple
from mtpy.vis.abstract import AbstractPlotter

from .dispatchers import plot_dispatch

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

config_path = "plotter.json"
with Path(f"{Path(__file__).parents[0].resolve()}/{config_path}").open("r") as f:
    config = json.load(f)


class Plotter(AbstractPlotter):
    """The 2D plotter class."""

    # # Similar to base: commented out because for now its unneeded and only causing headaches
    # def init_panel(self, *args, **kwargs):
    #     """initialize the panel widgets"""
    #     super().init_panel(*args, **kwargs)
    #     # Bind 2d plotting functions to the panel
    #     self.scatter2d_panel = pn.bind(
    #         self.scatter2d,
    #         xrange=(self.xmin_slider, self.xmax_slider),
    #         yrange=(self.ymin_slider, self.ymax_slider),
    #         zrange=(self.zmin_slider, self.zmax_slider),
    #         samples=self.sample_slider,
    #     )
    #     self.layer_scatter2d_panel = pn.bind(
    #         self.scatter2d,
    #         xrange=(self.xmin_slider, self.xmax_slider),
    #         yrange=(self.ymin_slider, self.ymax_slider),
    #         zrange=self.layer_slider,
    #         samples=self.sample_slider,
    #     )
    #     self.distribution2d_panel = pn.bind(
    #         self.distribution2d,
    #         xrange=(self.xmin_slider, self.xmax_slider),
    #         yrange=(self.ymin_slider, self.ymax_slider),
    #         zrange=self.layer_slider,
    #         samples=self.sample_slider,
    #     )

    def plot(
        self: "Plotter",
        kind: str,
        filename: Optional[str] = None,
        *args,
        add_to_dashboard: bool = False,
        samples: Optional[int | Iterable[int]] = None,
        xrange: Tuple[Optional[float], Optional[float]] | Optional[float] = None,
        yrange: Tuple[Optional[float], Optional[float]] | Optional[float] = None,
        zrange: Tuple[Optional[float], Optional[float]] | Optional[float] = None,
        groupby: Optional[str | Iterable[str]] = None,
        aggregator: Optional[Reduction] = None,
        **kwargs,
    ) -> Chart:
        """Creates a 2d plot.

        Args:
            kind (str): the kind of plot to produce
            filename (Optional[str], optional): file path to save plot to, if desired.
                Defaults to None.
            add_to_dashboard (bool, optional): the dashboard to add the plot to, if
                desired Defaults to False.
            *args: additional positional arguments to be passed to the plotting function
            samples (Optional[int | Iterable], optional): the samples to include on the plot.
                Defaults to None.
            xrange (Tuple[Optional[float], Optional[float]] | Optional[float], optional): the range
                of x values to plot. Defaults to None.
            yrange (Tuple[Optional[float], Optional[float]] | Optional[float], optional): the range
                of y values to plot. Defaults to None.
            zrange (Tuple[Optional[float], Optional[float]] | Optional[float], optional): the range
                of z values to plot. Defaults to None.
            groupby (Optional[str | list[str]], optional): the groupby to apply to the dataframe
                before plotting. Defaults to None.
            aggregator (Optional[Reduction], optional): the aggregator to apply to the plot.
                Defaults to None.
            **kwargs: additional keyword arguments to be passed to the plotting function

        Returns:
            Chart: a holoviz plot
        """
        chunk = self.loader.data

        # Filter to relevant samples
        if "sample" in chunk:
            if isinstance(samples, int):
                chunk = chunk.loc[chunk["sample"].eq(samples)]
            elif isinstance(samples, Iterable):
                chunk = chunk.loc[chunk["sample"].isin(samples)]

        # filter dataframe based on ranges given
        for axis, axis_range in zip(
            (kwargs.get("x", "x"), kwargs.get("y", "y"), kwargs.get("z", "z")),
            (xrange, yrange, zrange),
            strict=False,
        ):
            if axis_range is None:
                continue
            if isinstance(axis_range, float):
                chunk = chunk.loc[chunk[axis].eq(float(axis_range))]
            elif is_float_pair_tuple(axis_range):
                axis_min, axis_max = axis_range
                chunk = (
                    chunk.loc[chunk[axis].ge(float(axis_min))] if axis_min is not None else chunk
                )
                chunk = (
                    chunk.loc[chunk[axis].le(float(axis_max))] if axis_max is not None else chunk
                )
            else:
                msg = f"Invalid range for {axis}: {axis_range}"
                raise ValueError(msg)

        # Then group if groupby is present (NOTE: NOT TESTED YET!)
        chunk = chunk.groupby(groupby) if groupby is not None else chunk

        # generate a view id string for caching views
        view_id = self.generate_view_id(kind, samples, kwargs, xrange, yrange, zrange, groupby)

        f_list, kwargs_list, opts = plot_dispatch(kind, chunk, aggregator, **kwargs)

        plot = chunk
        for f, plot_kwargs in zip(f_list, kwargs_list, strict=False):
            plot = f(plot, **plot_kwargs)
        plot = plot.opts(**opts)

        self.views[view_id] = plot

        # If filename is given, save to that file
        if filename is not None:
            print(f"Saving to {filename}...")
            hv.save(plot, filename)
            print(f"{filename} saved!")

        # # If adding to dashboard, add this plot to the dashboard
        # if add_to_dashboard and self.dashboard:
        #     self.add_to_dashboard(plot)

        # Finally, return the plot for viewing, e.g. in jupyter notebook
        return plot

    def scatter2d(self: "Plotter", *args, **kwargs) -> Chart:
        """Creates a 2d scatter plot.

        Returns:
            Chart: a holoviz plot
        """
        plot_kwargs = config["scatter2d"].copy()
        plot_kwargs.update(kwargs)
        return self.plot(*args, **plot_kwargs)

    def distribution2d(self: "Plotter", *args, **kwargs) -> Chart:
        """Creates a 2d distribution plot.

        Returns:
            Chart: a holoviz plot
        """
        plot_kwargs = config["distribution2d"].copy()
        plot_kwargs.update(kwargs)
        return self.plot(*args, **plot_kwargs)
