#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ..data.data_processor import DataProcessor
from pathlib import Path
from typing import Callable, Union
import numpy as np
from matplotlib import pyplot as plt
from mpl_toolkits import mplot3d  # noqa
from plotly import express as px

# This piece of init code prevents a warning resulting from generation of
#   many matplotlib "figure" objects. This is unimportant on my current
#   computer as i have plenty of RAM but if becomes an issue in future may need
#   to write a singleton wrapper object for plt.figure
plt.rcParams.update({"figure.max_open_warning": 0})

# Constants go here
valid_ws = ("t1", "t2")

# Default params for kwarg dicts libraries and a function for applying them
mtpy_defaults = {
    "data_path": Path.cwd()
}
sample_defaults = {
    "w": ["t1", "t2"],
    "plotparams": {}
}
viz_plot_defaults = {
    "colormap": "plasma",
    "colorbar": True,
    "shape": 2046
}
viz_figure_defaults = {
    "facecolor": "white"
}
mpl_plot_defaults = {
    "cmap": "plasma",
    "marker": ".",
}
mpl_figure_defaults = {
    "facecolor": "white"
}
plotly_plot_defaults = {
    "color_continuous_scale": "Plasma",
}
plotly_figure_defaults = {
}


def apply_defaults(kwargs, defaults):
    new_kwargs = kwargs.copy()
    for k, v in defaults.items():
        if k not in new_kwargs:
            new_kwargs[k] = v
    return new_kwargs


