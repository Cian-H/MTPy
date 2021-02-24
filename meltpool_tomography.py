#!/usr/bin/env python
# coding: utf-8

from pathlib import Path
import os
import numpy as np
import pandas as pd
from types import FunctionType
from matplotlib import pyplot as plt
from mpl_toolkits import mplot3d  # noqa
from plotly import express as px
from tqdm import tqdm

# Cluster function imports and dispatcher (allows for easy switching
#   of clustering function)
clusterfunc_dispatcher = []

# import KMeans and minibatch variant from scikit-learn
#   CPU bound. Minibatch is significantly faster but more error-prone
try:
    from sklearn.cluster import KMeans
    from sklearn.cluster import MiniBatchKMeans as KMeans_MB
    clusterfunc_dispatcher += [KMeans, KMeans_MB]
except ImportError:
    print("Optional module Scikit-Learn not present")
# A custom wrapper for TensorFlow KMeans function that matches sklearn api
#    GPU bound if available.
try:
    from kmeans_tf import KMeans_TF
    clusterfunc_dispatcher.append(KMeans_TF)
except ImportError:
    print("Optional module TensorFlow not present")

clusterfunc_dispatcher = {func.__name__: func for
                          func in clusterfunc_dispatcher}

# This piece of init code prevents a warning resulting from generation of
#   many matplotlib "figure" objects. This is unimportant on my current
#   computer as i have plenty of RAM but if becomes an issue in future may need
#   to write a singleton wrapper object for plt.figure
plt.rcParams.update({'figure.max_open_warning': 0})

# %% Define functions #########################################################


# Helper function: silencable print, for code clarity
def qprint(string_to_print, quiet=False):
    if not quiet:
        print(string_to_print)


# Function that reads layer files into dict of dataframes
def read_layers(dir_path, quiet=True):
    qprint(f"\nSearching for files at {dir_path}", quiet)
    # glob filenames
    pathlist = Path(dir_path).glob("*.pcd")
    data_dict = {}
    files = []

    for path in pathlist:
        path_in_str = str(path)
        file = path_in_str.split("/")[-1:][0]
        files.append(file)

    files = sorted(files)

    qprint(f"Reading files from {dir_path}", quiet)
    # add end slash if not present
    if dir_path[-1] != "/":
        dir_path += "/"
    # Read data from files
    for idx, file in tqdm(enumerate(files), total=len(files),
                          disable=quiet):
        try:
            df = pd.read_csv(dir_path + file,
                             names=["x", "y", "temp", "temp_duplicate"],
                             header=None, delimiter=" ")

            df.drop(["temp_duplicate"], axis=1, inplace=True)
            df = df.groupby(["x", "y"], sort=False, as_index=False).mean()
            # Corrects for flipped x axis on aconity output
            df["x"] *= -1
            data_dict[idx] = df
        except:  # noqa
            qprint(f"File {file} not found!", quiet)

    return data_dict


# Thresholds data (x,y or x,y,z) based on percentage of max average slope
#   of displacement
def avgspeed_threshold(x, y, z=None, threshold_percent=1, avgof=1,
                       quiet=True):
    qprint(f"Thresholding data by rolling avg speed (n={avgof}, cutoff={threshold_percent}%)...", quiet) # noqa
    threshold_percent /= 100  # convert threshold percent to decimal
    # calc displacements using pythagorean theorem
    qprint("Calculating point displacements", quiet)
    displacement = np.sqrt(np.add(np.square(x), np.square(y)))

    qprint("Calculating rolling averages", quiet)
    # Calculate rolling average of displacement
    rollingavgdisp = []
    for start, end in tqdm(zip(range(displacement.size - avgof),
                           range(avgof, displacement.size)),
                           disable=quiet):
        rollingavgdisp.append(np.mean(displacement[start:end]))
    rollingavgdisp = np.asarray(rollingavgdisp)

    qprint("Calculating absolute rolling average speeds", quiet)
    # get absolute average speed based on rolling avg displacement
    absavgdispslope = np.abs(np.diff(rollingavgdisp))
    qprint("Eliminating points below threshold", quiet)
    threshold = threshold_percent * np.max(absavgdispslope)  # threshold val
    # mask out points without enough predecessors for rolling avg
    xmasked, ymasked = x[-absavgdispslope.size:], y[-absavgdispslope.size:]
    # filter based on threshold criteria
    x_thresh = xmasked[absavgdispslope < threshold]
    y_thresh = ymasked[absavgdispslope < threshold]
    # return thresholded x,y or x,y,z depending on input
    if z is None:
        return x_thresh, y_thresh
    else:
        zmasked = z[-absavgdispslope.size:]
        z_thresh = zmasked[absavgdispslope < threshold]
        return x_thresh, y_thresh, z_thresh


