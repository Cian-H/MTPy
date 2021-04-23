#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ..data.data_loader import DataLoader
import numpy as np
from tqdm.auto import tqdm
from types import FunctionType, MethodType
import operator as op

# Cluster function imports and dispatcher (allows for easy switching
#   of clustering function)
clusterfunc_dispatcher = []

# import KMeans and minibatch variant from scikit-learn
#   CPU bound. Minibatch is significantly faster but more error-prone
try:
    from sklearn.cluster import KMeans
    from sklearn.cluster import MiniBatchKMeans
    clusterfunc_dispatcher += [KMeans, MiniBatchKMeans]
except ImportError:
    print("Optional module Scikit-Learn not present")

clusterfunc_dispatcher = {func.__name__: func for
                          func in clusterfunc_dispatcher}


class DataProcessor(DataLoader):
    """
    DataLoader class for loading data into the MTPy Module

    Attributes
    ----------
        quiet: bool = False
            Determines whether object should be quiet or not
        data_path: str = None
            The path to the data to be processed

    Methods
    -------
        _qprint(string: str)
            Prints a line if self.quiet is False
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
        avgspeed_threshold(x, y, w, threshold_percent=1, avgof=1)
            Thresholds data (x,y,w) based on percentage of max average slope
            of rolling average of displacement
        avgw_threshold(x, y, w, threshold_percent=1, comparison_func=None)
            Selectively keeps data based on comparison with a percentage of the
            mean of whatever w data is given
        avgw_greaterthan(x, y, w, threshold_percent=1)
            Keeps all values greater than threshold percent of average
        avgw_lessthan(x, y, w, threshold_percent=1)
            Keeps all values greater than threshold percent of average
        threshold_all_layers(thresh_functions, threshfunc_kwargs):
            Thresholds all layers by applying listed functions with listed
            params
        detect_samples(n_samples, label_samples: bool = True, mode="KMeans")
            Uses a clustering algorithm to detect samples automatically
        separate_samples()
            Separates labelled layer data into samples
    """

    def __init__(self, **kwargs):
        """
        Constructor for the MTPy DataProcessor Base class

        Parameters
        ----------
            quiet: bool = False
                Determines whether object should be quiet or not
            data_path: str = None
                The path to the data to be processed
        """
        super().__init__(**kwargs)

    def apply_calibration_curve(self, calibration_curve: FunctionType):
        "Applies calibration curve function to w axis (temp) data"
        self._qprint("Applying calibration curve")
        if self.data_dict is not None:
            for layer_num, layer_data in tqdm(self.data_dict.items(),
                                              total=len(self.data_dict),
                                              desc="Layers",
                                              disable=self.quiet):
                layer_data[2, :] = calibration_curve(layer_data[2, :])
        if self.sample_data is not None:
            for sample_num, layers in tqdm(self.sample_data.items(),
                                           total=len(self.sample_data),
                                           desc="Samples",
                                           disable=self.quiet):
                for layer_number, layer_data in layers.items():
                    layer_data[2, :] = calibration_curve(layer_data[2, :])

    def avgspeed_threshold(self, x, y, w, threshold_percent=1, avgof=1):
        """
        Thresholds layer data (x,y,w) based on percentage of max average slope
        of rolling average of displacement
        """
        threshold_percent /= 100.  # convert threshold percent to decimal
        # calc displacements using pythagorean theorem
        displacement = np.sqrt(np.add(np.square(x), np.square(y)))

        # Calculate rolling average of displacement
        rollingavgdisp = np.convolve(displacement,
                                     np.ones(avgof) / avgof,
                                     mode="valid")

        # get absolute average speed based on rolling avg displacement
        absavgdispslope = np.abs(np.diff(rollingavgdisp))
        threshold = threshold_percent * np.max(absavgdispslope)  # thresh val
        # mask out points without enough predecessors for rolling avg
        xmasked = x[-absavgdispslope.size:]
        ymasked = y[-absavgdispslope.size:]
        wmasked = w[-absavgdispslope.size:]
        # filter based on threshold criteria
        x_thresh = xmasked[absavgdispslope < threshold]
        y_thresh = ymasked[absavgdispslope < threshold]
        w_thresh = wmasked[absavgdispslope < threshold]
        return x_thresh, y_thresh, w_thresh

    def avgw_threshold(self, x, y, w, threshold_percent=1,
                       comparison_func=None):
        """
        Selectively keeps data based on comparison with a percentage of the
        mean of whatever w data is given
        """
        threshold_percent /= 100  # convert threshold percent to decimal
        threshold = threshold_percent * np.mean(w)  # threshold val
        # filter based on threshold criteria
        x_thresh = x[comparison_func(w, threshold)]
        y_thresh = y[comparison_func(w, threshold)]
        w_thresh = w[comparison_func(w, threshold)]
        # Return thresholded data
        return x_thresh, y_thresh, w_thresh

    def avgw_greaterthan(self, x, y, w, threshold_percent=1):
        "Keeps all values greater than threshold percent of average"
        return self.avgw_threshold(x, y, w,
                                   threshold_percent=threshold_percent,
                                   comparison_func=op.gt)

    def avgw_lessthan(self, x, y, w, threshold_percent=1):
        "Keeps all values less than threshold percent of average"
        return self.avgw_threshold(x, y, w,
                                   threshold_percent=threshold_percent,
                                   comparison_func=op.lt)

    def threshold_all_layers(self, thresh_functions, threshfunc_kwargs):
        "Thresholds all layers by applying listed functions with listed params"
        # if conversions to dict is needed for single function, then convert
        if type(thresh_functions) in (FunctionType, MethodType):
            thresh_functions = (thresh_functions,)
        if type(threshfunc_kwargs) is dict:
            threshfunc_kwargs = (threshfunc_kwargs,)

        self._qprint("\nThresholding all layers")

        # Loop through dict, applying thresh_func to each layer
        for layer_number, layer_data in tqdm(self.data_dict.items(),
                                             total=len(self.data_dict),
                                             desc="Layers",
                                             position=0,
                                             disable=self.quiet):
            # apply each requested thresholding function in sequence
            for thresh_function, kwargs in tqdm(zip(thresh_functions,
                                                    threshfunc_kwargs),
                                                total=len(thresh_functions),
                                                desc="Thresholds",
                                                position=1,
                                                leave=False,
                                                disable=self.quiet):

                self.data_dict[layer_number] = \
                    np.asarray(
                        thresh_function(layer_data[:, 0],
                                        layer_data[:, 1],
                                        layer_data[:, 2],
                                        **kwargs))

    def detect_samples(self, n_samples,
                       label_samples: bool = True,
                       mode="KMeans"):
        "Uses a clustering algorithm to detect samples automatically"
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
        labelled_layer_data = {}
        for layer_number, layer_data in tqdm(self.data_dict.items(),
                                             total=len(self.data_dict),
                                             disable=self.quiet):
            layer_xy = layer_data[:2, :]
            clusters = self.model.predict(layer_xy.T)
            labelled_layer_data[layer_number] = (layer_data, clusters)

        if label_samples is True:
            self.sample_labels = self.model.cluster_centers_

        self.labelled_layer_data = labelled_layer_data

    def separate_samples(self):
        "Separates labelled layer data into samples"
        self._qprint("\nSeparating samples into different datasets")
        sample_data = {}
        for layer_number, layer_data in tqdm(self.labelled_layer_data.items(),
                                             total=len(
                                                self.labelled_layer_data),
                                             desc="Overall",
                                             position=0,
                                             disable=self.quiet):
            layer_set = set(layer_data[1])
            for cluster_num in tqdm(layer_set,
                                    total=len(layer_set),
                                    desc=f"Layer {layer_number}",
                                    position=1,
                                    leave=False,
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
