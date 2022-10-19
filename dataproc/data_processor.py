#!/usr/bin/env python
# -*- coding: utf-8 -*-

import operator as op
from types import FunctionType, MethodType

import numpy as np

from .data_loader import DataLoader


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
        # Include and bind julia counterpart to this module
        # self._jl_interpreter.include(f"{__file__[:__file__.rfind('.')]}.jl")
        # self._julia = getattr(
        #     self._jl_interpreter, __file__.split("/")[-1].split(".")[0]
        # )

    def vx_rolling_sum(self, series, window):
        array = [0.0 for i in range(window)]
        max = series.shape[0]
        for i, j in zip(range(0, max - window), range(window, max)):
            array.append(series[i:j].sum())
        return array

    def avgspeed_threshold(self, threshold_percent=1, avgof=1):
        """
        Thresholds layer data (x,y,w) based on percentage of max average slope
        of rolling average of displacement
        """
        threshold_percent /= 100.0  # convert threshold percent to decimal
        # calc displacements using pythagorean theorem
        x_squared = self.data["x"] * self.data["x"]
        y_squared = self.data["y"] * self.data["y"]
        sum_of_squares = x_squared + y_squared
        # Add displacement column to frame
        displacement = sum_of_squares.sqrt()

        # Calculate rolling average of displacement
        rollingavgdisp = np.convolve(
            displacement.to_numpy(), np.ones(avgof) / avgof, mode="valid"
        )
        # get absolute average speed based on rolling avg displacement
        absavgdispslope = np.abs(np.diff(rollingavgdisp))
        threshold = threshold_percent * np.max(absavgdispslope)  # thresh val
        self.data = self.data[avgof:]
        self.data.add_column(name="filter", f_or_array=absavgdispslope < threshold)
        self.data = self.data[self.data["filter"]]
        self.data = self.data.extract()
        self.data.drop("filter", inplace=True)

    def avg_threshold(self, threshold_percent=1, column="w1", comparison_func=None):
        """
        Selectively keeps data based on comparison with a percentage of the
        mean of whatever column is given
        """
        threshold_percent /= 100.0  # convert threshold percent to decimal
        threshold = threshold_percent * self.data[column].mean()
        self.data = self.data[comparison_func(self.data[column], threshold)]
        self.data = self.data.extract()

    def avg_greaterthan(self, column="w1", threshold_percent=1):
        "Keeps all values greater than threshold percent of average for column"
        return self.avg_threshold(
            column=column, threshold_percent=threshold_percent, comparison_func=op.gt
        )

    def avg_lessthan(self, x, y, z, w1, w2, column="w1", threshold_percent=1):
        "Keeps all values less than threshold percent of average for column"
        return self.avg_threshold(
            column=column, threshold_percent=threshold_percent, comparison_func=op.lt
        )

    def threshold_all_layers(self, thresh_functions, threshfunc_kwargs):
        "Thresholds all layers by applying listed functions with listed params"
        # if conversions to dict is needed for single function, then convert
        if type(thresh_functions) in (FunctionType, MethodType):
            thresh_functions = (thresh_functions,)
        if type(threshfunc_kwargs) is dict:
            threshfunc_kwargs = (threshfunc_kwargs,)

        self._qprint("\nThresholding data")

        # Prep progress bar iterator (assigned to variable for code clarity)
        progbar_iterator = self.progressbar(
            zip(thresh_functions, threshfunc_kwargs),
            total=len(thresh_functions),
            position=1,
            leave=False,
            disable=self.quiet,
        )

        # apply each requested thresholding function in sequence
        for thresh_function, kwargs in progbar_iterator:
            thresh_function(**kwargs)

    def detect_samples_kmeans(self, n_samples):
        "Uses a clustering algorithm to detect samples automatically"
        self._qprint("\nDetecting contiguous samples\n")
        # KMeans train to recognize clusters
        self.kmeans_model = KMeans(
            n_clusters=n_samples, features=["x", "y"], verbose=(not self.quiet)
        )
        # Loop repeats the kmeans training until desired num of samples found
        while True:
            self.kmeans_model.fit(self.data)
            # Label samples
            self._qprint("\nKmeans training complete!\nLabelling samples...")
            data = self.kmeans_model.transform(self.data)
            n_found = len(data["prediction_kmeans"].unique())
            if n_found < n_samples:
                print(f"\nRepeating Kmeans training (samples found: {n_found})\n")
            else:
                self.data = data
                break

        # Save centroids for positioning of labels
        self.sample_labels = np.asarray(self.kmeans_model.cluster_centers)
        self.data.rename("prediction_kmeans", "sample")
        self._qprint("\nSample detection complete!")
