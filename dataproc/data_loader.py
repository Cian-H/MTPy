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
from ..utils.apply_defaults import apply_defaults
from ..utils.large_hash import large_hash
from ..utils.metadata_tagging import add_metadata, read_metadata


default_cluster_config = {
    "n_workers": psutil.cpu_count() - 1,
    "threads_per_worker": 2,
    # "memory_limit": f"{psutil.virtual_memory().total / (2 * (psutil.cpu_count() - 1) * 1_073_741_824)}GB",
}


class DataLoader(Base):
    def __init__(
        self,
        cluster=None,
        data_cache: Path | str | None = "cache",
        keep_raw: bool = True,
        cluster_config: dict = {},
        **kwargs,
    ):
        super().__init__(**kwargs)
        if data_cache is None:
            data_cache = str(Path().cwd())
        if cluster is None:
            self.cluster = LocalCluster(**apply_defaults(cluster_config, default_cluster_config))
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
        self,
        data_path,
        calibration_curve: FunctionType | None = None,
        temp_units: str = "mV",
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
                columns=["x", "y", "z", "t", "rgb"],
            ).drop("rgb", axis=1) # The 'RGB' column is superfluous, as far as i can tell.
            batch_df.to_hdf(
                f"{self._data_cache}/working.h5",
                key="pyrometer",
                complib="blosc:lz4hc",
                complevel=9,
                append=True,
                compute=True,
            )

        # if keeping raw data, copy raw HDF5 files before modifying
        if self.keep_raw:
            shutil.copy(f"{self._data_cache}/working.h5", f"{self._data_cache}/raw.h5")

        self.data = dd.read_hdf(f"{self._data_cache}/working.h5", key="pyrometer", chunksize=2_500_000)

        # If given a calibration curve, apply it
        if calibration_curve is not None:
            self.apply_calibration_curve(calibration_curve=calibration_curve)
        self.temp_units = temp_units

    def commit(self):
        # If data in working.h5 doesnt match current dataframe, create new file to replace working.h5
        # if not self.data.eq(dd.read_hdf("cache/working.h5", key="pyrometer")).all().all().compute():
        Path(f"{self._data_cache}/commit.h5").unlink(missing_ok=True)
        self.data.to_hdf(
            f"{self._data_cache}/commit.h5",
            key="pyrometer",
            complib="blosc:lz4hc",
            complevel=9,
            compute=True,
        )
        del self.data
        Path(f"{self._data_cache}/working.h5").unlink(missing_ok=True)
        Path(f"{self._data_cache}/commit.h5").rename(f"{self._data_cache}/working.h5")
        self.data = dd.read_hdf(f"{self._data_cache}/working.h5", key="pyrometer", chunksize=2_500_000)

    def apply_calibration_curve(
        self,
        calibration_curve: FunctionType | None = None,
        temp_column: str = "t",
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
            self.commit()
            if units is not None:
                self.temp_units = units
            self._qprint("Calibrated!")
        # otherwise, set to raw values from datafiles
        else:
            self._qprint("No calibration curve given!")

    def reload_raw(self):
        unmodified = large_hash(f"{self._data_cache}/working.h5") == large_hash(f"{self._data_cache}/raw.h5")
        if self.keep_raw and not unmodified:
            del self.data
            Path(f"{self._data_cache}/working.h5").unlink(missing_ok=True)
            shutil.copy(f"{self._data_cache}/raw.h5", f"{self._data_cache}/working.h5")
            self.data = dd.read_hdf(f"{self._data_cache}/working.h5", key="pyrometer", chunksize=2_500_000)
        elif self.keep_raw:
            self._qprint("keep_raw param is set to False, no changes have been applied")
        elif unmodified:
            self._qprint("working == raw, no changes have been applied")

    def save(self, filepath: Path | str = Path("data")):
        self._qprint("Saving data...")
        # First, commit any pending changes
        self.commit()
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
        # Add pickled self.__dict__ (not including temporary attrs) to the data cache
        attrs = self.__dict__.copy()
        if "cluster" in attrs: del attrs["cluster"]
        if "client" in attrs: del attrs["client"]
        if "cache" in attrs: del attrs["cache"]
        pickle.dump(attrs, open(f"{self._data_cache}/attrs.pickle", "wb+"))
        # Get a hash for each file present in cache, and store to accelerate unpacking
        hashes = {}
        for f in Path(self._data_cache).iterdir():
            hashes[f.name] = large_hash(f)
        # Finally, compress the cache and its contents
        with tarfile.open(filepath, "w|gz") as tarball: # , compresslevel=5) as tarball:
            for p in self.progressbar(list(self._data_cache.iterdir())):
                tarball.add(p, arcname=p.name)
        add_metadata(filepath, hashes)
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
            try:
                # Check for hash metadata tagged onto file
                hashes = read_metadata(filepath)
                # Finally, extract and replace cache files unless hashes prove files are identical
                for member, fhash in self.progressbar(hashes.items()):
                    cache_path = Path(f"{self._data_cache}/{member}")
                    if cache_path.exists():
                        if fhash != large_hash(cache_path):
                            tarball.extract(member=member, path=self._data_cache)
                        else:
                            self._qprint(f"{member} matches existing cache. Skipping...")
            except Exception:
                self._qprint("No valid metadata was found! Attempting full overwrite...")
                members = list(tarball.getmembers())
                for member in self.progressbar(members):
                    tarball.extract(member=member, path=self._data_cache)
                
        # Finally, if present the attributes from the saved instance
        attr_path = Path(f"{self._data_cache}/attrs.pickle")
        if attr_path.exists():
            attrs = pickle.load(open(attr_path, "rb"))
            for k, v in attr_path.items():
                if k in self.__dict__ and k != "cache":
                    self.__dict__[k] = v
        self.data = dd.read_hdf(f"{self._data_cache}/working*.h5", key="pyrometer", chunksize=2_500_000)
        self._qprint("Data loaded!")
