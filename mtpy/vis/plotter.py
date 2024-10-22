"""Data visualisation components of the MTPy module."""

from typing import Any, Dict, Iterable, Optional, Tuple

from datashader.reductions import Reduction
import holoviews as hv
from holoviews.element.chart import Chart

from mtpy.loaders.dummy import DummyLoader
from mtpy.loaders.protocol import LoaderProtocol
from mtpy.vis.abstract import AbstractPlotter
from mtpy.vis.protocol import PlotterProtocol
from mtpy.vis.vis2d.plotter import Plotter as Plotter2D
from mtpy.vis.vis3d.plotter import Plotter as Plotter3D

hv.extension("plotly")


class CombinedPlotter(AbstractPlotter):
    """This class is a factory that combines multiple plotters in a single class.

    Args:
        plotters (Dict[str, PlotterProtocol]): A dict of mapping labels to subplotters.
            The keys (labels) are labels that will be prepended when directing a call
            at a specific plotter.
    """

    def __init__(self: "CombinedPlotter", plotters: Dict[str, PlotterProtocol]) -> None:
        super().__init__(DummyLoader())
        self.plotters = plotters

    def plot(
        self: "CombinedPlotter",
        filename: Optional[str] = None,
        *args,
        kind: str,
        add_to_dashboard: bool = False,
        samples: Optional[int | Iterable[int]] = None,
        xrange: Tuple[Optional[float], Optional[float]] | Optional[float] = None,
        yrange: Tuple[Optional[float], Optional[float]] | Optional[float] = None,
        zrange: Tuple[Optional[float], Optional[float]] | Optional[float] = None,
        groupby: Optional[str | Iterable[str]] = None,
        aggregator: Optional[Reduction] = None,
        **kwargs,
    ) -> Chart:
        """Creates a plot.

        This method creates a plot using one of the subplotters. Will execute plot
            function for first subplotter for which the kind is valid. If this
            behaviour is undesirable subplotters can be targetted using the `kind`
            string via the syntax: "{subplotter_label}-{kind}".

        Args:
            filename (Optional[str], optional): file path to save plot to, if desired.
                Defaults to None.
            *args: additional positional arguments to be passed to the plotting function
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
            **kwargs: additional keyword arguments to be passed to the plotting function

        Returns:
            Chart: a holoviz plot

        Raises:
            ValueError: If combination of subplotter and kind cannot be resolved successfully
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

    def __getattr__(self: "CombinedPlotter", attr: str) -> Any:  # noqa: ANN401
        """Fallback method that retrieves attributes from subplotters.

        Retrieves attributes from subplotters if they are not present in the
            CombinedPlotter instance. Resolves attributes in the order they
            appear in the provided `self.plotters`.

        Args:
            attr (str): The attribute to be fetched

        Returns:
            Any: Returns the object at the attribute provided if resolvable

        Raises:
            AttributeError: If attribute is not found and unable to be successfully
                resolved
        """
        for obj in self.plotters.values():
            if hasattr(obj, attr):
                return getattr(obj, attr)
        msg = f"{self.__class__.__name__!r} object has no attribute {attr!r}"
        raise AttributeError(msg)


class Plotter(CombinedPlotter):
    """A CombinedPlotter combining the `Plotter2D` and `Plotter3D` classes.

    Args:
        loader (LoaderProtocol): The loader providing the data to the plotter
    """

    def __init__(self: "Plotter", loader: LoaderProtocol) -> None:
        from mtpy.utils.type_guards import guarded_plotter_protocol

        plotters: Dict[str, PlotterProtocol] = {
            "2d": guarded_plotter_protocol(Plotter2D(loader)),
            "3d": guarded_plotter_protocol(Plotter3D(loader)),
        }

        super().__init__(plotters)
