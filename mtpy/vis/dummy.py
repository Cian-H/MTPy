"""This module defines a protocol for a valid MTPy Plotter class."""

from typing import Iterable, Optional, Tuple

from datashader.reductions import Reduction
from holoviews.element.chart import Chart

from mtpy.loaders.dummy import DummyLoader


class DummyPlotter:
    """A dummy loader for tests and composing classes that do not plot anything.

    Attributes:
        loader (DummyLoader): The loader providing the data to the Plotter object
    """

    def __init__(self: "DummyPlotter") -> None:
        """Initialises a dummy plotter object."""
        self.loader = DummyLoader()

    def plot(
        self: "DummyPlotter",
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

        Args:
            kind (str): the kind of plot to produce
            filename (Optional[str], optional): file path to save plot to, if desired.
                Defaults to None.
            add_to_dashboard (bool, optional): the dashboard to add the plot to, if
                desired Defaults to False.
            *args: additional positional arguments to be passed to the plotting function
            samples (Optional[int | Iterable[int]], optional): the samples to include on the plot.
                Defaults to None.
            xrange (Tuple[Optional[float], Optional[float]] | Optional[float]): the range of
                x values to plot. Defaults to None.
            yrange (Tuple[Optional[float], Optional[float]] | Optional[float]): the range of
                y values to plot. Defaults to None.
            zrange (Tuple[Optional[float], Optional[float]] | Optional[float]): the range of
                z values to plot. Defaults to None.
            groupby (Optional[str | list[str]], optional): the groupby to apply to the dataframe
                before plotting. Defaults to None.
            aggregator (Optional[Reduction], optional): the aggregator to apply to the plot.
                Defaults to None.
            **kwargs: additional keyword arguments to be passed to the plotting function

        Returns:
            Chart: a holoviz plot
        """
        return Chart(None)

    def generate_view_id(
        self: "DummyPlotter",
        kind: str,
        samples: Optional[int | Iterable[int]] = None,
        kwargs: Optional[dict] = None,
        xrange: Tuple[Optional[float], Optional[float]] | Optional[float] = None,
        yrange: Tuple[Optional[float], Optional[float]] | Optional[float] = None,
        zrange: Tuple[Optional[float], Optional[float]] | Optional[float] = None,
        groupby: Optional[str | Iterable[str]] = None,
    ) -> str:
        """Generates a view id string for caching views.

        Args:
            kind (str): the kind of plot to produce
            samples (Optional[int | Iterable[int]], optional): The samples in the view.
                Defaults to None.
            kwargs (Optional[dict], optional): The kwargs for hte plotting function.
                Defaults to None.
            xrange (Tuple[Optional[float], Optional[float]] | Optional[float], optional): The range
                of x values to be plotted. Defaults to None.
            yrange (Tuple[Optional[float], Optional[float]] | Optional[float], optional): The range
                of y values to be plotted. Defaults to None.
            zrange (Tuple[Optional[float], Optional[float]] | Optional[float], optional): The range
                of z values to be plotted. Defaults to None.
            groupby (Optional[str | Iterable[str]], optional): the aggregator to apply to the plot.
                Defaults to None.

        Returns:
            str: The view ID.
        """
        return ""
