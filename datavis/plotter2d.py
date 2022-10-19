from itertools import chain
from typing import Iterable

from dash.dash import Dash
import dask
import holoviews as hv
import holoviews.operation.datashader as hd

from .plotter_base import PlotterBase

# NOTES: Matplotlib and plotly clearly arent up to the job alone here. Implement holoviews + datashading
# to give interactive, dynamically updating plots
# Added bonus: holoviews also makes possible to create interactive dashboards from plots
# See:
#   - https://holoviews.org/user_guide/Large_Data.html and ../mtpy_test/MTPy_Test.ipynb
#   - https://medium.com/plotly/introducing-dash-holoviews-6a05c088ebe5

# TODO: replace dash with holoviz panels

# Currently implemented plot kinds:
#   - scatter

hv.extension("plotly")


def plot2d_hook(colorbar_label):

    def hook(plot, element):
        plot.handles["components"]["traces"][0]["colorbar"]["title"] = colorbar_label

    return hook


class Plotter2D(PlotterBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def plot2D(
        self,
        kind: str,
        filename: None | str = None,
        add_to_dashboard: bool = False,
        samples: int | Iterable | None = False,
        xrange: tuple[float | None, float | None] | None = None,
        yrange: tuple[float | None, float | None] | None = None,
        zrange: tuple[float | None, float | None] | None = None,
        groupby: str | list[str] | None = None,
        aggregator: str = "mean",
        *args,
        **kwargs,
    ):
        chunk = self.data
        
        # add defaults for kwargs being passed through
        if "cmap" not in kwargs:
            kwargs["cmap"] = "plasma"

        # Filter to relevant samples
        if "sample" in chunk:
            if isinstance(samples, int):
                chunk = chunk.loc[chunk["sample"] == samples]
            elif isinstance(samples, Iterable):
                chunk = chunk.loc[chunk["sample"].isin(samples)]

        # take only columns needed for plotting
        axis_kws = ("x", "y", "z")
        columns = {
            k if k in axis_kws else None: v
            for k, v in chain(dict(zip(axis_kws, args)).items(), kwargs.items())
        }
        if None in columns: del columns[None]
        
        # if a groupby is present, ensure the data for grouping is kept
        if groupby is not None:
            columns["groupby"] = groupby
        chunk = chunk[list(columns.values())]

        # filter dataframe based on ranges given
        for axis, axis_range in zip(
            (columns[x] for x in axis_kws), (xrange, yrange, zrange)
        ):
            if axis_range is None:
                continue
            axis_min, axis_max = axis_range
            if axis_min is not None:
                chunk = chunk.loc[chunk[axis] >= axis_min]
            elif axis_max is not None:
                chunk = chunk.loc[chunk[axis] <= axis_max]

        # Then group if groupby is present (NOTE: NOT TESTED YET!)
        if groupby is not None:
            chunk = chunk.groupby(groupby)

        # generate a view id string for caching views
        view_id = f"plot2D_{kind}"

        if samples is not None:
            view_id += f"_s{str(samples)}"
        view_id += f"_{columns['x']}"
        if xrange is not None:
            view_id += f"{str(xrange)}"
        view_id += f"_{columns['y']}"
        if yrange is not None:
            view_id += f"{str(yrange)}"
        view_id += f"_{columns['z']}"
        if zrange is not None:
            view_id += f"{str(zrange)}"
        if groupby is not None:
            view_id += f"_g{str(groupby)}"

        # if view with same id already exists, fetch it, if not create one
        if view_id in self.views:
            plot = self.views[view_id]
        else:
            match kind:
                case "scatter":
                    plot_func = hv.Points
                case _:
                    raise ValueError(f"Unknown 2d plot kind given: {kind}")

            plot = plot_func(
                chunk, kdims=[columns["x"], columns["y"]], vdims=[columns["z"]], label=kind
            )
            self.views[view_id] = plot

        # I filename is given, save to that file
        if filename is not None:
            self._qprint(f"Saving to {filename}...")
            hv.save(plot, filename)
            self._qprint(f"{filename} saved!")

        # Create datashaded plot object
        ds_plot = hd.dynspread(hd.rasterize(plot, aggregator=aggregator)).opts(
                colorbar=True, cmap=kwargs["cmap"], hooks=[plot2d_hook(columns["z"])]
            )
        
        # If adding to dashboard, add this plot to the dashboard
        if add_to_dashboard and self.dashboard:
            self.add_to_dashboard(ds_plot)
        
        # Finally, return the plot for viewing, e.g. in jupyter notebook
        return ds_plot

    def scatter2D(self, *args, **kwargs):
        if "x" not in kwargs: kwargs["x"] = "x"
        if "y" not in kwargs: kwargs["y"] = "y"
        if "z" not in kwargs: kwargs["z"] = "t1"
        kwargs["kind"] = "scatter"
        return self.plot2D(*args, **kwargs)
