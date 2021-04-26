#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ..data.data_processor import DataProcessor
from pathlib import Path
from types import FunctionType
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from mpl_toolkits import mplot3d  # noqa
from plotly import express as px
import scipy.stats as st

# This piece of init code prevents a warning resulting from generation of
#   many matplotlib "figure" objects. This is unimportant on my current
#   computer as i have plenty of RAM but if becomes an issue in future may need
#   to write a singleton wrapper object for plt.figure
plt.rcParams.update({"figure.max_open_warning": 0})


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
        layers_to_figures(self, output_path, **kwargs)
            Generates figures from complete layers
        layers_to_3dplot(self, output_path, **kwargs)
            Function for generating 3d figures from layers
        samples_to_3dplots(output_path, filetype="png", z_range=None, z=None,
                           plot_w=False, colorbar=False, figureparams={},
                           plotparams={})
            Generates 3d figures for every labelled sample
        layers_to_3dplot_interactive(output_path, **kwargs)
            Generates interactive 3d figures from complete layers
        samples_to_3dplots_interactive(output_path, z_range=None, z=None,
                                       plot_w=False, downsampling=1,
                                       sliceable=False, plotparams={})
            Generates interactive 3d figures for every labelled sample
        temp_data_to_csv(output_path: str)
            Generates a csv containing temperature data for processed samples
    """

    def __init__(self, wlabel: str = "Temp (mv)", **kwargs):
        # Default args for the kwargs dictionary
        default_args = {"data_path": Path.cwd()}
        # Apply default args to kwargs if needed
        for arg, value in default_args.items():
            if arg not in kwargs:
                kwargs[arg] = value
        # Then call super and set attributes
        super().__init__(**kwargs)
        self.wlabel = wlabel

    def read_layers(self, wlabel: str = None, **kwargs):
        super().read_layers(**kwargs)
        if wlabel is not None:
            self.wlabel = wlabel

    def apply_calibration_curve(self, calibration_curve: FunctionType,
                                wlabel: str = None):
        super().apply_calibration_curve(calibration_curve)
        if wlabel is not None:
            self.wlabel = wlabel

    def _layers_to_figures(self, layers, output_path, filetype="png",
                           plot_w=True, colorbar=True,
                           figureparams={}, scatterparams={}):
        "Internally called function for generating figures from layers"
        self._qprint(
            f"\nPreparing to generate layer plots in {output_path}...")

        output_path = str(Path(output_path).expanduser())
        Path(output_path).mkdir(parents=True, exist_ok=True)

        self._qprint("\nGenerating layer plots")
        # Create figure
        plt.figure(**figureparams)
        # Loop through layers
        for layer_number, layer_data in self.progressbar(layers.items(),
                                                         total=len(layers),
                                                         disable=self.quiet):
            # If plotting z or averaging z assign variable
            if plot_w:
                z = layer_data[2, :]
            else:
                z = None
            # Create figure and scatter plot
            plt.scatter(layer_data[0, :], layer_data[1, :],
                        c=z, **scatterparams)
            # If we want a colorbar create one
            if colorbar and plot_w:
                plt.colorbar(label=self.wlabel)
            # If labels are given, plot them
            if self.sample_labels is not None:
                for i, xy in enumerate(self.sample_labels):
                    plt.annotate(str(i), xy)
            # Finally, format plots appropriately
            plt.xlabel("X")
            plt.ylabel("Y")
            # Save figure and clear pyplot buffer
            plt.savefig(f"{output_path}/{layer_number}.{filetype}")
            plt.clf()

        self._qprint("Layer plots complete!\n")

    def layers_to_figures(self, output_path, **kwargs):
        "Generates figures from complete layers"
        self._layers_to_figures(self.data_dict, output_path, **kwargs)

    def samples_to_figures(self, output_path, filetype="png",
                           plot_w=True, colorbar=True, figureparams={},
                           scatterparams={}):

        self._qprint(
            f"\nPreparing to generate sample plots in {output_path}...")

        output_path = str(Path(output_path).expanduser())
        Path(output_path).mkdir(parents=True, exist_ok=True)

        self._qprint("\nGenerating sample plots")

        # Loop through layers in layerdict
        for sample_number, sample_data in self.progressbar(
                                              self.sample_data.items(),
                                              total=len(self.sample_data),
                                              desc="Overall",
                                              disable=self.quiet):
            # Plot all layers in the sample
            self._layers_to_figures(sample_data,
                                    f"{output_path}/{sample_number}",
                                    plot_w=plot_w,
                                    colorbar=colorbar,
                                    figureparams=figureparams,
                                    scatterparams=scatterparams)

        self._qprint("Sample plots complete!\n")

    def _layers_to_3dplot(self, layers, output_path, filetype="png",
                          plot_w=True, colorbar=True,
                          figureparams={}, plotparams={}):
        """
        Internally called function for generating 3d figures from complete
        layers
        """
        self._qprint(f"\nPreparing to generate 3dplot in {output_path}...")

        output_path = str(Path(output_path).expanduser())
        Path(output_path).mkdir(parents=True, exist_ok=True)

        self._qprint("Preparing plot pointcloud")
        # Create full array of z values
        plotarray = []
        for (_, layer_data), z_value in self.progressbar(
                                            zip(layers.items(),
                                                self.data_dict.keys()),
                                            total=len(layers),
                                            disable=self.quiet):
            # prepare to generate numpy array of x, y, z values & w if present
            newlayer = [layer_data[:2, :],
                        np.repeat(z_value, layer_data.shape[1])]
            if layer_data.shape[0] == 3:
                newlayer.append(layer_data[2, :])
            plotarray.append(np.vstack(newlayer))
        plotarray = np.concatenate(plotarray, axis=1)
        plotarray = plotarray.T

        self._qprint("\nGenerating 3dplots")
        # Create figure and 3d axes
        plt.figure(**figureparams)
        ax = plt.axes(projection="3d")
        if plot_w:
            w = plotarray[:, 3]
        else:
            w = None
        p = ax.scatter(plotarray[:, 0], plotarray[:, 1], plotarray[:, 2], c=w,
                       **plotparams)
        # If we want a colorbar create one
        if colorbar and plot_w:
            plt.colorbar(p, label=self.wlabel)
        # Finally, format plots appropriately
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_zlabel("Z")
        # Save figure and clear pyplot buffer
        plt.savefig(f"{output_path}/3dplot.{filetype}")
        plt.clf()

        self._qprint("3dplot complete!\n")

    def layers_to_3dplot(self, output_path, **kwargs):
        "Function for generating 3d figures from layers"
        self._layers_to_3dplot(self.data_dict, output_path, **kwargs)

    # Does same as layers_to_3dplots but for each individual sample instead of
    #   entire layer
    def samples_to_3dplots(self, output_path, filetype="png", plot_w=True,
                           colorbar=True, figureparams={}, plotparams={}):
        "Generates 3d figures for every labelled sample"
        self._qprint(
            f"\nPreparing to generate sample 3dplots in {output_path}...")

        output_path = str(Path(output_path).expanduser())
        Path(output_path).mkdir(parents=True, exist_ok=True)

        self._qprint("\nGenerating sample 3dplots")

        # Loop through layers in layerdict
        for sample_number, sample_data in self.progressbar(
                                              self.sample_data.items(),
                                              total=len(self.sample_data),
                                              desc="Overall",
                                              disable=self.quiet):
            # Plot all layers in the sample
            self._layers_to_3dplot(sample_data,
                                   f"{output_path}/{sample_number}",
                                   plot_w=plot_w,
                                   colorbar=colorbar,
                                   figureparams=figureparams,
                                   plotparams=plotparams)

        self._qprint("Sample 3dplots complete!\n")

    def _layers_to_3dplot_interactive(self, layers, output_path,
                                      downsampling=1, sliceable=False,
                                      plot_w=True, plotparams={}):
        """
        Internally called function for generating interactive 3d figures from
        complete layers
        """
        self._qprint(
            f"\nPreparing to generate 3dplot_interactive in {output_path}...")

        output_path = str(Path(output_path).expanduser())
        Path(output_path).mkdir(parents=True, exist_ok=True)

        self._qprint("Preparing plot pointcloud")
        # Create full array of z values
        plotarray = []
        for (_, layer_data), z_value in self.progressbar(
                                            zip(layers.items(),
                                                self.data_dict.keys()),
                                            total=len(layers),
                                            disable=self.quiet):
            # prepare to generate numpy array of x, y, z values & w if present
            newlayer = [layer_data[:2, :],
                        np.repeat(z_value, layer_data.shape[1])]
            if layer_data.shape[0] == 3:
                newlayer.append(layer_data[2, :])
            plotarray.append(np.vstack(newlayer))
        plotarray = np.concatenate(plotarray, axis=1)
        plotarray = plotarray.T

        self._qprint("\nGenerating 3dplot_interactive")

        df = pd.DataFrame(data={"X": plotarray[::downsampling, 0],
                                "Y": plotarray[::downsampling, 1],
                                "Z": plotarray[::downsampling, 2],
                                })

        # If plotting a 4th dimension, add column for w
        if plot_w:
            df[self.wlabel] = plotarray[::downsampling, 3]
            plotparams["color"] = self.wlabel

            if "range_color" not in plotparams:
                plotparams["range_color"] = (df[self.wlabel].max(),
                                             df[self.wlabel].min())

            if "color_continuous_scale" not in plotparams:
                plotparams["color_continuous_scale"] = "Jet"

        # Finally, add indeces (n) for data points
        # NOTE: may add functionality for additional data in
        #       plotly tooltip bubble here later
        df["n"] = range(0, plotarray[:, 0].size, downsampling)

        # Create column for animation slider
        if sliceable:
            # Get all z values
            layer_values = sorted(set(df["Z"]))
            unfiltered_dataframes = [df.copy() for i in layer_values]
            filtered_dataframes = []
            # Create multiple version of dataset corresponding to different
            # frames
            for top_layer, dataframe in zip(layer_values,
                                            unfiltered_dataframes):
                filtered_dataframes.append(df.loc[df["Z"] <= top_layer].copy())
            # Then add columns denoting frame numbers
            for dataframe in filtered_dataframes:
                dataframe["Top Layer"] = dataframe["Z"].max()
            # Combine frames into new dataset
            df = pd.concat(filtered_dataframes)
            # Finally, add params for animation
            plotparams["animation_frame"] = "Top Layer"

        # Create figure and save to html
        fig = px.scatter_3d(df, x="X", y="Y", z="Z",
                            hover_data="n", **plotparams)
        fig.write_html(f"{output_path}/3dplot_interactive.html")

        self._qprint("3dplot_interactive complete!\n")

    def layers_to_3dplot_interactive(self, output_path, **kwargs):
        "Generates interactive 3d figures from complete layers"
        self._layers_to_3dplot_interactive(self.data_dict, output_path,
                                           **kwargs)

    def samples_to_3dplots_interactive(self, output_path, plot_w=True,
                                       downsampling=1, sliceable=False,
                                       plotparams={}):
        "Generates interactive 3d figures for every labelled sample"
        self._qprint(f"\nPreparing to generate sample interactive 3dplots in {output_path}...")  # noqa

        output_path = str(Path(output_path).expanduser())
        Path(output_path).mkdir(parents=True, exist_ok=True)

        self._qprint("\nGenerating sample interactive 3dplots")

        # Loop through layers in layerdict
        for sample_number, sample_data in self.progressbar(
                                              self.sample_data.items(),
                                              total=len(self.sample_data),
                                              desc="Overall",
                                              disable=self.quiet):
            # Plot all layers in the sample
            self._layers_to_3dplot_interactive(sample_data,
                                               f"{output_path}/" +
                                               f"{sample_number}",
                                               plot_w=plot_w,
                                               downsampling=downsampling,
                                               sliceable=sliceable,
                                               plotparams=plotparams)

        self._qprint("Sample interactive 3dplots complete!\n")

    def temp_data_to_csv(self, output_path: str,
                         layers: bool = True,
                         samples: bool = True,
                         confidence_interval: float = 0.95):
        "Generates a csv containing temperature data for processed samples"
        if output_path[-1] != "/":
            output_path += "/"
        if layers:
            layers_output_path = f"{output_path}layertemps.csv"
        if samples:
            samples_output_path = f"{output_path}sampletemps.csv"
        Path(output_path).mkdir(parents=True, exist_ok=True)
        self._qprint(f"Generating datasheets at {output_path}...")
        # Save sample temp data to a csv file (may have to make function later)
        with open(f"{layers_output_path}", "w") as lfile, \
             open(f"{samples_output_path}", "w") as sfile:
            # Add a header column
            lfile.write("SAMPLE, LAYER, AVG_TEMP, MIN_TEMP, MAX_TEMP, STDEV, STDERR, CI_MIN, CI_MAX\n")  # noqa
            sfile.write("SAMPLE, AVG_TEMP, MIN_TEMP, MAX_TEMP, STDEV, STDERR, CI_MIN, CI_MAX\n")  # noqa
            # loop through data array to generate csv
            for sample_number, sample_dict in self.progressbar(
                                                  self.sample_data.items(),
                                                  total=len(self.sample_data),
                                                  desc="Samples",
                                                  disable=self.quiet):
                temps_flat = np.array([])
                for layer_number, layer_array in self.progressbar(
                                                     sample_dict.items(),
                                                     total=len(sample_dict),
                                                     desc="Layers",
                                                     disable=self.quiet,
                                                     leave=False):
                    layer_temps = layer_array[2, :]
                    # Calc avg, stdev, stderr and confidence intervals
                    layer_avg = np.mean(layer_temps)
                    layer_min = np.min(layer_temps)
                    layer_max = np.max(layer_temps)
                    layer_stdev = np.std(layer_temps)
                    # Unsure of proper degrees of freedom here so guessing its
                    #   the standard "dof=n-1"?
                    layer_stderr = st.sem(layer_temps, ddof=layer_temps.size-1)
                    layer_conf = st.t.interval(confidence_interval,
                                               layer_temps.size-1,
                                               loc=layer_avg,
                                               scale=layer_stderr)
                    # Write layer data to file
                    lfile.write(f"{sample_number}, {layer_number}, {layer_avg}, {layer_min}, {layer_max}, {layer_stdev}, {layer_stderr}, {layer_conf[0]}, {layer_conf[1]}\n")  # noqa
                    temps_flat = np.append(temps_flat, layer_temps)
                # Calc avg, stdev, stderr and confidence intervals
                sample_avg = np.mean(temps_flat)
                sample_min = np.min(temps_flat)
                sample_max = np.max(temps_flat)
                sample_stdev = np.std(temps_flat)
                # Unsure of proper degrees of freedom here so guessing its
                #   the standard "dof=n-1"?
                sample_stderr = st.sem(temps_flat, ddof=temps_flat.size-1)
                sample_conf = st.t.interval(confidence_interval,
                                            temps_flat.size-1,
                                            loc=sample_avg,
                                            scale=sample_stderr)
                # Write sample overall data to file
                sfile.write(f"{sample_number}, {sample_avg}, {sample_min}, {sample_max}, {sample_stdev}, {sample_stderr}, {sample_conf[0]}, {sample_conf[1]}\n")  # noqa

        self._qprint(f"Datasheets generated at {output_path}!")
