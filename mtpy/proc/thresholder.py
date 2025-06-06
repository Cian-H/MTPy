"""A class that handles thresholding of data for the data pipeline."""

from __future__ import annotations

from math import cos, pi, sin
import operator as op
from typing import Any, Callable, Dict, Iterable, Protocol, Tuple, cast, runtime_checkable

from dask import dataframe as dd
import numpy as np
import pandas as pd

from mtpy.base.abstract import AbstractBase
from mtpy.utils.type_coercions import ensure_typedsizediterable

from .abstract import AbstractProcessor

degrees_per_rad = 180 / pi


@runtime_checkable
class ThresholdFunction(Protocol):
    """A protocol defining valid thresholding functions."""

    def __call__(self: "ThresholdFunction", x: float, y: float) -> bool:
        """Checks if an (x, y) point should be kept or removed from the dataset.

        Args:
            x (float): the x value.
            y (float): the y value.

        Returns:
            bool: True if point should be kept, False if not
        """
        ...


class Thresholder(AbstractProcessor, AbstractBase):
    """A class that handles thresholding of data for the data pipeline."""

    def rotate_xy(self: "Thresholder", angle: float) -> None:
        """Rotates the x and y coordinates of the current dataframe by the given angle.

        Args:
            angle (float): the angle by which to rotate the coordinates.
        """
        from mtpy.utils.type_guards import guarded_dask_series

        sin_theta = sin(angle / degrees_per_rad)
        cos_theta = cos(angle / degrees_per_rad)
        x = guarded_dask_series(self.loader.data["x"])
        y = guarded_dask_series(self.loader.data["y"])
        self.loader.data["x"] = (x.mul(cos_theta)) + (y.mul(sin_theta))
        self.loader.data["y"] = (x.mul(-sin_theta)) + (y.mul(cos_theta))

    def avgspeed_threshold(
        self: "Thresholder", threshold_percent: float = 1, avgof: int = 1
    ) -> None:
        """Thresholds layer data (x,y,w) based on average speed.

        Thresholds layer data based on (x, y) average speed. Average speed is calculated as the
        average slope of the rolling average of displacement. Points are then thresholded out if
        they are above a certain percentage of the max speed, based on the assumption they are
        intersample traversal paths.

        Args:
            threshold_percent (float, optional): the percentage of the max speed above which points
                will be removed. Defaults to 1.
            avgof (int, optional): the number of points to average over. Defaults to 1.
        """
        threshold_percent /= 100.0  # convert threshold percent to decimal
        # calc displacements using pythagorean theorem
        x_squared = self.loader.data["x"] * self.loader.data["x"]
        y_squared = self.loader.data["y"] * self.loader.data["y"]
        sum_of_squares = x_squared + y_squared
        # Add displacement column to frame
        displacement = sum_of_squares.sqrt()

        # Calculate rolling average of displacement
        rollingavgdisp = np.convolve(displacement.to_numpy(), np.ones(avgof) / avgof, mode="valid")
        # get absolute average speed based on rolling avg displacement
        absavgdispslope = np.abs(np.diff(rollingavgdisp))
        threshold = threshold_percent * np.max(absavgdispslope)  # thresh val
        self.loader.data = self.loader.data[avgof:]
        self.loader.data.add_column(name="filter", f_or_array=absavgdispslope < threshold)
        self.loader.data = self.loader.data[self.loader.data["filter"]]
        self.loader.data = self.loader.data.extract()
        self.loader.data.drop("filter", inplace=True)

    def avg_threshold(
        self: "Thresholder",
        threshold_percent: float = 1,
        column: str = "w1",
        comparison_func: Callable[[float, float], bool] = op.gt,
    ) -> None:
        """Threshold by comparison with the mean of a column.

        Selectively keeps data based on comparison with a percentage of the mean of whatever column
        is specified.

        Args:
            threshold_percent (float, optional): the percentage of the mean to threshold by.
                Defaults to 1.
            column (str, optional): the column to threshold by. Defaults to "w1".
            comparison_func (Callable[[float, float], bool], optional): The comparison function by
                which to threshold. Defaults to f(x, y): x > y.
        """
        threshold_percent /= 100.0  # convert threshold percent to decimal
        threshold = threshold_percent * cast("dd.Series", self.loader.data[column]).mean()
        self.loader.data = self.loader.data[comparison_func(self.loader.data[column], threshold)]
        self.loader.data = self.loader.data.extract()

    def avg_greaterthan(
        self: "Thresholder",
        column: str = "w1",
        threshold_percent: float = 1,
    ) -> None:
        """Keeps all values greater than threshold percent of average for column.

        Args:
            column (str, optional): column to threshold by. Defaults to "w1".
            threshold_percent (float, optional): the percentage to threshold by. Defaults to 1.
        """
        self.avg_threshold(
            column=column, threshold_percent=threshold_percent, comparison_func=op.gt
        )

    def avg_lessthan(
        self: "Thresholder",
        column: str = "w1",
        threshold_percent: float = 1,
    ) -> None:
        """Keeps all values less than threshold percent of average for column.

        Args:
            column (str, optional): column to threshold by. Defaults to "w1".
            threshold_percent (float, optional): the percentage to threshold by. Defaults to 1.
        """
        self.avg_threshold(
            column=column, threshold_percent=threshold_percent, comparison_func=op.lt
        )

    def threshold_all_layers(
        self: "Thresholder",
        thresh_functions: Callable[[float, float], bool] | Iterable[Callable[[float, float], bool]],
        threshfunc_kwargs: Dict[str, Any] | Iterable[Dict[str, Any]],
    ) -> None:
        """Thresholds all layers in a single pass.

        Thresholds all layers by applying listed functions to the current dataframe with
        listed params.

        Args:
            thresh_functions
                (Callable[[float, float], bool] | Iterable[Callable[[float, float], bool]]): a list
                of functions to apply
            threshfunc_kwargs (Dict[str, Any] | Iterable[Dict[str, Any]]): a list of kwargs for
                the functions to apply

        Raises:
            ValueError: If provided `thresh_function` is invalid or if `threshfunc_kwargs` do not
                match `thresh_func` kwargs.
        """
        thresh_functions = ensure_typedsizediterable(thresh_functions, ThresholdFunction)
        threshfunc_kwargs = ensure_typedsizediterable(threshfunc_kwargs, Dict[str, object])

        if len(thresh_functions) != len(threshfunc_kwargs):
            msg = "thresh_functions and threshfunc_kwargs must be the same length"
            raise ValueError(msg)

        self.logger.info("Thresholding data")

        # Prep progress bar iterator (assigned to variable for code clarity)
        progbar_iterator = self.progressbar(
            zip(thresh_functions, threshfunc_kwargs, strict=False),
            total=len(thresh_functions),
            position=1,
            leave=False,
        )

        # apply each requested thresholding function in sequence
        for thresh_function, kwargs in progbar_iterator:
            # WARNING: This is a clear, dynamic footgun but fixing it would hamstring the
            #   usefulness of the thresholding function without serious type gymnastics.
            thresh_function(**kwargs)

    # def detect_samples_kmeans(self, n_samples):
    #     "Uses a clustering algorithm to detect samples automatically"
    #     self.logger.info("Detecting contiguous samples")
    #     # KMeans train to recognize clusters
    #     self.kmeans_model = KMeans(n_clusters=n_samples, features=["x", "y"])
    #     # Loop repeats the kmeans training until desired num of samples found
    #     while True:
    #         self.kmeans_model.fit(self.loader.data)
    #         # Label samples
    #         self.logger.info("Kmeans training complete!\nLabelling samples...")
    #         data = self.kmeans_model.transform(self.loader.data)
    #         n_found = len(data["prediction_kmeans"].unique())
    #         if n_found < n_samples:
    #             self.logger.info(f"Repeating Kmeans training (samples found: {n_found})")
    #         else:
    #             self.loader.data = data
    #             break

    #     # Save centroids for positioning of labels
    #     self.sample_labels = np.asarray(self.kmeans_model.cluster_centers)
    #     self.loader.data.rename("prediction_kmeans", "sample")
    #     self.logger.info("Sample detection complete!")

    def mask_xyrectangles(
        self: "Thresholder", sample_map: Dict[Any, Tuple[Tuple[int, int], Tuple[int, int]]]
    ) -> None:
        """Mask rectangles on the projected xy plane.

        Masks off rectangles as samples based on a dict where keys are sample numbers and values
        are tuples of ((x1, x2), (y1, y2)), then dump all points outside those samples

        Args:
            sample_map (Dict[Any, Tuple[Tuple[int, int], Tuple[int, int]]]):
                a dict of sample labels and tuples of ((x1, x2), (y1, y2))
        """

        def map_func(df: pd.DataFrame) -> pd.Series[float]:
            samples = np.full(len(df), -1, dtype=int)
            for k, ((x1, x2), (y1, y2)) in sample_map.items():
                x_min, x_max = min(x1, x2), max(x1, x2)
                y_min, y_max = min(y1, y2), max(y1, y2)
                samples[df["x"].between(x_min, x_max) & df["y"].between(y_min, y_max)] = k
            return pd.Series(samples, index=df.index, name="sample")

        self.loader.data["sample"] = self.loader.data.map_partitions(map_func)
        self.loader.data = self.loader.data.loc[self.loader.data["sample"].ge(0)]
