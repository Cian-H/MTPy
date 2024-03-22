from typing import Iterable, Optional, Protocol, Tuple, Union

from datashader.reductions import Reduction
from holoviews.element.chart import Chart

from ..loaders.protocol import LoaderProtocol


class PlotterProtocol(Protocol):

    loader: LoaderProtocol

    def plot(
        self: "PlotterProtocol",
        kind: str,
        filename: Optional[str] = None,
        *args,
        add_to_dashboard: bool = False,
        samples: Optional[Union[int, Iterable[int]]] = None,
        xrange: Tuple[Optional[float], Optional[float]] | Optional[float] = None,
        yrange: Tuple[Optional[float], Optional[float]] | Optional[float] = None,
        zrange: Tuple[Optional[float], Optional[float]] | Optional[float] = None,
        groupby: Optional[Union[str, Iterable[str]]] = None,
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
        ...


    def generate_view_id(
        self: "PlotterProtocol",
        kind: str,
        samples: Optional[Union[int, Iterable[int]]] = None,
        kwargs: Optional[dict] = None,
        xrange: Tuple[Optional[float], Optional[float]] | Optional[float] = None,
        yrange: Tuple[Optional[float], Optional[float]] | Optional[float] = None,
        zrange: Tuple[Optional[float], Optional[float]] | Optional[float] = None,
        groupby: Optional[Union[str, Iterable[str]]] = None,
    ) -> str:
        """Generates a view id string for caching views.

        Args:
            kind (str): the kind of plot to produce
            samples (Optional[Union[int, Iterable[int]]], optional): The samples in the view.
                Defaults to None.
            kwargs (Optional[dict], optional): The kwargs for hte plotting function.
                Defaults to None.
            xrange (Tuple[Optional[float], Optional[float]] | Optional[float], optional): The range
                of x values to be plotted. Defaults to None.
            yrange (Tuple[Optional[float], Optional[float]] | Optional[float], optional): The range
                of y values to be plotted. Defaults to None.
            zrange (Tuple[Optional[float], Optional[float]] | Optional[float], optional): The range
                of z values to be plotted. Defaults to None.
            groupby (Optional[Union[str, Iterable[str]]], optional): _description_.
                Defaults to None.

        Returns:
            str: The view ID.
        """
        ...
