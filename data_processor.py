#!/usr/bin/env python
# -*- coding: utf-8 -*-

from data_loader import DataLoader
import numpy as np
from tqdm.auto import tqdm
from types import FunctionType
import operator as op

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

clusterfunc_dispatcher = {func.__name__: func for
                          func in clusterfunc_dispatcher}


class DataProcessor(DataLoader):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # modifiable in case needed in future
        self.z_header = "temp"

    # Thresholds data (x,y or x,y,z) based on percentage of max average slope
    #   of displacement
    def avgspeed_threshold(self, x, y, z, threshold_percent=1, avgof=1):
        self._qprint(f"Thresholding data by rolling avg speed (n={avgof}, cutoff={threshold_percent}%)...") # noqa
        threshold_percent /= 100.  # convert threshold percent to decimal
        # calc displacements using pythagorean theorem
        self._qprint("Calculating point displacements")
        displacement = np.sqrt(np.add(np.square(x), np.square(y)))

        self._qprint("Calculating rolling averages")
        # Calculate rolling average of displacement
        rollingavgdisp = []
        for start, end in tqdm(zip(range(displacement.size - avgof),
                               range(avgof, displacement.size)),
                               disable=self.quiet):
            rollingavgdisp.append(np.mean(displacement[start:end]))
        rollingavgdisp = np.asarray(rollingavgdisp)

        self._qprint("Calculating absolute rolling average speeds")
        # get absolute average speed based on rolling avg displacement
        absavgdispslope = np.abs(np.diff(rollingavgdisp))
        self._qprint("Eliminating points below threshold")
        threshold = threshold_percent * np.max(absavgdispslope)  # thresh val
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

    # Selectively keeps data based on comparison with a percentage of the mean
    #   of whatever z data is given
    def avgz_threshold(self, x, y, z, threshold_percent=1,
                       comparison_func=None):
        self._qprint(f"Thresholding data by z based on {comparison_func.__name__} (cutoff={threshold_percent}%)...") # noqa
        threshold_percent /= 100  # convert threshold percent to decimal
        threshold = threshold_percent * np.mean(z)  # threshold val
        # filter based on threshold criteria
        x_thresh = x[comparison_func(z, threshold)]
        y_thresh = y[comparison_func(z, threshold)]
        z_thresh = z[comparison_func(z, threshold)]
        # Return thresholded data
        return x_thresh, y_thresh, z_thresh

    def avgz_greaterthan(self, x, y, z, threshold_percent=1):
        return self.avgz_threshold(x, y, z,
                                   threshold_percent=threshold_percent,
                                   comparison_func=op.gt)

    def avgz_lessthan(self, x, y, z, threshold_percent=1):
        return self.avgz_threshold(x, y, z,
                                   threshold_percent=threshold_percent,
                                   comparison_func=op.lt)

    def threshold_all_layers(self, thresh_functions, threshfunc_kwargs):
        # if conversions to dict is needed for single function, then convert
        if type(thresh_functions) is FunctionType:
            thresh_functions = (thresh_functions,)
        if type(threshfunc_kwargs) is dict:
            threshfunc_kwargs = (threshfunc_kwargs,)

        self._qprint("\nThresholding all layers")

        # Dict to hold output data
        thresholded_data_layers = {}
        # Loop through dict, applying thresh_func to each layer
        for layer_number, layer_data in tqdm(self.data_dict.items(),
                                             total=len(self.data_dict),
                                             disable=self.quiet):
            # apply each requested thresholding function in sequence
            for thresh_function, kwargs in zip(thresh_functions,
                                               threshfunc_kwargs):

                thresholded_data_layers[layer_number] = \
                    np.asarray(
                        thresh_function(layer_data[:, 0],
                                        layer_data[:, 1],
                                        layer_data[:, 2],
                                        **kwargs))

        self.data_dict = thresholded_data_layers

    # Takes data and creates dict of each layer (layer num = key)
    #   with first index of tuple being 2d array of layer data and
    #   second index being cluster numbers. Also returns
    #   array for adding labels to layer plots as second output if requested
    def detect_samples(self, n_samples,
                       label_samples: bool = True,
                       mode="KMeans"):
        self._qprint("\nDetecting contiguous samples\n")
        # Concatenate x and y arrays into 2d array for training
        cluster_training = np.concatenate(tuple(self.data_dict.values()),
                                          axis=1)[:2, :]
        cluster_training = cluster_training.T

        # Set clustering function
        clusterfunc = clusterfunc_dispatcher[mode]

        # KMeans train to recognize clusters
        self.model = clusterfunc(n_clusters=n_samples,
                                 verbose=1*(not self.quiet))
        self.model.fit(cluster_training)

        self._qprint("\nLabelling contiguous samples")
        # loop through layers clustering xy data points
        clustered_layer_data = {}
        for layer_number, layer_data in tqdm(self.data_dict.items(),
                                             total=len(self.data_dict),
                                             disable=self.quiet):
            layer_xy = layer_data[:2, :]
            clusters = self.model.predict(layer_xy.T)
            clustered_layer_data[layer_number] = (layer_data, clusters)

        if label_samples is True:
            self.sample_labels = self.model.cluster_centers_

        self.clustered_layer_data = clustered_layer_data

    # takes a dataset as returned by detect_samples and separates the samples
    #   into a dict by cluster number. Samples are stored as dicts of layers,
    #   where layers are dfs (as is done with whole layers in other functions)
    def separate_samples(self):
        self._qprint("\nSeparating samples into different datasets")
        sample_data = {}
        for layer_number, layer_data in tqdm(self.clustered_layer_data.items(),
                                             total=len(
                                                self.clustered_layer_data),
                                             desc="Overall",
                                             disable=self.quiet):
            for cluster_num in tqdm(set(layer_data[1]),
                                    desc=f"Layer {layer_number}",
                                    disable=self.quiet):
                # Filter cluster from data
                cluster = layer_data[0][:, layer_data[1] == cluster_num]
                # If key for cluster not in data dict create
                if cluster_num not in sample_data:
                    sample_data[cluster_num] = {}
                # Add layer to sample subdictionary with key layer_number
                sample_data[cluster_num][layer_number] = cluster

        self._qprint("")  # if not silent, add a line after progress bars

        self.sample_data = sample_data
