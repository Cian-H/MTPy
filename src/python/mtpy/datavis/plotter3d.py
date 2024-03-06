# -*- coding: utf-8 -*-

"""Data visualisation components of the MTPy module."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Optional, Tuple, Union

from datashader.reductions import Reduction
import holoviews as hv
from holoviews.element.chart import Chart

from mtpy.utils.apply_defaults import apply_defaults

from .dispatchers3d import plot_dispatch
from .plotter_base import PlotterBase

hv.extension("plotly")

config_path = "config/plotter3d.json"
with Path(f"{Path(__file__).parents[0].resolve()}/{config_path}").open("r") as f:
    config = json.load(f)


class Plotter3D(PlotterBase):
    """a 3d plotter class."""

    def __init__(self: "Plotter3D", **kwargs) -> None:
        """Initialize the Plotter3D class.

        Args:
            self (Plotter3D): the Plotter3D object
            **kwargs: keyword arguments to be passed to the parent class initialiser
        """
        super().__init__(**kwargs)

    def plot3d(
        self: "Plotter3D",
        kind: str,
        filename: Optional[str] = None,
        *args,
        add_to_dashboard: bool = False,
        samples: Optional[Union[int, Iterable[int]]] = None,
        xrange: Tuple[Optional[float], Optional[float]] | None = None,
        yrange: Tuple[Optional[float], Optional[float]] | None = None,
        zrange: Tuple[Optional[float], Optional[float]] | None = None,
        groupby: Optional[Union[str, Iterable[str]]] = None,
        aggregator: Optional[Reduction] = None,
        **kwargs,
    ) -> Chart:
        """Creates a 3d plot.

        Args:
            kind (str): the kind of plot to produce
            filename (Optional[str], optional): file path to save plot to, if desired.
                Defaults to None.
            *args: additional arguments to be passed to the plotting function for the given kind
            add_to_dashboard (bool, optional): the dashboard to add the plot to, if
                desired Defaults to False.
            samples (Optional[Union[int, Iterable[int]]], optional): the samples to include on the
                plot. Defaults to None.
            xrange (tuple[float  |  None, float  |  None] | Optional[float], optional): the range of
                x values to plot. Defaults to None.
            yrange (tuple[float  |  None, float  |  None] | Optional[float], optional): the range of
                y values to plot. Defaults to None.
            zrange (tuple[float  |  None, float  |  None] | Optional[float], optional): the range of
                z values to plot. Defaults to None.
            groupby (Optional[Union[str, Iterable[str]]], optional): the groupby to apply to the
                dataframe before plotting. Defaults to None.
            aggregator (Optional[Reduction], optional): the aggregator to apply to the plot.
                Defaults to None.
            **kwargs: additional keyword arguments to be passed to the plotting function for the

        Returns:
            Chart: a holoviz plot
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
            (kwargs["x"], kwargs["y"], kwargs["z"]), (xrange, yrange, zrange), strict=False
        ):
            if axis_range is None:
                continue
            axis_min, axis_max = axis_range
            chunk = chunk.loc[chunk[axis].ge(axis_min)] if axis_min is not None else chunk
            chunk = chunk.loc[chunk[axis].le(axis_max)] if axis_max is not None else chunk

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
            self._qprint(f"Saving to {filename}...")
            hv.save(plot, filename)
            self._qprint(f"{filename} saved!")

        # The code below is currently part of a planned feature to add plots to a dashboard
        # # If adding to dashboard, add this plot to the dashboard
        # if add_to_dashboard and hasattr(self, "dashboard") :
        #     self.add_to_dashboard(plot)

        # Finally, return the plot for viewing, e.g. in jupyter notebook
        return plot

    def scatter3d(self: "Plotter3D", *args, **kwargs) -> Chart:
        """Creates a 3d scatter plot.

        Returns:
            Chart: a holoviz plot
        """
        return self.plot3d(*args, **apply_defaults(kwargs, config["scatter3d"]))
