# -*- coding: utf-8 -*-

"""Data visualisation components of the MTPy module."""

from typing import Any, Dict, Iterable, Optional, Tuple

from datashader.reductions import Reduction
import holoviews as hv
from holoviews.element.chart import Chart

from mtpy.loaders.dummy import DummyLoader
from mtpy.loaders.protocol import LoaderProtocol

from .abstract import AbstractPlotter
from .protocol import PlotterProtocol
from .vis2d.plotter import Plotter as Plotter2D
from .vis3d.plotter import Plotter as Plotter3D

hv.extension("plotly")


class CombinedPlotter(AbstractPlotter):
    """This class combines other plotters to create a plotter that combines the
    functions of both.
    """

    def __init__(self: "CombinedPlotter", plotters: Dict[str, PlotterProtocol]) -> None:
        """Initialises CombinedPlotter object.

        Args:
            plotters (Dict[str, PlotterProtocol]): A dict of plotters to combine
            where the keys are labels to prepend for each plotter.
        """
        super().__init__(DummyLoader())
        self.plotters = plotters

    def plot(
        self: "CombinedPlotter",
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
        """Creates a plot. Will execute plot function for first subplotter fpr which
        the kind is valid. Subplotters can be targetted using the `kind` string
        syntax: \"{subplotter_label}-{kind}\".

        Args:
            kind (str): the kind of plot to produce
            filename (Optional[str], optional): file path to save plot to, if desired.
                Defaults to None.
            add_to_dashboard (bool, optional): the dashboard to add the plot to, if
                desired Defaults to False.
            *args: additional positional arguments to be passed to the plotting function
            samples (int | Iterable | None, optional): the samples to include on the plot.
                Defaults to None.
            xrange (tuple[float  |  None, float  |  None] | Optional[float], optional): the range of
                x values to plot. Defaults to None.
            yrange (tuple[float  |  None, float  |  None] | Optional[float], optional): the range of
                y values to plot. Defaults to None.
            zrange (tuple[float  |  None, float  |  None] | Optional[float], optional): the range of
                z values to plot. Defaults to None.
            groupby (str | list[str] | None, optional): the groupby to apply to the dataframe
                before plotting. Defaults to None.
            aggregator (Optional[Reduction], optional): the aggregator to apply to the plot.
                Defaults to None.
            **kwargs: additional keyword arguments to be passed to the plotting function

        Returns:
            Chart: a holoviz plot
        """
        if "-" in kind:
            plotter_label, plot_kind = kind.split("-")
            return self.plotters[plotter_label].plot(
                plot_kind,
                filename,
                add_to_dashboard,
                *args,
                samples,
                xrange,
                yrange,
                zrange,
                groupby,
                aggregator,
                **kwargs,
            )
        for plotter in self.plotters.values():
            try:
                return plotter.plot(
                    plot_kind,
                    filename,
                    add_to_dashboard,
                    *args,
                    samples,
                    xrange,
                    yrange,
                    zrange,
                    groupby,
                    aggregator,
                    **kwargs,
                )
            except ValueError:
                continue
        msg = "Plot kind is not valid in any subplotters"
        raise ValueError(msg)

    def __getattr__(self: "CombinedPlotter", attr: str) -> Any: # noqa: ANN401
        for obj in self.plotters.values():
            if hasattr(obj, attr):
                return getattr(obj, attr)
        return AttributeError(f"{self.__class__.__name__!r} object has no attribute {attr!r}")


class Plotter(CombinedPlotter):
    def __init__(self: "Plotter", loader: LoaderProtocol) -> None:
        super().__init__(
            {
                "2d": Plotter2D(loader),
                "3d": Plotter3D(loader),
            }
        )
