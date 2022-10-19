#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pickle
import shutil
import tarfile
from itertools import repeat
from multiprocessing import Pool
from pathlib import Path
from types import FunctionType, SimpleNamespace

import psutil
from dask import array as da
from dask import dataframe as dd
from dask.distributed import Client, LocalCluster
from read_layers import read_selected_layers

from ..common.base import Base


default_cluster_config = {
    "n_workers": psutil.cpu_count() - 1,
    "threads_per_worker": 2,
    # "memory_limit": f"{psutil.virtual_memory().total / (2 * (psutil.cpu_count() - 1) * 1_073_741_824)}GB",
}


class DataLoader(Base):

    def __init__(
        self,
        cluster=None,
        data_cache: str | None = None,
        keep_raw: bool = True,
        **kwargs,
    ):
        super().__init__(**kwargs)
        if data_cache is None:
            data_cache = str(Path().cwd())
        if cluster is None:
            self.cluster = LocalCluster(**default_cluster_config)
        else:
            self.cluster = cluster
        self.client = Client(self.cluster)
        # Stores location from which to read data
        # Set default labels for t axis
        self.temp_label = "Pyrometer Response"
        self.temp_units = None
        # Cache info
        self.keep_raw = keep_raw
        self._cache = (
            SimpleNamespace()
        )  # NOTE: DEPRECATED! Left it because i cant remember if its needed in the GUI application. If unneeded will delete later.
        self._data_cache = Path(data_cache)
        self._data_cache.mkdir(parents=True, exist_ok=True)
        # Misc configuration attributes
        self._memory_limit = self.cluster._memory_per_worker()
        self._file_suffix = ".mtp"

    def __del__(self, **kwargs):
        # Close dask cluster and client
        # TODO: possible bug here if user passes dask client and intends to continue using it outside MTPy
        # Without this code though, dask clients could be left causing mem leaks. Need to find a solution
        self.cluster.close()
        self.client.close()
        # Delete cache files if still present
        for p in self._data_cache.iterdir():
            p.unlink(missing_ok=True)
        self._data_cache.rmdir()
        # super().__del__(**kwargs) # Not needed currently, but will be if __del__ added to parent

    def read_layers(
        self, data_path, calibration_curve: FunctionType | None = None, temp_units: str = "mV"
    ):
        self._qprint(f"\nSearching for files at {data_path}")
        # Calculate read batches
        batches = [[]]
        acc = 0
        layer_files = list(Path(data_path).expanduser().glob("*.pcd"))
        # Prepare batches of files wtih total size less than memory_limit to read at once
        for p in sorted(layer_files, key=lambda x: float(x.stem)):
            file_size = p.stat().st_size
            assert (
                file_size < self._memory_limit
            ), "File size too large for available RAM!"
            acc += file_size
            if acc > self._memory_limit:
                batches.append([])
                acc = file_size
            batches[-1].append(str(p))

        # Then read files (offloaded to local rust library "read_layers")
        for file_list in self.progressbar(batches, position=2):
            # Read each batch in rust to dask dataframe, then add df to compressed HDF5
            batch_df = dd.from_array(
                da.from_array(read_selected_layers(file_list)),
                columns=["x", "y", "z", "t1", "t2"],
            )
            batch_df.to_hdf(
                f"{self._data_cache}/working.h5",
                key="pyrometer",
                complib="blosc:lz4hc",
                complevel=9,
                append=True,
            )

        # if keeping raw data, copy raw HDF5 files before modifying
        if self.keep_raw:
            shutil.copy(f"{self._data_cache}/working.h5", f"{self._data_cache}/raw.h5")

        self.data = dd.read_hdf(f"{self._data_cache}/working.h5", key="pyrometer")

        # If given a calibration curve, apply it
        if calibration_curve:
            self.apply_calibration_curve(calibration_curve=calibration_curve)
        self.temp_units = temp_units

    def apply_calibration_curve(
        self,
        calibration_curve: FunctionType | None = None,
        temp_column: str = "t1",
        units: str | None = None,
    ):
        # if a calibration curve is given
        if calibration_curve is not None:
            # Set temp_column to calibrated values
            self._qprint("Applying calibration curve")
            self.data[temp_column] = calibration_curve(
                x=self.data["x"],
                y=self.data["y"],
                z=self.data["z"],
                t=self.data[temp_column],
            )
            # Then, create a new HDF5 to work from, replace old one, and load it
            self.data.to_hdf(
                f"{self._data_cache}/calibrated.h5",
                key="pyrometer",
                complib="blosc:lz4hc",
                complevel=9,
            )
            del self.data
            Path(f"{self._data_cache}/working.h5").unlink(missing_ok=True)
            Path(f"{self._data_cache}/calibrated.h5").rename(
                f"{self._data_cache}/working.h5"
            )
            self.data = dd.read_hdf(f"{self._data_cache}/working.h5", key="pyrometer")
            if units is not None:
                self.temp_units = units
            self._qprint("Calibrated!")
        # otherwise, set to raw values from datafiles
        else:
            self._qprint("No calibration curve given!")

    def reload_raw(self):
        if self.keep_raw:
            del self.data
            Path(f"{self._data_cache}/working.h5").unlink(missing_ok=True)
            shutil.copy(f"{self._data_cache}/raw.h5", f"{self._data_cache}/working.h5")
            self.data = dd.read_hdf(f"{self._data_cache}/working.h5", key="pyrometer")
        else:
            self._qprint("keep_raw param set to False, no raw data present!")

    def save(self, filepath: Path | str = Path("data")):
        self._qprint("Saving data...")
        # Process filename before saving
        if type(filepath) is str:
            filepath = Path(filepath)
        if not filepath.suffix:
            filepath = filepath.with_suffix(self._file_suffix)
        # Check if file exists, if does save with lowest available number added
        p = filepath
        i = 1
        while p.exists():
            p = Path(f"{str(filepath)[:-4]}({i}){str(filepath)[-4:]}")
            i += 1
        if filepath != p:
            self._qprint(f"{filepath} already exists! Saving as {p}...")
            filepath = p
        # Add pickled self.__dict__ to the data cache
        attrs = self.__dict__.copy()
        del attrs["cluster"]
        del attrs["client"]
        pickle.dump(attrs, open(f"{self._data_cache}/attrs.dict", "wb+"))
        with tarfile.open(filepath, "w:gz", compresslevel=5) as tarball:
            for p in self.progressbar(list(self._data_cache.iterdir())):
                tarball.add(p, arcname=p.name)
        self._qprint("Data saved!")

    def load(self, filepath: Path | str = Path("data")):
        self._qprint("Loading data...")
        # Process filename before saving
        if type(filepath) is str:
            filepath = Path(filepath)
        if not filepath.exists() and not filepath.suffix:
            filepath = filepath.with_suffix(self._file_suffix)
        self._data_cache.mkdir(parents=True, exist_ok=True)
        with tarfile.open(filepath, "r:gz") as tarball:
            members = list(tarball.getmembers())
            for member in self.progressbar(members):
                tarball.extract(member=member, path=self._data_cache)
        # Finally, reload the attributes from the saved instance
        attrs = pickle.load(open(f"{self._data_cache}/attrs.dict", "rb"))
        for k, v in attrs.items():
            if k in self.__dict__ and k != "cache":
                self.__dict__[k] = v
        self.data = dd.read_hdf(f"{self._data_cache}/working*.h5", key="pyrometer")
        self._qprint("Data loaded!")
