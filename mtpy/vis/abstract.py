"""Data visualisation components of the MTPy module."""

from abc import ABCMeta, abstractmethod
from typing import Any, Dict, Iterable, Optional, Tuple

from datashader.reductions import Reduction
import holoviews as hv
from holoviews.element.chart import Chart

from mtpy.base.abstract import AbstractBase
from mtpy.loaders.protocol import LoaderProtocol

# import dash
# from dash import html
# from holoviews.plotting.plotly.dash import to_dash

hv.extension("plotly")


class AbstractPlotter(AbstractBase, metaclass=ABCMeta):
    """The base class for all plotter classes.

    Args:
        loader (LoaderProtocol): The data loader associated with this plotter.
    """

    def __init__(
        self: "AbstractPlotter",
        loader: LoaderProtocol,
        #  dashboard: bool | dash.dash.Dash = False,
        #  dash_args: list = [],
        #  dash_kwargs: dict = {},
    ) -> None:
        super().__init__()
        self.views: Dict[str, Chart] = {}
        self.view_tag = self.__class__.__name__
        self.loader = loader
        # if dashboard:
        #     if isinstance(dashboard, dash.dash.Dash):
        #         self.dashboard = dashboard
        #     else:
        #         self.dashboard = dash.Dash(__name__)
        #     self.dashboard_components = []
        #     self.dash_args = dash_args
        #     self.dash_kargs = dash_kwargs

    @abstractmethod
    def plot(
        self: "AbstractPlotter",
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
        """Creates a plot.

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
            xrange (Optional[Tuple[Optional[float], Optional[float]]]): the range
                of x values to plot. Defaults to None.
            yrange (Optional[Tuple[Optional[float], Optional[float]]]): the range
                of y values to plot. Defaults to None.
            zrange (Optional[Tuple[Optional[float], Optional[float]]]): the range
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
        ...

    def generate_view_id(
        self: "AbstractPlotter",
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
            kwargs (Optional[dict[str, object]], optional): The kwargs for the plotting function.
                Defaults to None.
            xrange (Tuple[Optional[float], Optional[float]] | Optional[float], optional): The range
                of x values to be plotted. Defaults to None.
            yrange (Tuple[Optional[float], Optional[float]] | Optional[float], optional): The range
                of y values to be plotted. Defaults to None.
            zrange (Tuple[Optional[float], Optional[float]] | Optional[float], optional): The range
                of z values to be plotted. Defaults to None.
            groupby (Optional[str | Iterable[str]], optional): the groupby to apply to the
                dataframe before plotting. Defaults to None.

        Returns:
            str: The view ID.
        """
        if kwargs is None:
            kwargs = {"x": "x", "y": "y", "z": "z"}

        view_id = f"{self.view_tag}_{kind}"

        if samples is not None:
            view_id += f"_s{samples!s}"
        view_id += f"_{kwargs['x']}"
        if xrange is not None:
            view_id += f"{xrange!s}"
        view_id += f"_{kwargs.get('y', '')}"
        if yrange is not None:
            view_id += f"{yrange!s}"
        view_id += f"_{kwargs.get('w', '')}"
        view_id += f"_{kwargs.get('z', '')}"
        if zrange is not None:
            view_id += f"{zrange!s}"
        if groupby is not None:
            view_id += f"_g{groupby!s}"
        return view_id

    # # Commenting this out as this feature isn't complete yet, it may be changed in future, and
    # # for now all it's doing is wreaking havoc on mypy
    # def init_panel(self, *args, **kwargs) -> None:
    #     """initialize the panel widgets"""
    #     if hasattr(self, "data"):
    #         # Create basic builtin panel widget items
    #         ops = [
    #             self.data["x"].min(),
    #             self.data["x"].max(),
    #             self.data["y"].min(),
    #             self.data["y"].max(),
    #             self.data["z"].min(),
    #             self.data["z"].max(),
    #             self.data["z"].unique(),
    #         ]
    #         if "samples" in self.data:
    #             ops.append(self.data["samples"].unique())
    #             xmin, xmax, ymin, ymax, zmin, zmax, layers, samples = dask.compute(*ops)
    #             self.sample_slider = pn.widgets.DiscreteSlider(
    #                 name="Sample", options=list(samples), value=None
    #             )
    #         else:
    #             xmin, xmax, ymin, ymax, zmin, zmax, layers = dask.compute(*ops)
    #             self.sample_slider = None

    #         self.xmin_slider = pn.widgets.FloatSlider(
    #             name="xmin", value=xmin, start=xmin, end=xmax
    #         )
    #         self.xmax_slider = pn.widgets.FloatSlider(
    #             name="xmax", value=xmin, start=xmin, end=xmax
    #         )
    #         self.ymin_slider = pn.widgets.FloatSlider(
    #             name="ymin", value=ymin, start=ymin, end=ymax
    #         )
    #         self.ymax_slider = pn.widgets.FloatSlider(
    #             name="ymax", value=ymin, start=ymin, end=ymax
    #         )
    #         self.zmin_slider = pn.widgets.FloatSlider(
    #             name="zmin", value=zmin, start=zmin, end=zmax
    #         )
    #         self.zmax_slider = pn.widgets.FloatSlider(
    #             name="zmax", value=zmin, start=zmin, end=zmax
    #         )
    #         self.layer_slider = pn.widgets.DiscreteSlider(
    #             name="Layer", options=list(layers), value=None
    #         )

    # def add_to_dashboard(self, plot):
    #     # If a dashboard exists and it has components, add the new plot to the components
    #     if hasattr(self, "dashboard"):
    #         if hasattr(self, "dashboard_components"):
    #             self.dashboard_components.append(
    #                 plot
    #             )
    #         else:
    #             raise AttributeError(f"No dashboard_components list present in {self}")
    #     else:
    #         raise AttributeError(f"No dashboard present in {self}")
    #     # Then, update the dashboard to include this plot
    #     self.update_dashboard()

    # def update_dashboard(self, *args, **kwargs):
    #     # if  no args or kwargs are given, use previously cached values if they exist,
    #     # otherwise, use args and kwargs given
    #     if not args and hasattr(self, "dash_args"):
    #         args = self.dash_args
    #     else:
    #         self.dash_args = args
    #     if not kwargs and hasattr(self, "dash_kwargs"):
    #         kwargs = self.dash_kwargs
    #     else:
    #         self.dash_kwargs = kwargs

    #     # Then, convert the components to dash and replace the dashboard layout with them
    #     components = to_dash(
    #         self.dashboard, self.dashboard_components, *args, **kwargs
    #     )
    #     self.dashboard.layout = html.Div(components.children)

    # def run_dashboard_server(self, *args, **kwargs):
    #     self.dashboard.run_server(*args, **kwargs)
