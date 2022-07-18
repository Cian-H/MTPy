#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ..common.base import Base
from pathlib import Path
import shutil
import re
import vaex as vx
import numpy as np
from types import FunctionType, SimpleNamespace


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
                 chunk_size: int = 1_048_576,
                 cache_path: str = None,
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
        # Sets a chunk size for all vaex ops
        self.chunk_size = chunk_size
        # Stores location from which to read data
        self.data_path = str(Path(data_path).expanduser())
        # Modifiable file extensions, in case needed in future
        self.data_extension = "pcd"
        # Path to the currently loaded datafile to prevent read/write segfaults
        self.currently_loaded = None
        # Set default labels for w axis
        self.wlabel = "Temp"
        self.wunits = "mV"
        # Cache info
        self._cache = SimpleNamespace()
        self._cache.cache_extension = "arrow"
        if cache_path is None:
            self._cache.cache_path = f"{self.data_path}/cache/"
        else:
            self._cache.cache_path = cache_path
        self._cache.read_cache_file = f"{self._cache.cache_path}read"  # noqa
        self._cache.raw_cache_file = f"{self._cache.cache_path}data_raw.{self._cache.cache_extension}"  # noqa
        self._cache.cache_file = f"{self._cache.cache_path}data.{self._cache.cache_extension}"  # noqa

    def read_layers(self, calibration_curve: FunctionType = None,
                    units: str = "mV"):
        """Reads layer files into DataFrames for processing.

        DataFrames will be:
        raw_data  = the unthresholded dataset
        data      = the thresholded dataset

        Columns in each will be:
        x     = x coordinates,
        y     = y coordinates,
        z     = z coordinates,
        w1    = calibrated temperature data from probe 1,
        w2    = calibrated temperature data from probe 2,
        w1_0  = uncalibrated temperature data from probe 1,
        w2_0  = uncalibrated temperature data from probe 2"""
        self._qprint(f"\nSearching for files at {self.data_path}")
        # glob filenames
        dataframes = []
        files = sorted(
            [file.name for file in
                Path(self.data_path).glob(f"*.{self.data_extension}")]
        )

        self._qprint(f"Reading files from {self.data_path}")
        Path(f"{self.data_path}/cache").mkdir(parents=True, exist_ok=True)

        # Read data from files
        for file in self.progressbar(files, total=len(files),
                                     disable=self.quiet):
            # Check file isnt empty before reading
            if Path(f"{self.data_path}/{file}").stat().st_size != 0:
                df = vx.from_csv(f"{self.data_path}/{file}",
                                 names=["x", "y", "w1_0", "w2_0"],
                                 header=None, delimiter=" ", dtype="float64",
                                 chunk_size=self.chunk_size,  # noqa Num of rows resident in memory at once
                                 convert=f"{self._cache.read_cache_file}_{file}.{self._cache.cache_extension}")  # noqa Sets to convert chunks to files for caching
                # Corrects for flipped x axis on aconity output
                df["x"] *= -1
                # Prep z column
                df["z"] = np.repeat(float(file[:-1 - len(self.data_extension)]),
                                    len(df))
                dataframes.append(df)
            else:  # Otherwise, print an error message
                print(f"File {file} is empty! Skipping...\n")

        # concatenate dataframes, add indeces and save this new array to an,
        # arrow file
        self.raw_data = vx.concat(dataframes)
        self.raw_data["n"] = np.arange(self.raw_data.shape[0], dtype="int64")
        self.raw_data.export(self._cache.raw_cache_file)
        # Clear out now unneeded vaex arrays and caches
        dataframes.clear()
        del(dataframes)
        del(self.raw_data)
        cache_dir = Path(self._cache.cache_path)
        read_cache = (cache_dir.glob(f"read*.{self._cache.cache_extension}"),
                      cache_dir.glob("read*.yaml"))
        read_cache = (Path(item) for sublist in read_cache for item in sublist)
        for file in read_cache:
            file.unlink()
        # Load vaex array from new arrow cache
        self.raw_data = vx.open(self._cache.raw_cache_file)
        # If given a calibration curve, apply it
        self.apply_calibration_curve(calibration_curve=calibration_curve,
                                     units=units)

    def apply_calibration_curve(self,
                                calibration_curve: FunctionType = None,
                                units: str = "mV"):
        "Applies calibration curve function to w axis (temp) data"
        # if data is present
        if hasattr(self, "raw_data"):
            # First, create and assign a new cache for working data
            if not Path(self._cache.raw_cache_file).exists():
                self.raw_data.export(self._cache.raw_cache_file)
            shutil.copy(self._cache.raw_cache_file, self._cache.cache_file)
            self.data = vx.open(self._cache.cache_file)

            # if a calibration curve is given set wn_1 to calibrated values
            if calibration_curve is not None:
                self._qprint("Applying calibration curve")
                # TODO: TEMPORARY PATCH!!!!! DOESNT ALLOW USE OF W2!
                self.data["w1"] = calibration_curve(
                    x=self.data["x"],
                    y=self.data["y"],
                    z=self.data["z"],
                    w1=self.data["w1_0"],
                    w2=self.data["w2_0"]
                )
            # otherwise, set to raw values from datafiles
            else:
                self._qprint("Applying no calibration curve")
                self.data["w1"] = self.data["w1_0"]
                self.data["w2"] = self.data["w2_0"]
            self.wunits = units
        self._qprint("Calibrated!")

    def save_data(self, filename: str = "data"):
        self._qprint("Saving data...")
        # Process filename before saving
        if "." not in filename:
            filename += f".{self._cache.cache_extension}"
        # Ensure not saving to same file being read
        if f"{Path().cwd()}/{filename}" == self.currently_loaded:
            parsed = filename.split(".")
            # if ends in a number, increment it by 1
            if parsed[-2][-1].isnumeric():
                n1 = re.search(r"\d+$", parsed[-2]).group()
                n2 = str(int(n1) + 1)
                parsed[-2] = parsed[-2][-len(n1):] + n2
            # Otherwise, just add a "1"
            else:
                parsed[-2] += "1"
            filename = ".".join(parsed)
        # If working data is present, save it
        if hasattr(self, "data"):
            self.data.export(filename, chunk_size=self.chunk_size)
        # If raw data is present save it too
        if hasattr(self, "raw_data"):
            raw_filename = filename.split(".")
            raw_filename[-2] += "_raw"
            raw_filename = ".".join(raw_filename)
            self.raw_data.export(raw_filename, chunk_size=self.chunk_size)
        # If sample labels are present, save them too
        if hasattr(self, "sample_labels"):
            label_filename = filename.split(".")
            label_filename[-2] += "_labels"
            label_filename = ".".join(label_filename[:-1])
            self.sample_labels.tofile(f"{label_filename}.np")
        self._qprint("Data saved!")

    def load_data(self, filename: str = "data"):
        self._qprint("Loading data...")
        # Process filename to ensure is a working data filename
        if "." not in filename:
            filename += f".{self._cache.cache_extension}"
        filename = filename.split(".")
        if filename[-2][-4:] == "_raw":
            filename[-2] = filename[-2][:-4]
        filename = ".".join(filename)
        # Generate a raw filename from that
        raw_filename = filename.split(".")
        label_filename = raw_filename.copy()  # copy to avoid repeating split
        raw_filename[-2] += "_raw"
        raw_filename = ".".join(raw_filename)
        # Also generate a label filename from that
        label_filename[-2] += "_labels"
        label_filename = ".".join(label_filename[:-1])
        label_filename += ".np"
        # Create cache if needed
        if (Path(raw_filename).is_file()
                or Path(filename).is_file()
                or Path(label_filename).is_file()):
            Path(f"{self.data_path}/cache").mkdir(parents=True, exist_ok=True)
        # open raw file if present
        if Path(raw_filename).is_file():
            self.raw_data = vx.open(raw_filename)
        # open working data if present
        if Path(filename).is_file():
            self.data = vx.open(filename)
        # open labels if present
        if Path(label_filename).is_file():
            self.sample_labels = np.fromfile(label_filename)
            self.sample_labels = self.sample_labels.reshape(
                (self.sample_labels.shape[0] // 2, 2)
            )
        # if not present, silently create working data
        else:
            quiet_state = self.quiet
            self.quiet = True
            self.apply_calibration_curve()
            self.quiet = quiet_state
        # Finally, store path to prevent segfaults later
        self.currently_loaded = f"{Path().cwd()}/{filename}"
        self._qprint("Data loaded!")