class MeltpoolTomography(DataProcessor):
    """
    Class for handling and processing meltpool tomography in the MTPy Module

    Attributes
    ----------
        quiet: bool = False
            Determines whether object should be quiet or not
        data_path: str = None
            The path to the data to be processed

    Methods
    -------
        dump(dumppath)
            Pickles object to location in dumppath
        undump(dumppath)
            Unpickles object at dumppath and copies its attributes to self
        read_layers(calibration_curve: FunctionType = None)
            Reads layer files into data structure for processing
        reset_data()
            Undoes all data processing that was performed on loaded data
        apply_calibration_curve(calibration_curve: FunctionType)
            Applies calibration curve function to w axis (temp) data
        avgspeed_threshold(x, y, z, threshold_percent=1, avgof=1)
            Thresholds data (x,y,z) based on percentage of max average slope
            of rolling average of displacement
        avgz_threshold(x, y, z, threshold_percent=1, comparison_func=None)
            Selectively keeps data based on comparison with a percentage of the
            mean of whatever z data is given
        avgz_greaterthan(x, y, z, threshold_percent=1)
            Keeps all values greater than threshold percent of average
        avgz_lessthan(x, y, z, threshold_percent=1)
            Keeps all values greater than threshold percent of average
        threshold_all_layers(thresh_functions, threshfunc_kwargs):
            Thresholds all layers by applying listed functions with listed
            params
        detect_samples(n_samples, label_samples: bool = True, mode="KMeans")
            Uses a clustering algorithm to detect samples automatically
        separate_samples()
            Separates labelled layer data into samples
        layers_to_heatmap(self, output_path, **kwargs)
            Generates figures from complete layers
        layers_to_3dplot(self, output_path, **kwargs)
            Function for generating 3d figures from layers
        samples_to_3dplots(output_path, filetype="png", z_range=None, z=None,
                           plot_w=False, colorbar=False, figureparams={},
                           plotparams={})
            Generates 3d figures for every labelled sample
        layers_to_3dscatter_interactive(output_path, **kwargs)
            Generates interactive 3d figures from complete layers
        samples_to_3dscatter_interactive(output_path, z_range=None, z=None,
                                       plot_w=False, downsampling=1,
                                       sliceable=False, plotparams={})
            Generates interactive 3d figures for every labelled sample
        temp_data_to_csv(output_path: str)
            Generates a csv containing temperature data for processed samples
    """

    def __init__(self, **kwargs):
        # Apply default args to kwargs if needed
        kwargs = apply_defaults(kwargs, mtpy_defaults)
        # Then call super and set attributes
        super().__init__(**kwargs)
        # Initialize bool for suppressing certain prints during callbacks
        self._quiet_callback = False

    def layers_to_heatmap(self, output_path,
                          filetype: str = "png",
                          sample_labels: bool = True,
                          w: Union[list, str] = ["t1", "t2"],
                          layer_filter: Callable[[float], bool] = None,
                          sample_filter: Callable[[float], bool] = None,
                          sample_data=None,
                          plotparams: dict = {},
                          figureparams: dict = {}):
        "Function for generating figures from layers"

        # apply defaults for matplotlib
        plotparams = apply_defaults(plotparams, viz_plot_defaults)
        figureparams = apply_defaults(figureparams, viz_figure_defaults)
        # Ensure all values in w are valid
        if type(w) is str:
            w = [w]
        for x in w:
            assert x in valid_ws
        if not self._quiet_callback:
            self._qprint(
                f"\nPreparing to generate layer heatmaps in {output_path}...")
        # Prepare path for figure generation
        output_path = str(Path(output_path).expanduser())
        Path(output_path).mkdir(parents=True, exist_ok=True)
        # apply sample filter if possible and given one
        if "sample" in self.data:
            if sample_filter is not None:
                data = self.data[sample_filter(self.data["sample"])]
            else:
                data = self.data
        else:
            self._qprint("\nNo sample labels present!")
            data = self.data
        # apply layer filter if given one
        if layer_filter is not None:
            data = data[layer_filter(self.data["z"])]
        # pull out vmin and vmax in case doing per-column normalization
        vmin, vmax = {}, {}
        if "vmin" and "vmax" in plotparams:
            vmin = plotparams.pop("vmin")
            vmax = plotparams.pop("vmax")
            if not ((type(vmin) is dict)
                    and (type(vmin) is dict)):
                vmin = {x: vmin for x in w}
                vmax = {x: vmax for x in w}
        else:
            for column in w:
                vmin[column] = float(self.data[column].min())
                vmax[column] = float(self.data[column].max())

        if not self._quiet_callback:
            self._qprint("\nGenerating layer heatmaps")

        # Prep progress bar iterator (assigned to variable for code clarity)
        if sample_data is not None:
            layer_iterator = sample_data.groupby("z")
        else:
            layer_iterator = data.groupby("z")
        progbar_iterator = self.progressbar(layer_iterator,
                                            desc="Layers",
                                            total=len(layer_iterator),
                                            leave=False,
                                            position=1,
                                            disable=self.quiet)
        # Loop through layers
        for layer, layer_data in progbar_iterator:
            # Make progress bar for w plots if more than one w
            if type(w) is str:
                w_iterator = [w]
            elif (wlength := len(w)) > 1:
                w_iterator = self.progressbar(w,
                                              desc="Plots",
                                              total=wlength,
                                              leave=False,
                                              position=2,
                                              disable=self.quiet)
            else:
                w_iterator = w
            # Plot for every requested w axis
            for column in w_iterator:
                # if per-column normalizing apply vmin and vmax
                if type(vmin) is dict:
                    plotparams["vmin"] = vmin[column]
                if type(vmax) is dict:
                    plotparams["vmax"] = vmax[column]
                # Filter out target layer
                if plotparams["colorbar"] \
                        and "colorbar_label" not in plotparams:
                    plotparams["colorbar_label"] = \
                        f"{self.temp_label} ({self.temp_units})"
                # Create plot
                heatmap = layer_data.viz.heatmap(
                    x="x", y="y",
                    what=f"max({column})",
                    **plotparams
                )
                # Get figure and axis
                fig = heatmap.figure.get_figure()
                ax = fig.axes[0]
                # If labels are given, add labels for all samples in layer
                if hasattr(self, "sample_labels") and sample_labels:
                    samples_present = data["sample"].unique()
                    samples_present = {key: val for (key, val) in
                                       enumerate(self.sample_labels) if
                                       key in samples_present}
                    for i, xy in samples_present.items():
                        ax.annotate(str(i), xy)
                # Save figure and clear pyplot buffer
                fig.savefig(f"{output_path}/{column}_heatmap_z={layer}.{filetype}",  # noqa
                            **figureparams)
                # Clear figure and ensure large, local objects get deleted
                fig.clf()
                del layer_data, heatmap, fig, ax
        # Delete last filter to remove unneeded vaex filters
        del data

        if not self._quiet_callback:
            self._qprint("Layer heatmaps complete!\n")

    def samples_to_heatmap(self, output_path,
                           global_norm: bool = False,
                           **kwargs):
        # apply defaults to kwargs
        kwargs = apply_defaults(kwargs, sample_defaults)
        self._qprint(
            f"\nPreparing to generate sample heatmaps in {output_path}...")
        output_path = str(Path(output_path).expanduser())
        Path(output_path).mkdir(parents=True, exist_ok=True)
        # if not specified otherwise turn off sample labels
        if "sample_labels" not in kwargs:
            kwargs["sample_labels"] = False
        # if asked for global_norm, define fixed norm for all samples
        plotparams = kwargs["plotparams"]
        plotparams = apply_defaults(plotparams, viz_plot_defaults)
        global_vmin, global_vmax = False, False
        if global_norm:
            w = kwargs["w"]
            global_vmin, global_vmax = {}, {}
            for column in w:
                if "vmin" in plotparams:
                    vmin = plotparams["vmin"]
                else:
                    vmin = float(self.data[column].min())
                if "vmax" in plotparams:
                    vmax = plotparams["vmax"]
                else:
                    vmax = float(self.data[column].max())
                global_vmin[column] = vmin
                global_vmax[column] = vmax
            plotparams["vmin"] = global_vmin
            plotparams["vmax"] = global_vmax

        # Announce all settings set and proceed to generate plots
        self._qprint("\nGenerating sample heatmaps")

        # Prep progress bar iterator (assigned to variable for code clarity)
        sample_iterator = self.data.groupby("sample")
        progbar_iterator = self.progressbar(sample_iterator,
                                            total=len(sample_iterator),
                                            desc="Samples",
                                            position=0,
                                            disable=self.quiet)

        self._quiet_callback = True
        # Loop through layers in layerdict
        for sample_number, sample_data in progbar_iterator:
            # Set sample filter for selected layer
            kwargs["sample_filter"] = lambda x: x == sample_number
            kwargs["sample_data"] = sample_data
            # Plot all layers in the sample
            self.layers_to_heatmap(f"{output_path}/{sample_number}",
                                   **kwargs)
        self._quiet_callback = False

        self._qprint("Sample heatmaps complete!\n")

    def layers_to_scatter(self, output_path,
                          filetype: str = "png",
                          sample_labels: bool = True,
                          w: Union[list, str] = ["t1", "t2"],
                          layer_filter: Callable[[float], bool] = None,
                          sample_filter: Callable[[float], bool] = None,
                          plotparams: dict = {},
                          figureparams: dict = {}):
        "Function for generating figures from layers"

        # apply defaults for matplotlib
        plotparams = apply_defaults(plotparams, mpl_plot_defaults)
        figureparams = apply_defaults(figureparams, mpl_figure_defaults)
        # Ensure all values in w are valid
        if type(w) is str:
            w = [w]
        for x in w:
            assert x in valid_ws
        if not self._quiet_callback:
            self._qprint(
                f"\nPreparing to generate layer scatters in {output_path}...")
        # Prepare path for figure generation
        output_path = str(Path(output_path).expanduser())
        Path(output_path).mkdir(parents=True, exist_ok=True)
        # apply sample filter if possible and given one
        if "sample" in self.data:
            if sample_filter is not None:
                data = self.data[sample_filter(self.data["sample"])]
            else:
                data = self.data
        else:
            self._qprint("\nNo sample labels present!")
            data = self.data
        # apply layer filter if given one
        if layer_filter is not None:
            data = data[layer_filter(self.data["z"])]
        # pull out vmin and vmax in case doing per-column normalization
        vmin, vmax = {}, {}
        if "vmin" and "vmax" in plotparams:
            vmin = plotparams.pop("vmin")
            vmax = plotparams.pop("vmax")
            if not ((type(vmin) is dict)
                    and (type(vmin) is dict)):
                vmin = {x: vmin for x in w}
                vmax = {x: vmax for x in w}
        else:
            for column in w:
                vmin[column] = float(self.data[column].min())
                vmax[column] = float(self.data[column].max())
        layers = data["z"].unique()

        if not self._quiet_callback:
            self._qprint("\nGenerating layer scatters")

        # Prep progress bar iterator (assigned to variable for code clarity)
        progbar_iterator = self.progressbar(layers,
                                            desc="Layers",
                                            total=len(layers),
                                            leave=False,
                                            position=1,
                                            disable=self.quiet)
        # Loop through layers
        for layer in progbar_iterator:
            # Make progress bar for w plots if more than one w
            if type(w) is str:
                w_iterator = [w]
            elif (wlength := len(w)) > 1:
                w_iterator = self.progressbar(w,
                                              desc="Plots",
                                              total=wlength,
                                              leave=False,
                                              position=2,
                                              disable=self.quiet)
            else:
                w_iterator = w
            # Plot for every requested w axis
            for column in w_iterator:
                # if per-column normalizing apply vmin and vmax
                if type(vmin) is dict:
                    local_vmin = vmin[column]
                if type(vmax) is dict:
                    local_vmax = vmax[column]
                # Create norm and colormap
                plotparams["norm"] = plt.Normalize(vmin=local_vmin,
                                                   vmax=local_vmax)
                mappable = plt.cm.ScalarMappable(norm=plotparams["norm"],
                                                 cmap=plotparams["cmap"])
                # Filter out target layer
                layer_data = data[data["z"] == layer]
                # Create plot
                scatter = layer_data.viz.scatter(
                    x="x", y="y",
                    c=layer_data[column].to_numpy(),
                    length_check=False,
                    **plotparams
                )
                # Get figure and axis
                fig = scatter.figure.get_figure()
                ax = fig.axes[0]
                # Create a colorbar
                fig.colorbar(mappable, label=self.temp_label)
                # Finally, format plots appropriately
                ax.set_xlabel("x")
                ax.set_ylabel("y")
                # If labels are given, add labels for all samples in layer
                if hasattr(self, "sample_labels") and sample_labels:
                    samples_present = data["sample"].unique()
                    samples_present = {key: val for (key, val) in
                                       enumerate(self.sample_labels) if
                                       key in samples_present}
                    for i, xy in samples_present.items():
                        ax.annotate(str(i), xy)
                # Save figure and clear pyplot buffer
                fig.savefig(f"{output_path}/{column}_scatter_z={layer}.{filetype}",  # noqa
                            **figureparams)
                # Clear figure and ensure large, local objects get deleted
                fig.clf()
                del layer_data, scatter, fig, ax
        # Delete last filter to remove unneeded vaex filters
        del data

        if not self._quiet_callback:
            self._qprint("Layer scatters complete!\n")

    def samples_to_scatter(self, output_path,
                           global_norm: bool = False,
                           **kwargs):
        # apply defaults to kwargs
        kwargs = apply_defaults(kwargs, sample_defaults)
        self._qprint(
            f"\nPreparing to generate sample scatters in {output_path}...")
        output_path = str(Path(output_path).expanduser())
        Path(output_path).mkdir(parents=True, exist_ok=True)
        samples = self.data["sample"].unique()
        # if not specified otherwise turn off sample labels
        if "sample_labels" not in kwargs:
            kwargs["sample_labels"] = False
        # if asked for global_norm, define fixed norm for all samples
        plotparams = kwargs["plotparams"]
        plotparams = apply_defaults(plotparams, mpl_plot_defaults)
        global_vmin, global_vmax = False, False
        if global_norm:
            w = kwargs["w"]
            global_vmin, global_vmax = {}, {}
            for column in w:
                if "vmin" in plotparams:
                    vmin = plotparams["vmin"]
                else:
                    vmin = float(self.data[column].min())
                if "vmax" in plotparams:
                    vmax = plotparams["vmax"]
                else:
                    vmax = float(self.data[column].max())
                global_vmin[column] = vmin
                global_vmax[column] = vmax
            plotparams["vmin"] = global_vmin
            plotparams["vmax"] = global_vmax

        # Announce all settings set and proceed to generate plots
        self._qprint("\nGenerating sample scatters")

        # Prep progress bar iterator (assigned to variable for code clarity)
        progbar_iterator = self.progressbar(samples,
                                            total=len(samples),
                                            desc="Samples",
                                            position=0,
                                            disable=self.quiet)

        self._quiet_callback = True
        # Loop through layers in layerdict
        for sample_number in progbar_iterator:
            # Set sample filter for selected layer
            kwargs["sample_filter"] = lambda x: x == sample_number
            # Plot all layers in the sample
            self.layers_to_scatter(f"{output_path}/{sample_number}",
                                   **kwargs)
        self._quiet_callback = False

        self._qprint("Sample scatters complete!\n")

    def layers_to_3dscatter(self, output_path,
                            filetype: str = "png",
                            colorbar: bool = True,
                            w: Union[list, str] = ["t1", "t2"],
                            layer_filter: Callable[[float], bool] = None,
                            sample_filter: Callable[[float], bool] = None,
                            plotparams: dict = {},
                            figureparams: dict = {}):
        """
        Function for generating 3d figures from complete layers
        """

        # apply defaults for matplotlib
        plotparams = apply_defaults(plotparams, mpl_plot_defaults)
        figureparams = apply_defaults(figureparams, mpl_figure_defaults)
        # make sure there is no "c" in plotparams
        if "c" in plotparams:
            del plotparams["c"]
        # Ensure all values in w are valid
        if type(w) is str:
            w = [w]
        for x in w:
            assert x in valid_ws
        if not self._quiet_callback:
            self._qprint(f"\nPreparing to generate 3dscatter in {output_path}...")  # noqa
        # Prepare path for figure generation
        output_path = str(Path(output_path).expanduser())
        Path(output_path).mkdir(parents=True, exist_ok=True)
        # apply sample filter if possible and given one
        if "sample" in self.data:
            if sample_filter is not None:
                data = self.data[sample_filter(self.data["sample"])]
            else:
                data = self.data
        else:
            self._qprint("\nNo sample labels present!")
            data = self.data
        # apply layer filter if given one
        if layer_filter is not None:
            data = data[layer_filter(self.data["z"])]
        # Prepare colormaps
        cmap_info = {}
        for column in w:
            if "norm" in plotparams:
                if type(plotparams["norm"]) is dict:
                    cmap_info = plotparams["norm"]
                    break
                else:
                    norm = plotparams["norm"]
            else:
                if "vmin" in plotparams:
                    vmin = plotparams.pop("vmin")
                else:
                    vmin = data[column].min()
                if "vmax" in plotparams:
                    vmax = plotparams.pop("vmax")
                else:
                    vmax = data[column].max()
                norm = plt.Normalize(vmin=vmin, vmax=vmax)
            mappable = plt.cm.ScalarMappable(norm,
                                             cmap=plotparams["cmap"])
            cmap_info[column] = (norm, mappable)
        if not self._quiet_callback:
            self._qprint("\nGenerating 3dscatter")
        # Make progress bar for w plots if more than one w
        if type(w) is str:
            w_iterator = [w]
        elif (wlength := len(w)) > 1:
            w_iterator = self.progressbar(w,
                                          desc="Plots",
                                          total=wlength,
                                          leave=False,
                                          position=1,
                                          disable=self.quiet)
        else:
            w_iterator = w
        # Plot for every requested w axis
        for column in w_iterator:
            # Retrieve colormap info for column
            norm, mappable = cmap_info[column]
            # assign norm for column
            plotparams["norm"] = norm
            # Create figure and 3d axes
            plt.figure(**figureparams)
            ax = plt.axes(projection="3d")
            ax.scatter(data["x"].to_numpy(),
                       data["y"].to_numpy(),
                       data["z"].to_numpy(),
                       c=data[column].to_numpy(),
                       **plotparams)
            # If we want a colorbar create one
            if colorbar:
                plt.colorbar(mappable,
                             label=f"{self.temp_label} ({self.temp_units})")
            # Finally, format plots appropriately
            ax.set_xlabel("x")
            ax.set_ylabel("y")
            ax.set_zlabel("z")
            # Save figure and clear pyplot buffer
            plt.savefig(f"{output_path}/{column}_3dscatter.{filetype}")
            plt.clf()
        # Delete last filter to remove unneeded vaex filters
        del data

        if not self._quiet_callback:
            self._qprint("3dscatter complete!\n")

    # Does same as layers_to_3dscatter but for each individual sample instead
    #   of entire layer
    def samples_to_3dscatter(self, output_path,
                             global_norm: bool = False,
                             **kwargs):
        "Generates 3d figures for every labelled sample"
        # apply defaults to kwargs
        kwargs = apply_defaults(kwargs, sample_defaults)
        self._qprint(
            f"\nPreparing to generate sample 3dplots in {output_path}...")
        output_path = str(Path(output_path).expanduser())
        Path(output_path).mkdir(parents=True, exist_ok=True)
        samples = self.data["sample"].unique()
        self._qprint("\nGenerating sample 3dscatters")

        # if asked for global_norm, define fixed norm for all samples
        if global_norm:
            plotparams, w = kwargs["plotparams"], kwargs["w"]
            plotparams = apply_defaults(plotparams, mpl_plot_defaults)
            # This loop is copy/pasted from layers_to_heatmap with slight tweak
            cmap_info = {}
            for column in w:
                if "norm" in plotparams:
                    if type(plotparams["norm"]) is dict:
                        cmap_info = plotparams["norm"]
                        break
                    else:
                        norm = plotparams["norm"]
                else:
                    if "vmin" in plotparams:
                        vmin = plotparams.pop("vmin")
                    else:
                        vmin = self.data[column].min()
                    if "vmax" in plotparams:
                        vmax = plotparams.pop("vmax")
                    else:
                        vmax = self.data[column].max()
                    norm = plt.Normalize(vmin=vmin, vmax=vmax)
                mappable = plt.cm.ScalarMappable(norm,
                                                 cmap=plotparams["cmap"])
                cmap_info[column] = (norm, mappable)
            else:
                plotparams["norm"] = cmap_info
        # Announce all settings set and proceed to generate plots
        self._qprint("\nGenerating sample 3scatters")

        # Prep progress bar iterator (assigned to variable for code clarity)
        progbar_iterator = self.progressbar(samples,
                                            total=len(samples),
                                            desc="Samples",
                                            position=0,
                                            disable=self.quiet)

        self._quiet_callback = True
        # Loop through layers in layerdict
        for sample_number in progbar_iterator:
            # Set sample filter for selected layer
            kwargs["sample_filter"] = lambda x: x == sample_number
            # Plot all layers in the sample
            self.layers_to_3dscatter(f"{output_path}/{sample_number}",
                                     **kwargs)
        self._quiet_callback = False

        self._qprint("Sample 3dscatters complete!\n")

    def layers_to_3dscatter_interactive(self, output_path,
                                        downsampling: int = 1,
                                        sliceable: bool = False,
                                        w: Union[list, str] = ["t1", "t2"],
                                        hover_data=[],
                                        layer_filter: Callable[[float], bool] = None,  # noqa
                                        sample_filter: Callable[[float], bool] = None,  # noqa
                                        plotparams: dict = {},
                                        figureparams: dict = {}):
        """
        Internally called function for generating interactive 3d figures from
        complete layers
        """
        if not self._quiet_callback:
            self._qprint(f"\nPreparing to generate interactive 3dscatter in {output_path}...")  # noqa

        # apply defaults for matplotlib
        plotparams = apply_defaults(plotparams, plotly_plot_defaults)
        figureparams = apply_defaults(figureparams, plotly_figure_defaults)
        # Ensure all values in w are valid
        if type(w) is str:
            w = [w]
        for x in w:
            assert x in valid_ws
        if not self._quiet_callback:
            self._qprint("\nGenerating interactive 3dscatter")
        # Prepare path for figure generation
        output_path = str(Path(output_path).expanduser())
        Path(output_path).mkdir(parents=True, exist_ok=True)
        # apply sample filter if possible and given one
        if "sample" in self.data:
            if sample_filter is not None:
                data = self.data[sample_filter(self.data["sample"])]
            else:
                data = self.data
        else:
            self._qprint("\nNo sample labels present!")
            data = self.data
        # apply layer filter if given one
        if layer_filter is not None:
            data = data[layer_filter(self.data["z"])]
        else:
            data = data

        # Modify dynamically controlled plot params for plotting
        if "color" in plotparams:
            del(plotparams["color"])
        if "range_z" not in plotparams:
            plotparams["range_z"] = [0., data["z"].max() + 0.1]
        # add n to hover data
        hover_data += ["n"]

        # Downsample data for plotting
        if downsampling > 1:
            data = data[(data["n"] % downsampling) == 0]

        # Add units to all w values
        w_units = [f"{column} ({self.temp_units})" for column in w]
        w_map = dict(zip(w, w_units))
        for column, column_units in w_map.items():
            data.rename(column, column_units)

        # Update w values in hover_data (if present)
        hover_data = [w_map[x] if x in w_map else x for x in hover_data]

        # Prep progress bar iterator (assigned to variable for code clarity)
        progbar_iterator = self.progressbar(w_map.items(),
                                            desc="Plots",
                                            total=len(w),
                                            leave=False,
                                            position=1,
                                            disable=self.quiet)

        # # Prepare for type casting after converting to pandas df
        # df_columns = ["x", "y", "z", *w_units, *hover_data]
        # # Convert minimized vaex selection to a pandas df for plotting
        # data = data.to_pandas_df(df_columns)

        # Plot for every requested w axis
        for column, column_units in progbar_iterator:

            # # Create figure and save to html
            # fig = px.scatter_3d(data,
            #                     x="x", y="y", z="z",
            #                     color=column_units,
            #                     hover_data=hover_data,
            #                     **plotparams)
            # Create figure and save to html
            fig = px.scatter_3d(x=data["x"].to_numpy(),
                                y=data["y"].to_numpy(),
                                z=data["z"].to_numpy(),
                                color=data[column_units].to_numpy(),
                                hover_data=[data[x].to_numpy() for x in hover_data],  # noqa
                                **plotparams)
            fig.write_html(
                f"{output_path}/3dscatter_interactive_{column}.html",
                **figureparams
            )
        # Delete last filter to remove unneeded vaex filters
        del data

        if not self._quiet_callback:
            self._qprint("Interactive 3dscatter complete!\n")

    def samples_to_3dscatter_interactive(self, output_path,
                                         global_norm: bool = False,
                                         **kwargs):
        "Generates interactive 3d figures for every labelled sample"
        self._qprint(f"\nPreparing to generate sample interactive 3dplots in {output_path}...")  # noqa

        output_path = str(Path(output_path).expanduser())
        Path(output_path).mkdir(parents=True, exist_ok=True)

        samples = self.data["sample"].unique()

        self._qprint("\nGenerating sample interactive 3dplots")

        # Prep progress bar iterator (assigned to variable for code clarity)
        progbar_iterator = self.progressbar(samples,
                                            total=len(samples),
                                            desc="Samples",
                                            position=0,
                                            disable=self.quiet)

        self._quiet_callback = True
        # Loop through layers in layerdict
        for sample_number in progbar_iterator:
            # Set sample filter for selected layer
            kwargs["sample_filter"] = lambda x: x == sample_number
            # Plot all layers in the sample
            self.layers_to_3dscatter_interactive(
                f"{output_path}/{sample_number}",
                **kwargs
            )
        self._quiet_callback = False

        self._qprint("Sample interactive 3dplots complete!\n")

    def calculate_stats(self, groupby: list = [], confidence_interval=0.95):
        stats = self.data.groupby(groupby, agg={"t1": ["min", "max", "mean", "std"]})
        stats["t1_stderr"] = stats["t1_std"] / np.sqrt(stats["t1_mean"])
        stats["t1_ci_error"] = 0.95 * stats["t1_stderr"]
        stats["t1_ci_min"] = stats["t1_mean"] - stats["t1_ci_error"]
        stats["t1_ci_max"] = stats["t1_mean"] + stats["t1_ci_error"]
        return stats

    def temp_data_to_csv(self, output_path: str,
                         layers: bool = True,
                         samples: bool = True,
                         sample_layers: bool = True,
                         w: Union[list, str] = ["t1", "t2"],
                         layer_filter: Callable[[float], bool] = None,
                         sample_filter: Callable[[float], bool] = None,
                         confidence_interval: float = 0.95):
        "Generates a csv containing temperature data for processed samples"
        Path(output_path).mkdir(parents=True, exist_ok=True)
        if output_path[-1] != "/":
            output_path += "/"
        if layers:
            self.calculate_stats(groupby="z").export_csv(f"{output_path}layertemps.csv")
        if samples:
            self.calculate_stats(groupby="sample").export_csv(f"{output_path}sampletemps.csv")
        if sample_layers:
            self.calculate_stats(groupby=["sample", "z"]).export_csv(f"{output_path}samplelayertemps.csv")
        self._qprint(f"Datasheets generated at {output_path}!")
