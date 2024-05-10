"""A dummy loader module for composite classes that do not actually load data."""

from pathlib import Path
from typing import Optional

import dask.dataframe as dd
from fsspec.implementations.local import LocalFileSystem

from mtpy.utils.types import CalibrationFunction


class DummyLoader:
    """A dummy loader for composites that do not actually load data.

    Attributes:
        fs: The fsspec filesystem (defaults to `LocalFileSystem`)
        data: An empty dask `DataFrame` as a placeholder for loaded data
        temp_label: An empty string representing the expected temperature label
        temp_units: An empty string representing the units to be given to the
            temperature measurements
    """

    def read_layers(
        self: "DummyLoader",
        data_path: str = "",
        calibration_curve: Optional[CalibrationFunction] = None,
        temp_units: str = "",
        chunk_size: int = 0,
    ) -> None:
        """A `read_layers` method mimicking the state changes that occur when reading data.

        Args:
            self (DummyLoader): The DummyLoader instance
            data_path (str): The path to the data to be read. defaults to "".
            calibration_curve (Optional[CalibrationFunction]): A function for calibration of the
                data axes. Defaults to None.
            temp_units: The temperature units to be applied to the temperature axis. defaults to "".
            chunk_size: The target chunk size for the partitioned DataFrame. Unused in this dummy
                object. Defaults to 0
        """
        self.fs = LocalFileSystem()
        self.data = dd.DataFrame.from_dict({}, npartitions=1)
        self.temp_label = ""
        self.temp_units = ""

    def commit(self: "DummyLoader") -> None:
        """A placeholder for the `LoaderProtocol.commit` method.

        Does nothing in the context of this dummy object.

        Args:
            self (DummyLoader): The DummyLoader instance
        """
        pass

    def apply_calibration_curve(
        self: "DummyLoader",
        calibration_curve: Optional[CalibrationFunction],
        temp_column: str,
        units: Optional[str],
    ) -> None:
        """A placeholder for the `LoaderProtocol.apply_calibration_curve` method.

        Does nothing in the context of this dummy object.

        Args:
            self (DummyLoader): The DummyLoader instance
            calibration_curve (Optional[CalibrationFunction]): A function for calibration of the
                data axes. Defaults to None.
            temp_column: The column to designate as the temperature column
            units: The unist for the designated temperature column
        """
        pass

    def save(self: "DummyLoader", filepath: Path | str) -> None:
        """A placeholder for the `LoaderProtocol.save` method.

        Does nothing in the context of this dummy object.

        Args:
            self (DummyLoader): The DummyLoader instance
            filepath (str): The filepath to save to
        """
        pass

    def load(self: "DummyLoader", filepath: Path | str) -> None:
        """A placeholder for the `LoaderProtocol.load` method.

        Does nothing in this dummy object.

        Args:
            self (DummyLoader): The DummyLoader instance
            filepath (str): The filepath to load to
        """
        pass