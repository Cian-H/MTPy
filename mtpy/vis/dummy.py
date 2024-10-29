"""This module defines a protocol for a valid MTPy Plotter class."""

from typing import Any, Iterable, Optional, Tuple

from datashader.reductions import Reduction
from holoviews.element.chart import Chart

from mtpy.loaders.dummy import DummyLoader


class DummyPlotter:
    """A dummy loader for tests and composing classes that do not plot anything."""

    def __init__(self: "DummyPlotter") -> None:
        self.loader = DummyLoader()

    def plot(
        self: "DummyPlotter",
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
        """Creates a plot.

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
            **kwargs (Any): additional keyword arguments to be passed to the plotting function

        Returns:
            Chart: a holoviz plot
        """
        return Chart(None)

    def generate_view_id(
        self: "DummyPlotter",
        kind: str,
        samples: Optional[int | Iterable[int]] = None,
        kwargs: Optional[dict[str, object]] = None,
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
            kwargs (Optional[dict[str, object]], optional): The kwargs for hte plotting function.
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
