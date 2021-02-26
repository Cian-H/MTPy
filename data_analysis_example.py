#!/usr/bin/env python
# encoding: utf-8

from mtpy import MeltpoolTomography

# —— Initialise data processing object ————————————————————————————————————————

# path to location with datafiles
dir_path = "~/test_data/layer"
# Folders in which to output figures
output_path = "~/test_data/OUTPUT"
layer_subfolder = "Layers"
sample_subfolder = "Samples"
mpt = MeltpoolTomography(data_path=dir_path)

# —— Set processing parameters ————————————————————————————————————————————————
# All changeable params are grouped up here for neatness and clarity.
#   In the future, a lot of this stuff could be automated out or GUI-ified

# Number of samples expected
n_samples = 81
# kwargs for thresholding
avgspeed_thresh_kwargs = {"threshold_percent": 2.5,
                          "avgof": 40}
# Note: the avgz_threshold function this kwarg dict is destined for isnt
#   specific to temperature, its generalised. In this case, we want to keep
#   anything greater than a certain threshold, so we're just passing the
#   "greater than" function (op.gt) as out comparison_func
avgtemp_thresh_kwargs = {"threshold_percent": 92.5}
# Prepare tuples with thresholding functions and kwargs
# IMPORTANT NOTE: When using functions in this module DO NOT SPLAT KWARGS!
#   The module has had to make use of several subfunctions to which we
#   might want to pass kwargs so some functions need multiple kwarg dicts.
#   Therefore, for consistency, i decided all kwargs passed should stay as
#   encapsulated dicts and not be splatted
thresh_functions = (mpt.avgspeed_threshold, mpt.avgz_greaterthan)
thresh_kwargs = (avgspeed_thresh_kwargs, avgtemp_thresh_kwargs)
# Set mode for clustering function
cluster_mode = "KMeans"
# Parameters for figures, scatter plots and interactive plots
# This gets passed to matplotlib.pyplot.figure
figureparams = {"figsize": (15, 15),
                "facecolor": "white"}
# This gets passed to matplotlib.pyplot.scatter
scatterparams = {"cmap": "jet"}
# This gets passed to plotly.express.scatter_3d
interactiveparams = {"color_continuous_scale": "Jet",
                     "range_z": [-1, 5]}
# Header of the z (temperature) column in the datafiles
temp_header = "temp"
# amount of downsampling for interactive plots
downsampling_layers = 10
downsampling_samples = 1

# —— Function calls for processing ————————————————————————————————————————————

# Read the data files at dir_path
data_dict = mpt.read_layers()

# Threshold data based on speed and temperature
mpt.threshold_all_layers(thresh_functions, thresh_kwargs)

mpt.detect_samples(81)  # detect contiguous samples
mpt.separate_samples()  # Separate detected samples into individual pointclouds

# Save thresholded layers to figures
mpt.layers_to_figures(f"{output_path}/{layer_subfolder}",
                      plot_z=True,
                      colorbar=True,
                      figureparams=figureparams,
                      scatterparams=scatterparams)

# Create figures for every layer of every individual sample
mpt.samples_to_figures(f"{output_path}/{sample_subfolder}",
                       plot_z=True,
                       colorbar=True,
                       figureparams=figureparams,
                       scatterparams=scatterparams)

# Create static 3d plot for entire build tray
mpt.layers_to_3dplot(f"{output_path}/{layer_subfolder}",
                     plot_w=True,
                     colorbar=True,
                     figureparams=figureparams,
                     plotparams=scatterparams)

# Create static 3d plot for each individual sample
mpt.samples_to_3dplots(f"{output_path}/{sample_subfolder}",
                       plot_w=True,
                       colorbar=True,
                       figureparams=figureparams,
                       plotparams=scatterparams)

# Create interactive 3d plot for entire build tray
mpt.layers_to_3dplot_interactive(f"{output_path}/{layer_subfolder}",
                                 plot_w=True,
                                 downsampling=downsampling_layers,
                                 plotparams=interactiveparams,
                                 sliceable=True)

# Create interactive 3d plot for each individual sample
mpt.samples_to_3dplots_interactive(f"{output_path}/{sample_subfolder}",
                                   plot_w=True,
                                   downsampling=downsampling_samples,
                                   plotparams=interactiveparams,
                                   sliceable=True)

mpt.temp_data_to_csv(f"{output_path}/temp_data.csv")

print("Script complete!")
