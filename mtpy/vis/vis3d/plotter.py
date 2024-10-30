"""Data visualisation components of the MTPy module."""

from __future__ import annotations

from pathlib import Path
import tomllib
from typing import Any, Iterable, Optional, Tuple

from datashader.reductions import Reduction
import holoviews as hv
from holoviews.element.chart import Chart

from mtpy.utils.types import TOMLDict
from mtpy.vis.abstract import AbstractPlotter

from .dispatchers import DispatchParams, guarded_dispatchparams, plot_dispatch

hv.extension("plotly")


class _PlotParams(DispatchParams):
    kind: str


def _guarded_plotparams(t: object) -> _PlotParams:
    if (
        isinstance(t, dict)
        and hasattr(t, "x")
        and isinstance(str, t["x"])
        and hasattr(t, "y")
        and isinstance(str, t["y"])
        and hasattr(t, "z")
        and isinstance(str, t["z"])
        and hasattr(t, "w")
        and isinstance(str, t["w"])
        and hasattr(t, "kind")
        and isinstance(str, t["kind"])
    ):
        return _PlotParams(x=t["x"], y=t["y"], z=t["z"], w=t["w"], kind=t["kind"])
    msg = "Expected _PlotParams"
    raise TypeError(msg)


class Plotter(AbstractPlotter):
    """a 3d plotter class."""

    def plot(
        self: "Plotter",
        filename: Optional[str] = None,
        *args: Any,
        kind: str,
        add_to_dashboard: bool = False,
        samples: Optional[int | Iterable[int]] = None,
        xrange: Optional[Tuple[Optional[float], Optional[float]]] = None,
        yrange: Optional[Tuple[Optional[float], Optional[float]]] = None,
        zrange: Optional[Tuple[Optional[float], Optional[float]]] = None,
        groupby: Optional[str | Iterable[str]] = None,
        aggregator: Optional[Reduction] = None,
        **kwargs: Any,
    ) -> Chart:
        """Creates a 3d plot.

        Args:
            filename (Optional[str], optional): file path to save plot to, if desired.
                Defaults to None.
            *args (Any): additional arguments to be passed to the plotting function for the given
                kind
            kind (str): the kind of plot to produce
            add_to_dashboard (bool, optional): the dashboard to add the plot to, if
                desired Defaults to False.
            samples (Optional[int | Iterable[int]], optional): the samples to include on the
                plot. Defaults to None.
            xrange (Optional[Tuple[Optional[float], Optional[float]]], optional): the range
                of x values to plot. Defaults to None.
            yrange (Optional[Tuple[Optional[float], Optional[float]]], optional): the range
                of y values to plot. Defaults to None.
            zrange (Optional[Tuple[Optional[float], Optional[float]]], optional): the range
                of z values to plot. Defaults to None.
            groupby (Optional[str | Iterable[str]], optional): the groupby to apply to the
                dataframe before plotting. Defaults to None.
            aggregator (Optional[Reduction], optional): the aggregator to apply to the plot.
                Defaults to None.
            **kwargs (Any): additional keyword arguments to be passed to the plotting function for
                the given kind

        Returns:
            Chart: a holoviz plot
        """
        from mtpy.utils.type_guards import guarded_str_key_dict, guarded_tomldict

        config_path = "plotter.toml"
        with Path(f"{Path(__file__).parents[0].resolve()}/{config_path}").open("rb") as f:
            self.config = guarded_tomldict(tomllib.load(f))

        _kwargs = guarded_dispatchparams(kwargs)

        chunk = self.loader.data

        # Filter to relevant samples
        if "sample" in chunk:
            if isinstance(samples, int):
                chunk = chunk.loc[chunk["sample"].eq(samples)]
            elif isinstance(samples, Iterable):
                chunk = chunk.loc[chunk["sample"].isin(samples)]

        # filter dataframe based on ranges given
        for axis, axis_range in zip(
            (_kwargs["x"], _kwargs["y"], _kwargs["z"]), (xrange, yrange, zrange), strict=False
        ):
            if axis_range is None:
                continue
            axis_min, axis_max = axis_range
            chunk = chunk.loc[chunk[axis].ge(axis_min)] if axis_min is not None else chunk
            chunk = chunk.loc[chunk[axis].le(axis_max)] if axis_max is not None else chunk

        # Then group if groupby is present (NOTE: NOT TESTED YET!)
        chunk = chunk.groupby(groupby) if groupby is not None else chunk

        # generate a view id string for caching views
        view_id = self.generate_view_id(
            kind, samples, guarded_str_key_dict(_kwargs), xrange, yrange, zrange, groupby
        )

        func_list, kwargs_list, opts = plot_dispatch(kind, chunk, aggregator, **kwargs)

        plot = chunk
        for func, plot_kwargs in zip(func_list, kwargs_list, strict=False):
            plot = func(plot if plot in locals() else chunk, **plot_kwargs)
        plot = plot.opts(**opts)

        self.views[view_id] = plot

        # If filename is given, save to that file
        if filename is not None:
            self.logger.info(f"Saving to {filename}...")
            hv.save(plot, filename)
            self.logger.info(f"{filename} saved!")

        # The code below is currently part of a planned feature to add plots to a dashboard
        # # If adding to dashboard, add this plot to the dashboard
        # if add_to_dashboard and hasattr(self, "dashboard") :
        #     self.add_to_dashboard(plot)

        # Finally, return the plot for viewing, e.g. in jupyter notebook
        return plot

    def scatter3d(self: "Plotter", *args: Any, **kwargs: TOMLDict) -> Chart:
        """Creates a 3d scatter plot.

        Args:
            *args (Any): The arguments to be passed to the plotting library's 3d scatter function.
            **kwargs (TOMLDict): The keyword arguments to be passed to the plotting library's 3d
                scatter function.

        Returns:
            Chart: a holoviz plot
        """
        from mtpy.utils.type_guards import guarded_tomldict

        plot_kwargs = guarded_tomldict(self.config["scatter3d"]).copy()
        plot_kwargs.update(kwargs)
        return self.plot(*args, **_guarded_plotparams(plot_kwargs))
