from __future__ import annotations

import panel as pn

# import dash
# from dash import html
# from holoviews.plotting.plotly.dash import to_dash
from ..common.base import Base


pn.extension()


class PlotterBase(Base):
    """The base class for all plotter classes."""

    def __init__(
        self,
        #  dashboard: bool | dash.dash.Dash = False,
        #  dash_args: list = [],
        #  dash_kwargs: dict = {},
        **kwargs,
    ):
        """initialize the PlotterBase class"""
        super().__init__(**kwargs)
        self.views = {}
        # if dashboard:
        #     if isinstance(dashboard, dash.dash.Dash):
        #         self.dashboard = dashboard
        #     else:
        #         self.dashboard = dash.Dash(__name__)
        #     self.dashboard_components = []
        #     self.dash_args = dash_args
        #     self.dash_kargs = dash_kwargs

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
