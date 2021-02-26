#!/usr/bin/env python
# encoding: utf-8

# "pyrometric_tomography" is dependent upon:
# - numpy
# - pandas
# - scikit-learn
# - matplotlib
# - plotly
# - tqdm

from mtpy import MeltpoolTomography
import numpy as np
import scipy.stats as st

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

print("Generating temp_data file")
# Save sample temp data to a csv file (may have to make function later)
with open(f"{output_path}/temp_data.csv", "w") as file:
    # Add a header column
    file.write("SAMPLE, LAYER, AVG_TEMP, MIN_TEMP, MAX_TEMP, STDEV, STDERR, CI_MIN, CI_MAX\n")  # noqa
    # loop through data array to generate csv
    for sample_number, sample_dict in mpt.sample_data.items():
        temps_flat = np.array([])
        for layer_number, layer_array in sample_dict.items():
            layer_temps = layer_array[2, :]
            # Calc avg, stdev, stderr and confidence intervals
            layer_avg = np.mean(layer_temps)
            layer_min = np.min(layer_temps)
            layer_max = np.max(layer_temps)
            layer_stdev = np.std(layer_temps)
            # Unsure of proper degrees of freedom here so guessing its
            #   the standard "dof=n-1"?
            layer_stderr = st.sem(layer_temps, ddof=layer_temps.size-1)
            layer_conf = st.t.interval(0.95,
                                       layer_temps.size-1,
                                       loc=layer_avg,
                                       scale=layer_stderr)
            # Write layer data to file
            file.write(f"{sample_number}, {layer_number}, {layer_avg}, {layer_min}, {layer_max}, {layer_stdev}, {layer_stderr}, {layer_conf[0]}, {layer_conf[1]}\n")  # noqa
            temps_flat = np.append(temps_flat, layer_temps)
        # Calc avg, stdev, stderr and confidence intervals
        sample_avg = np.mean(temps_flat)
        sample_min = np.min(temps_flat)
        sample_max = np.max(temps_flat)
        sample_stdev = np.std(temps_flat)
        # Unsure of proper degrees of freedom here so guessing its
        #   the standard "dof=n-1"?
        sample_stderr = st.sem(temps_flat, ddof=temps_flat.size-1)
        sample_conf = st.t.interval(0.95,
                                    temps_flat.size-1,
                                    loc=sample_avg,
                                    scale=sample_stderr)
        # Write sample overall data to file
        file.write(f"{sample_number}, OVERALL, {sample_avg}, {sample_min}, {sample_max}, {sample_stdev}, {sample_stderr}, {sample_conf[0]}, {sample_conf[1]}\n")  # noqa

print("Script complete!")
