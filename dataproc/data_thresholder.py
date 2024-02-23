#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import operator as op
from types import FunctionType, MethodType

import numpy as np
import pandas as pd
from math import pi, sin, cos

from .data_loader import DataLoader


degrees_per_rad = 180 / pi


class DataThresholder(DataLoader):
    """A class that handles thresholding of data for the data pipeline."""

    def __init__(self, **kwargs):
        """Initialises a DataThresholder object."""
        super().__init__(**kwargs)
        # Include and bind julia counterpart to this module
        # self._jl_interpreter.include(f"{__file__[:__file__.rfind('.')]}.jl")
        # self._julia = getattr(
        #     self._jl_interpreter, __file__.split("/")[-1].split(".")[0]
        # )

    def rotate_xy(self, angle: float) -> None:
        """Rotates the x and y coordinates of the current dataframe by the given angle.

        Args:
            angle (float): the angle by which to rotate the coordinates.
        """
        sin_theta, cos_theta = sin(angle / degrees_per_rad), cos(angle / degrees_per_rad)
        x, y = self.data["x"], self.data["y"]
        self.data["x"] = (x.mul(cos_theta)) + (y.mul(sin_theta))
        self.data["y"] = (x.mul(-sin_theta)) + (y.mul(cos_theta))

    def vx_rolling_sum(self, series, window):
        """A specialised method for calculating the rolling sum of a series on a vaex dataframe.
        (DEPRECATED)
        """
        array = [0.0 for i in range(window)]
        max = series.shape[0]
        for i, j in zip(range(0, max - window), range(window, max)):
            array.append(series[i:j].sum())
        return array

    def avgspeed_threshold(self, threshold_percent=1, avgof=1):
        """Thresholds layer data (x,y,w) based on percentage of max average slope
            of rolling average of displacement

        Args:
            threshold_percent (int, optional): the percentage of the max speed above which points
            will be removed. Defaults to 1.
            avgof (int, optional): the number of points to average over. Defaults to 1.
        """
        threshold_percent /= 100.0  # convert threshold percent to decimal
        # calc displacements using pythagorean theorem
        x_squared = self.data["x"] * self.data["x"]
        y_squared = self.data["y"] * self.data["y"]
        sum_of_squares = x_squared + y_squared
        # Add displacement column to frame
        displacement = sum_of_squares.sqrt()

        # Calculate rolling average of displacement
        rollingavgdisp = np.convolve(displacement.to_numpy(), np.ones(avgof) / avgof, mode="valid")
        # get absolute average speed based on rolling avg displacement
        absavgdispslope = np.abs(np.diff(rollingavgdisp))
        threshold = threshold_percent * np.max(absavgdispslope)  # thresh val
        self.data = self.data[avgof:]
        self.data.add_column(name="filter", f_or_array=absavgdispslope < threshold)
        self.data = self.data[self.data["filter"]]
        self.data = self.data.extract()
        self.data.drop("filter", inplace=True)

    def avg_threshold(self, threshold_percent=1, column="w1", comparison_func=None):
        """Selectively keeps data based on comparison with a percentage of the
            mean of whatever column is specified

        Args:
            threshold_percent (int, optional): the percentage of the mean to threshold by.
                Defaults to 1.
            column (str, optional): the column to threshold by. Defaults to "w1".
            comparison_func (_type_, optional): The comparison function by which to threshold.
                Defaults to None.
        """
        threshold_percent /= 100.0  # convert threshold percent to decimal
        threshold = threshold_percent * self.data[column].mean()
        self.data = self.data[comparison_func(self.data[column], threshold)]
        self.data = self.data.extract()

    def avg_greaterthan(self, column="w1", threshold_percent=1):
        """Keeps all values greater than threshold percent of average for column

        Args:
            column (str, optional): column to threshold by. Defaults to "w1".
            threshold_percent (int, optional): the percentage to threshold by. Defaults to 1.
        """
        self.avg_threshold(
            column=column, threshold_percent=threshold_percent, comparison_func=op.gt
        )

    def avg_lessthan(self, column="w1", threshold_percent=1):
        """Keeps all values less than threshold percent of average for column

        Args:
            column (str, optional): column to threshold by. Defaults to "w1".
            threshold_percent (int, optional): the percentage to threshold by. Defaults to 1.
        """
        self.avg_threshold(
            column=column, threshold_percent=threshold_percent, comparison_func=op.lt
        )

    def threshold_all_layers(self, thresh_functions: list, threshfunc_kwargs: list):
        """Thresholds all layers by applying listed functions to the current dataframe with
            listed params.

        Args:
            thresh_functions (list): a list of functions to apply
            threshfunc_kwargs (list): a list of kwargs for the functions to apply
        """
        # if conversion to dict is needed for single function, then convert
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

    # def detect_samples_kmeans(self, n_samples):
    #     "Uses a clustering algorithm to detect samples automatically"
    #     self._qprint("\nDetecting contiguous samples\n")
    #     # KMeans train to recognize clusters
    #     self.kmeans_model = KMeans(
    #         n_clusters=n_samples, features=["x", "y"], verbose=(not self.quiet)
    #     )
    #     # Loop repeats the kmeans training until desired num of samples found
    #     while True:
    #         self.kmeans_model.fit(self.data)
    #         # Label samples
    #         self._qprint("\nKmeans training complete!\nLabelling samples...")
    #         data = self.kmeans_model.transform(self.data)
    #         n_found = len(data["prediction_kmeans"].unique())
    #         if n_found < n_samples:
    #             print(f"\nRepeating Kmeans training (samples found: {n_found})\n")
    #         else:
    #             self.data = data
    #             break

    #     # Save centroids for positioning of labels
    #     self.sample_labels = np.asarray(self.kmeans_model.cluster_centers)
    #     self.data.rename("prediction_kmeans", "sample")
    #     self._qprint("\nSample detection complete!")

    def mask_xyrectangles(self, sample_map: dict):
        """Masks off rectangles as samples based on a dict where keys are sample numbers and values
            are tuples of ((x1, x2), (y1, y2)), then dump all points outside those samples

        Args:
            sample_map (dict): a dict of sample labels and tuples of ((x1, x2), (y1, y2))
        """

        # def map_func(row):
        #     for sample, ((x_min, x_max), (y_min, y_max)) in sample_map.items():
        #         if (x_min < row["x"] < x_max) and (y_min < row["y"] < y_max):
        #             return sample

        # self.data["sample"] = self.data.apply(map_func, axis=1, meta=(None, "int64"))
        def map_func(df):
            samples = np.full(len(df), -1, dtype=int)
            for k, ((x1, x2), (y1, y2)) in sample_map.items():
                x_min, x_max = min(x1, x2), max(x1, x2)
                y_min, y_max = min(y1, y2), max(y1, y2)
                samples[df["x"].between(x_min, x_max) & df["y"].between(y_min, y_max)] = k
            return pd.Series(samples, index=df.index, name="sample")
        
        self.data["sample"] = self.data.map_partitions(map_func)
        self.data = self.data.loc[self.data["sample"].ge(0)]