# Selectively keeps data based on comparison with a percentage of the mean of
#   whatever z data is given
def avgz_threshold(x, y, z, threshold_percent=1, comparison_func=None,
                   quiet=True):
    qprint(f"Thresholding data by temperature (cutoff={threshold_percent}%)...", quiet) # noqa
    threshold_percent /= 100  # convert threshold percent to decimal
    threshold = threshold_percent * np.mean(z)  # threshold val
    # filter based on threshold criteria
    x_thresh = x[comparison_func(z, threshold)]
    y_thresh = y[comparison_func(z, threshold)]
    z_thresh = z[comparison_func(z, threshold)]
    # Return thresholded data
    return x_thresh, y_thresh, z_thresh


def threshold_all_layers(data_dict, thresh_functions, threshfunc_kwargs,
                         z_header=None, quiet=True):
    # if conversions are needed for single function convert
    if type(thresh_functions) is FunctionType:
        thresh_functions = (thresh_functions,)
    if type(threshfunc_kwargs) is dict:
        threshfunc_kwargs = (threshfunc_kwargs,)

    qprint("\nThresholding all layers", quiet)
    data_layers = {}
    for layer_number, layer_data in data_dict.items():
        data_layers[layer_number] = []
        data_layers[layer_number].append(layer_data["x"].values)
        data_layers[layer_number].append(layer_data["y"].values)
        if z_header is not None:
            data_layers[layer_number].append(layer_data[z_header].values)
    # Dict to hold output data
    thresholded_data_layers = {}
    # Loop through dict, applying thresh_func to each layer
    for layer_number, layer_data in tqdm(data_layers.items(),
                                         total=len(data_layers),
                                         disable=quiet):
        # apply each requested thresholding function in sequence
        for thresh_function, kwargs in zip(thresh_functions,
                                           threshfunc_kwargs):
            if z_header is None:
                z = None
            else:
                z = layer_data[2]

            thresholded_data_layers[layer_number] = \
                np.asarray(
                    thresh_function(layer_data[0], layer_data[1], z, **kwargs))

    return thresholded_data_layers


# Takes data and creates dict of each layer (layer num = key)
#   with first index of tuple being 2d array of layer data and
#   second index being cluster numbers. Also returns
#   array for adding labels to layer plots as second output if requested
def detect_samples(layers, n_samples, return_labels=False, mode="kmeans",
                   quiet=True):
    qprint("\nDetecting contiguous samples\n", quiet)
    # Concatenate x and y arrays into 2d array for training
    cluster_training = np.concatenate(tuple(layers.values()), axis=1)[:2, :]
    cluster_training = cluster_training.T

    # Set clustering function
    clusterfunc = clusterfunc_dispatcher[mode]

    # KMeans train to recognize clusters
    model = clusterfunc(n_clusters=n_samples, verbose=1*(not quiet))
    model.fit(cluster_training)

    qprint("\nLabelling contiguous samples", quiet)
    # loop through layers clustering xy data points
    clustered_layer_data = {}
    for layer_number, layer_data in tqdm(layers.items(), total=len(layers),
                                         disable=quiet):
        layer_xy = layer_data[:2, :]
        clusters = model.predict(layer_xy.T)
        clustered_layer_data[layer_number] = (layer_data, clusters)

    if return_labels:
        return clustered_layer_data, model.cluster_centers_

    return clustered_layer_data


# takes a dataset as returned by detect_samples and separates the samples
#   into a dict by cluster number. Samples are stored as dicts of layers, where
#   layers are dataframes (as is done with whole layers in other functions)
def separate_samples(clustered_layer_data, quiet=True):
    qprint("\nSeparating samples into different datasets", quiet)
    sample_data = {}
    for layer_number, layer_data in tqdm(clustered_layer_data.items(),
                                         total=len(clustered_layer_data),
                                         desc="Overall",
                                         disable=quiet):
        for cluster_num in tqdm(set(layer_data[1]),
                                desc=f"Layer {layer_number}",
                                disable=quiet):
            # Filter cluster from data
            cluster = layer_data[0][:, layer_data[1] == cluster_num]
            # If key for cluster not in data dict create
            if cluster_num not in sample_data:
                sample_data[cluster_num] = {}
            # Add layer to sample subdictionary with key layer_number
            sample_data[cluster_num][layer_number] = cluster

    qprint("", quiet=quiet)  # if not silent, add a line after progress bars

    return sample_data


