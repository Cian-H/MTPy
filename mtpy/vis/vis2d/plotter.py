"""Data visualisation components of the MTPy module."""

from __future__ import annotations

from pathlib import Path
import tomllib
from typing import Any, Iterable, Optional, Tuple

# TEMPORARY FIX FOR WARNINGS
from datashader.reductions import Reduction
from holoviews.element.chart import Chart

from mtpy.utils.types import TOMLDict
from mtpy.vis.abstract import AbstractPlotter

from .dispatchers import DispatchParams, guarded_dispatchparams, plot_dispatch

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


class _PlotParams(DispatchParams):
    kind: str


def _guarded_plotparams(t: object) -> _PlotParams:
    if (
        isinstance(t, dict)
        and hasattr(t, "x")
        and isinstance(str, t["x"])
        and hasattr(t, "y")
        and isinstance(str, t["y"])
        and hasattr(t, "w")
        and isinstance(str, t["w"])
        and hasattr(t, "kind")
        and isinstance(str, t["kind"])
    ):
        return _PlotParams(x=t["x"], y=t["y"], w=t["w"], kind=t["kind"])
    msg = "Expected _PlotParams"
    raise TypeError(msg)


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
        filename: Optional[str] = None,
        *args: Any,
        kind: str,
        add_to_dashboard: bool = False,
        samples: Optional[int | Iterable[int]] = None,
        xrange: Tuple[Optional[float], Optional[float]] | Optional[float] = None,
        yrange: Tuple[Optional[float], Optional[float]] | Optional[float] = None,
        zrange: Tuple[Optional[float], Optional[float]] | Optional[float] = None,
        groupby: Optional[str | Iterable[str]] = None,
        aggregator: Optional[Reduction] = None,
        **kwargs: Any,
    ) -> Chart:
        """Creates a 2d plot.

        Args:
            filename (Optional[str], optional): file path to save plot to, if desired.
                Defaults to None.
            *args (Any): additional positional arguments to be passed to the plotting function
            kind (str): the kind of plot to produce
            add_to_dashboard (bool, optional): the dashboard to add the plot to, if
                desired Defaults to False.
            samples (Optional[int | Iterable[int]], optional): the samples to include on the plot.
                Defaults to None.
            xrange (Tuple[Optional[float], Optional[float]] | Optional[float], optional): the range
                of x values to plot. Defaults to None.
            yrange (Tuple[Optional[float], Optional[float]] | Optional[float], optional): the range
                of y values to plot. Defaults to None.
            zrange (Tuple[Optional[float], Optional[float]] | Optional[float], optional): the range
                of z values to plot. Defaults to None.
            groupby (Optional[str | Iterable[str]], optional): the groupby to apply to the dataframe
                before plotting. Defaults to None.
            aggregator (Optional[Reduction], optional): the aggregator to apply to the plot.
                Defaults to None.
            **kwargs (Any): additional keyword arguments to be passed to the plotting
                function

        Returns:
            Chart: a holoviz plot

        Raises:
            ValueError: If given `axis_range` is invalid for `axis`
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
            (_kwargs.get("x", "x"), _kwargs.get("y", "y"), _kwargs.get("z", "z")),
            (xrange, yrange, zrange),
            strict=False,
        ):
            from mtpy.utils.type_guards import is_float_pair_tuple

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
        view_id = self.generate_view_id(
            kind, samples, guarded_str_key_dict(_kwargs), xrange, yrange, zrange, groupby
        )

        func_list, kwargs_list, opts = plot_dispatch(kind, chunk, aggregator, **_kwargs)

        plot = chunk
        for func, plot_kwargs in zip(func_list, kwargs_list, strict=False):
            plot = func(plot, **plot_kwargs)
        plot = plot.opts(**opts)

        self.views[view_id] = plot

        import holoviews as hv

        hv.extension("plotly")

        # If filename is given, save to that file
        if filename is not None:
            self.logger.info(f"Saving to {filename}...")
            hv.save(plot, filename)
            self.logger.info(f"{filename} saved!")

        # # If adding to dashboard, add this plot to the dashboard
        # if add_to_dashboard and self.dashboard:
        #     self.add_to_dashboard(plot)

        # Finally, return the plot for viewing, e.g. in jupyter notebook
        return plot

    def scatter2d(self: "Plotter", *args: Any, **kwargs: TOMLDict) -> Chart:
        """Creates a 2d scatter plot.

        Args:
            *args (Any): The arguments to be passed to the plotting library's 2d scatter function.
            **kwargs (TOMLDict): The keyword arguments to be passed to the plotting library's
                2d scatter function.

        Returns:
            Chart: a holoviz plot
        """
        from mtpy.utils.type_guards import guarded_tomldict

        plot_kwargs = guarded_tomldict(self.config["scatter2d"]).copy()
        plot_kwargs.update(kwargs)
        return self.plot(*args, **_guarded_plotparams(plot_kwargs))

    def distribution2d(self: "Plotter", *args: Any, **kwargs: TOMLDict) -> Chart:
        """Creates a 2d distribution plot.

        Args:
            *args (Any): The arguments to be passed to the plotting library's 2d distribution
                function.
            **kwargs (TOMLDict): The keyword arguments to be passed to the plotting library's
                2d distribution function.

        Returns:
            Chart: a holoviz plot
        """
        from mtpy.utils.type_guards import guarded_tomldict

        plot_kwargs = guarded_tomldict(self.config["distribution2d"]).copy()
        plot_kwargs.update(kwargs)
        return self.plot(*args, **_guarded_plotparams(plot_kwargs))
