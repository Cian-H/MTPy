import dash
from dash import html
from holoviews.plotting.plotly.dash import to_dash

from ..common.base import Base


class PlotterBase(Base):
    def __init__(self,
                 dashboard: bool | dash.dash.Dash = False,
                 dash_args: list = [],
                 dash_kwargs: dict = {},
                 **kwargs):
        super().__init__(**kwargs)
        self.views = {}
        if dashboard:
            if isinstance(dashboard, dash.dash.Dash):
                self.dashboard = dashboard
            else:
                self.dashboard = dash.Dash(__name__)
            self.dashboard_components = []
            self.dash_args = dash_args
            self.dash_kargs = dash_kwargs
    
    def add_to_dashboard(self, plot):
        # If a dashboard exists and it has components, add the new plot to the components
        if hasattr(self, "dashboard"):
            if hasattr(self, "dashboard_components"):
                self.dashboard_components.append(
                    plot
                )
            else:
                raise AttributeError(f"No dashboard_components list present in {self}")
        else:
            raise AttributeError(f"No dashboard present in {self}")
        # Then, update the dashboard to include this plot
        self.update_dashboard()
    
    def update_dashboard(self, *args, **kwargs):
        # if  no args or kwargs are given, use previously cached values if they exist,
        # otherwise, use args and kwargs given
        if not args and hasattr(self, "dash_args"):
            args = self.dash_args
        else:
            self.dash_args = args
        if not kwargs and hasattr(self, "dash_kwargs"):
            kwargs = self.dash_kwargs
        else:
            self.dash_kwargs = kwargs
        
        # Then, convert the components to dash and replace the dashboard layout with them
        components = to_dash(
            self.dashboard, self.dashboard_components, *args, **kwargs
        )
        self.dashboard.layout = html.Div(components.children)
    
    def run_dashboard_server(self, *args, **kwargs):
        self.dashboard.run_server(*args, **kwargs)