# takes a collection of complete layers and plots figures from them at the
#   target filepath
def layers_to_figures(layers, output_path, filetype="png", plot_z=False,
                      colorbar=False, labels=None,
                      figureparams={}, scatterparams={},
                      quiet=True):

    qprint(f"\nPreparing to generate layer plots in {output_path}...",
           quiet)
    # Create paths if dont exist
    try:
        os.makedirs(f"{output_path}")
    except OSError as e:
        if e.errno == 17:
            qprint(f"Directory {output_path} already exists!", quiet)
        else:
            raise e

    qprint("\nGenerating layer plots", quiet)
    # Create figure
    plt.figure(**figureparams)
    # Loop through layers
    for layer_number, layer_data in tqdm(layers.items(), total=len(layers),
                                         disable=quiet):
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
        if labels is not None:
            for i, xy in enumerate(labels):
                plt.annotate(str(i), xy)
        # Save figure and clear pyplot buffer
        plt.savefig(f"{output_path}/{layer_number}.{filetype}")
        plt.clf()

    qprint("Layer plots complete!\n", quiet)


# takes a dictionary of samples (such as returned by the function
#   separate_samples) and plots figures from them at the target filepath
def samples_to_figures(sample_dict, output_path, filetype="png", plot_z=False,
                       colorbar=False, figureparams={},
                       scatterparams={}, quiet=True):

    qprint(f"\nPreparing to generate sample plots in {output_path}...",
           quiet)
    # Create paths if dont exist
    try:
        os.makedirs(f"{output_path}")
    except OSError as e:
        if e.errno == 17:
            qprint(f"Directory {output_path} already exists!", quiet)
        else:
            raise e

    qprint("\nGenerating sample plots", quiet)

    # Loop through layers in layerdict
    for sample_number, sample_data in tqdm(sample_dict.items(),
                                           total=len(sample_dict),
                                           desc="Overall",
                                           disable=quiet):
        # Plot all layers in the sample
        layers_to_figures(sample_data,
                          f"{output_path}/{sample_number}",
                          plot_z=plot_z,
                          colorbar=colorbar,
                          figureparams=figureparams,
                          scatterparams=scatterparams,
                          quiet=True)

    qprint("Sample plots complete!\n", quiet)


# takes a collection of complete layers and plots figures from them at the
#   target filepath. z values can be given or generated based on z_range
#   (assuming equal layer spacing). Otherwise, z values should be given
#   as an array of heights above zero for each layer
def layers_to_3dplot(layers, output_path, filetype="png",
                     z_range=None, z=None,
                     plot_w=False, colorbar=False,
                     figureparams={}, plotparams={},
                     quiet=True):

    qprint(f"\nPreparing to generate 3dplot in {output_path}...",
           quiet)
    # Create paths if dont exist
    try:
        os.makedirs(f"{output_path}")
    except OSError as e:
        if e.errno == 17:
            qprint(f"Directory {output_path} already exists!", quiet)
        else:
            raise e

    # Create z values assuming equal layer height if none given
    if z is None:
        if z_range is None:
            z = range(len(layers))
        else:
            increment = (z_range[1] - z_range[0]) / len(layers)
            z = np.arange(z_range[0], z_range[1] + increment,
                          increment)

    qprint("Preparing plot pointcloud", quiet)
    # Create full array of z values
    plotarray = []
    for (layer_number, layer_data), z_value in tqdm(zip(layers.items(), z),
                                                    total=len(layers),
                                                    disable=quiet):
        # prepare to generate numpy array of x, y, z values and w if present
        newlayer = [layer_data[:2, :],
                    np.repeat(z[layer_number], layer_data.shape[1])]
        if layer_data.shape[0] == 3:
            newlayer.append(layer_data[2, :])
        plotarray.append(np.vstack(newlayer))
    plotarray = np.concatenate(plotarray, axis=1)
    plotarray = plotarray.T

    qprint("\nGenerating 3dplots", quiet)
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

    qprint("3dplot complete!\n", quiet)


