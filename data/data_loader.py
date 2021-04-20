#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ..common.base import Base
from pathlib import Path
import pandas as pd
import numpy as np
from tqdm.auto import tqdm
from types import FunctionType


class DataLoader(Base):
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
    """

    def __init__(self,
                 data_path: str = None,
                 **kwargs):
        """
        Constructor for the MTPy DataLoader Base class

        Parameters
        ----------
            quiet: bool = False
                Determines whether object should be quiet or not
            data_path: str = None
                The path to the data to be processed
        """
        super().__init__(**kwargs)
        # stores location from which to read data
        self.data_path = str(Path(data_path).expanduser())
        # modifiable file extension to search for, in case needed in future
        self.file_extension = "pcd"
        # process data_path to make more usable

    def read_layers(self, calibration_curve: FunctionType = None):
        """Reads layer files into data structure for processing"""
        self._qprint(f"\nSearching for files at {self.data_path}")
        # glob filenames
        pathlist = Path(self.data_path).glob(f"*.{self.file_extension}")
        data_dict = {}
        files = []

        for path in pathlist:
            path_in_str = str(path)
            file = path_in_str.split("/")[-1:][0]
            files.append(file)

        files = sorted(files)

        self._qprint(f"Reading files from {self.data_path}")

        # Read data from files
        for file in tqdm(files, total=len(files), disable=self.quiet):
            # try:
            idx = float(file[:-1-len(self.file_extension)])
            df = pd.read_csv(f"{self.data_path}/{file}",
                             names=["x", "y", "temp", "temp_duplicate"],
                             header=None, delimiter=" ")

            df.drop(["temp_duplicate"], axis=1, inplace=True)
            df = df.groupby(["x", "y"], sort=False, as_index=False).mean()
            # Corrects for flipped x axis on aconity output
            df["x"] *= -1
            # If given a calibration curve, apply it
            if calibration_curve is not None:
                df["temp"] = calibration_curve(df["temp"])
            data_dict[idx] = np.asarray(df)
            # except:  # noqa
            #     self._qprint(f"File {file} not found!")

        self.original_data_dict = data_dict
        self.reset_data()

    def reset_data(self):
        """Undoes all data processing that was performed on loaded data"""
        self.data_dict = self.original_data_dict.copy()
