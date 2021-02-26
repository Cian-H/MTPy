#!/usr/bin/env python
# -*- coding: utf-8 -*-

from data_processor import DataProcessor
import os
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from mpl_toolkits import mplot3d  # noqa
from plotly import express as px
from tqdm.auto import tqdm

# This piece of init code prevents a warning resulting from generation of
#   many matplotlib "figure" objects. This is unimportant on my current
#   computer as i have plenty of RAM but if becomes an issue in future may need
#   to write a singleton wrapper object for plt.figure
plt.rcParams.update({"figure.max_open_warning": 0})


class MeltpoolTomography(DataProcessor):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _prep_path(self, output_path):
        """Checks if paths exist and creates them if they dont"""
        try:
            os.makedirs(f"{output_path}")
        except OSError as e:
            if e.errno == 17:
                self._qprint(f"Directory {output_path} already exists!")
            else:
                raise e

    # takes a collection of complete layers and plots figures from them at the
    #   target filepath
    def _layers_to_figures(self, layers, output_path, filetype="png",
                           plot_z=False, colorbar=False,
                           figureparams={}, scatterparams={}):

        self._qprint(
            f"\nPreparing to generate layer plots in {output_path}...")

        self._prep_path(output_path)

        self._qprint("\nGenerating layer plots")
        # Create figure
        plt.figure(**figureparams)
        # Loop through layers
        for layer_number, layer_data in tqdm(layers.items(), total=len(layers),
                                             disable=self.quiet):
            # If plotting z or averaging z assign variable
            if plot_z:
                z = layer_data[2, :]
            else:
                z = None
            # Create figure and scatter plot
            plt.scatter(layer_data[0, :], layer_data[1, :],
                        c=z, **scatterparams)
            # If we want a colorbar create one
            if colorbar and plot_z:
                plt.colorbar()
            # If labels are given, plot them
            if self.sample_labels is not None:
                for i, xy in enumerate(self.sample_labels):
                    plt.annotate(str(i), xy)
            # Save figure and clear pyplot buffer
            plt.savefig(f"{output_path}/{layer_number}.{filetype}")
            plt.clf()

        self._qprint("Layer plots complete!\n")

    def layers_to_figures(self, output_path, **kwargs):
        self._layers_to_figures(self.data_dict, output_path, **kwargs)

    # takes a dictionary of samples (such as returned by the function
    #   separate_samples) and plots figures from them at the target filepath
    def samples_to_figures(self, output_path, filetype="png",
                           plot_z=False, colorbar=False, figureparams={},
                           scatterparams={}):

        self._qprint(
            f"\nPreparing to generate sample plots in {output_path}...")

        self._prep_path(output_path)

        self._qprint("\nGenerating sample plots")

        # Loop through layers in layerdict
        for sample_number, sample_data in tqdm(self.sample_data.items(),
                                               total=len(self.sample_data),
                                               desc="Overall",
                                               disable=self.quiet):
            # Plot all layers in the sample
            self._layers_to_figures(sample_data,
                                    f"{output_path}/{sample_number}",
                                    plot_z=plot_z,
                                    colorbar=colorbar,
                                    figureparams=figureparams,
                                    scatterparams=scatterparams)

        self._qprint("Sample plots complete!\n")

    # takes a collection of complete layers and plots figures from them at the
    #   target filepath. z values can be given or generated based on z_range
    #   (assuming equal layer spacing). Otherwise, z values should be given
    #   as an array of heights above zero for each layer
    def _layers_to_3dplot(self, layers, output_path, filetype="png",
                          z_range=None, z=None,
                          plot_w=False, colorbar=False,
                          figureparams={}, plotparams={}):

        self._qprint(f"\nPreparing to generate 3dplot in {output_path}...")

        self._prep_path(output_path)

        # Create z values assuming equal layer height if none given
        if z is None:
            if z_range is None:
                z = range(len(layers))
            else:
                increment = (z_range[1] - z_range[0]) / len(layers)
                z = np.arange(z_range[0], z_range[1] + increment,
                              increment)

        self._qprint("Preparing plot pointcloud")
        # Create full array of z values
        plotarray = []
        for (layer_number, layer_data), z_value in tqdm(zip(layers.items(), z),
                                                        total=len(layers),
                                                        disable=self.quiet):
            # prepare to generate numpy array of x, y, z values & w if present
            newlayer = [layer_data[:2, :],
                        np.repeat(z[layer_number], layer_data.shape[1])]
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
            plt.colorbar(p)
        # Save figure and clear pyplot buffer
        plt.savefig(f"{output_path}/3dplot.{filetype}")
        plt.clf()

        self._qprint("3dplot complete!\n")

    def layers_to_3dplot(self, output_path, **kwargs):
        self._layers_to_3dplot(self.data_dict, output_path, **kwargs)

    # Does same as layers_to_3dplots but for each individual sample instead of
    #   entire layer
    def samples_to_3dplots(self, output_path, filetype="png",
                           z_range=None, z=None, plot_w=False, colorbar=False,
                           figureparams={}, plotparams={}):
        self._qprint(
            f"\nPreparing to generate sample 3dplots in {output_path}...")

        self._prep_path(output_path)

        self._qprint("\nGenerating sample 3dplots")

        # Create z values assuming equal layer height if none given
        if z is None:
            if z_range is None:
                z = range(len(self.data_dict))
            else:
                increment = (z_range[1] - z_range[0]) / len(self.data_dict)
                z = np.arange(z_range[0], z_range[1] + increment,
                              increment)

        # Loop through layers in layerdict
        for sample_number, sample_data in tqdm(self.sample_data.items(),
                                               total=len(self.sample_data),
                                               desc="Overall",
                                               disable=self.quiet):
            # Plot all layers in the sample
            self._layers_to_3dplot(sample_data,
                                   f"{output_path}/{sample_number}",
                                   plot_w=plot_w,
                                   colorbar=colorbar,
                                   z=z,
                                   figureparams=figureparams,
                                   plotparams=plotparams)

        self._qprint("Sample 3dplots complete!\n")

    # Does same as layer_to_3d_plot but produces an interactive figure
    # NOTE: Downsampling may be necessary here as plotly struggles to display
    #       more than 4 million points
    def _layers_to_3dplot_interactive(self, layers, output_path, z_range=None,
                                      z=None, plot_w=False, downsampling=1,
                                      sliceable=False, plotparams={}):

        self._qprint(
            f"\nPreparing to generate 3dplot_interactive in {output_path}...")

        self._prep_path(output_path)

        # Create z values assuming equal layer height if none given
        if z is None:
            if z_range is None:
                z = range(len(layers))
            else:
                increment = (z_range[1] - z_range[0]) / len(layers)
                z = np.arange(z_range[0], z_range[1] + increment,
                              increment)

        self._qprint("Preparing plot pointcloud")
        # Create full array of z values
        plotarray = []
        for (layer_number, layer_data), z_value in tqdm(zip(layers.items(), z),
                                                        total=len(layers),
                                                        disable=self.quiet):
            # prepare to generate numpy array of x, y, z values & w if present
            newlayer = [layer_data[:2, :],
                        np.repeat(z[layer_number], layer_data.shape[1])]
            if layer_data.shape[0] == 3:
                newlayer.append(layer_data[2, :])
            plotarray.append(np.vstack(newlayer))
        plotarray = np.concatenate(plotarray, axis=1)
        plotarray = plotarray.T

        self._qprint("\nGenerating 3dplot_interactive")

        df = pd.DataFrame(data={"x": plotarray[::downsampling, 0],
                                "y": plotarray[::downsampling, 1],
                                "z": plotarray[::downsampling, 2],
                                })

        # If plotting a 4th dimension, add column for w
        if plot_w:
            df["w"] = plotarray[::downsampling, 3]
            plotparams["color"] = "w"

        # Finally, add indeces (n) for data points
        # NOTE: may add functionality for additional data in
        #       plotly tooltip bubble here later
        df["n"] = range(0, plotarray[:, 0].size, downsampling)

        # Create column for animation slider
        if sliceable:
            # Get all z values
            layer_values = sorted(set(df["z"]))
            unfiltered_dataframes = [df.copy() for i in layer_values]
            filtered_dataframes = []
            # Create multiple version of dataset corresponding to different
            # frames
            for top_layer, dataframe in zip(layer_values,
                                            unfiltered_dataframes):
                filtered_dataframes.append(df.loc[df["z"] <= top_layer].copy())
            # Then add columns denoting frame numbers
            for dataframe in filtered_dataframes:
                dataframe["Top Layer"] = dataframe["z"].max()
            # Combine frames into new dataset
            df = pd.concat(filtered_dataframes)
            # Finally, add params for animation
            plotparams["animation_frame"] = "Top Layer"

        # Create figure and save to html
        fig = px.scatter_3d(df, x="x", y="y", z="z",
                            hover_data="n", **plotparams)
        fig.write_html(f"{output_path}/3dplot_interactive.html")

        self._qprint("3dplot_interactive complete!\n")

    def layers_to_3dplot_interactive(self, output_path, **kwargs):
        self._layers_to_3dplot_interactive(self.data_dict, output_path,
                                           **kwargs)

    # Does same as samples_to_3d_plot but produces an interactive figure
    def samples_to_3dplots_interactive(self, output_path,
                                       z_range=None, z=None, plot_w=False,
                                       downsampling=1, sliceable=False,
                                       plotparams={}):
        self._qprint(f"\nPreparing to generate sample interactive 3dplots in {output_path}...")  # noqa

        self._prep_path(output_path)

        self._qprint("\nGenerating sample interactive 3dplots")

        # Loop through layers in layerdict
        for sample_number, sample_data in tqdm(self.sample_data.items(),
                                               total=len(self.sample_data),
                                               desc="Overall",
                                               disable=self.quiet):
            # Plot all layers in the sample
            self._layers_to_3dplot_interactive(sample_data,
                                               f"{output_path}/" +
                                               f"{sample_number}",
                                               z_range=z_range,
                                               z=z,
                                               plot_w=plot_w,
                                               downsampling=downsampling,
                                               sliceable=sliceable,
                                               plotparams=plotparams)

        self._qprint("Sample interactive 3dplots complete!\n")