# Does same as layers_to_3dplots but for each individual sample instead of
#   entire layer
def samples_to_3dplots(sample_dict, output_path, filetype="png", z_range=None,
                       z=None, plot_w=False, colorbar=False,
                       figureparams={}, plotparams={},
                       quiet=True):
    qprint(f"\nPreparing to generate sample 3dplots in {output_path}...",
           quiet)
    # Create paths if dont exist
    try:
        os.makedirs(f"{output_path}")
    except OSError as e:
        if e.errno == 17:
            qprint(f"Directory {output_path} already exists!", quiet)
        else:
            raise e

    qprint("\nGenerating sample 3dplots", quiet)

    # Loop through layers in layerdict
    for sample_number, sample_data in tqdm(sample_dict.items(),
                                           total=len(sample_dict),
                                           desc="Overall",
                                           disable=quiet):
        # Plot all layers in the sample
        layers_to_3dplot(sample_data,
                         f"{output_path}/{sample_number}",
                         plot_w=plot_w,
                         colorbar=colorbar,
                         figureparams=figureparams,
                         plotparams=plotparams,
                         quiet=True)

    qprint("Sample 3dplots complete!\n", quiet)


# Does same as layer_to_3d_plot but produces an interactive figure
# NOTE: Downsampling may be necessary here as plotly struggles to display
#       more than 4 million points
def layers_to_3dplot_interactive(layers, output_path, z_range=None, z=None,
                                 plot_w=False, downsampling=1, sliceable=False,
                                 plotparams={},
                                 quiet=True):

    qprint(f"\nPreparing to generate 3dplot_interactive in {output_path}...",
           quiet)
    # Create paths if dont exist
    try:
        os.makedirs(f"{output_path}")
    except OSError as e:
        if e.errno == 17:
            qprint(f"Directory {output_path} already exists!", quiet)
        else:
            raise e

    # Create z values assuming equal layer height if none given
    if z is None:
        if z_range is None:
            z = range(len(layers))
        else:
            increment = (z_range[1] - z_range[0]) / len(layers)
            z = np.arange(z_range[0], z_range[1] + increment,
                          increment)

    qprint("Preparing plot pointcloud", quiet)
    # Create full array of z values
    plotarray = []
    for (layer_number, layer_data), z_value in tqdm(zip(layers.items(), z),
                                                    total=len(layers),
                                                    disable=quiet):
        # prepare to generate numpy array of x, y, z values and w if present
        newlayer = [layer_data[:2, :],
                    np.repeat(z[layer_number], layer_data.shape[1])]
        if layer_data.shape[0] == 3:
            newlayer.append(layer_data[2, :])
        plotarray.append(np.vstack(newlayer))
    plotarray = np.concatenate(plotarray, axis=1)
    plotarray = plotarray.T

    qprint("\nGenerating 3dplot_interactive", quiet)

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
        # Create multiple version of dataset corresponding to different frames
        for top_layer, dataframe in zip(layer_values, unfiltered_dataframes):
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

    qprint("3dplot_interactive complete!\n", quiet)


# Does same as samples_to_3d_plot but produces an interactive figure
def samples_to_3dplots_interactive(sample_dict, output_path, z_range=None,
                                   z=None, plot_w=False, downsampling=1,
                                   sliceable=False, plotparams={},
                                   quiet=True):
    qprint(f"\nPreparing to generate sample interactive 3dplots in {output_path}...",  # noqa
           quiet)
    # Create paths if dont exist
    try:
        os.makedirs(f"{output_path}")
    except OSError as e:
        if e.errno == 17:
            qprint(f"Directory {output_path} already exists!", quiet)
        else:
            raise e

    qprint("\nGenerating sample interactive 3dplots", quiet)

    # Loop through layers in layerdict
    for sample_number, sample_data in tqdm(sample_dict.items(),
                                           total=len(sample_dict),
                                           desc="Overall",
                                           disable=quiet):
        # Plot all layers in the sample
        layers_to_3dplot_interactive(sample_data,
                                     f"{output_path}/{sample_number}",
                                     z_range=z_range,
                                     z=z,
                                     plot_w=plot_w,
                                     downsampling=downsampling,
                                     sliceable=sliceable,
                                     plotparams=plotparams,
                                     quiet=True)

    qprint("Sample interactive 3dplots complete!\n", quiet)
