#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import pickle
import shutil
import tarfile
from itertools import repeat
from multiprocessing import Pool
from pathlib import Path
from types import FunctionType, SimpleNamespace

import psutil
import dask
from dask import array as da
from dask.distributed import Client, LocalCluster
from read_layers import read_selected_layers

from ..common.base import Base
from ..utils.apply_defaults import apply_defaults
from ..utils.large_hash import large_hash
from ..utils.metadata_tagging import add_metadata, read_metadata


# Conditional imports depending on whether a GPU is present
if "GPU" in dask.config.global_config["distributed"]["worker"]["resources"]:
    dask.config.set({"array.backend": "cupy"})
    from dask_cudf import dataframe as dd
else:
    from dask import dataframe as dd


class DataLoader(Base):
    def __init__(
        self,
        client=None,
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
            self.cluster = LocalCluster(n_workers=psutil.cpu_count()-1, threads_per_worker=2)
            self.cluster.adapt(minimum=1, maximum=psutil.cpu_count()-1)
        else:
            self.cluster = cluster
        if client is None:
            self.client = Client(self.cluster)
        else:
            self.client = client
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
        shutil.rmtree(self._data_cache)
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
            if acc > (self._memory_limit / 2): # NOTE: mem limit here is too large, is unoptimized. lowered to 1/2
                batches.append([])
                acc = file_size
            batches[-1].append(str(p))
        
        # Clear the cache so we can create a new one with the layers to be read
        for path in Path(self._data_cache).iterdir():
            if path.is_file():
                path.unlink(missing_ok=True)
            elif path.is_dir():
                shutil.rmtree(path)

        # Then read files (offloaded to local rust library "read_layers")
        for file_list in self.progressbar(batches, position=2):
            # Read each batch in rust to dask dataframe, then add df to compressed HDF5
            batch_df = dd.from_array(
                da.from_array(read_selected_layers(file_list)),
                columns=["x", "y", "z", "t", "rgb"],
            ).drop("rgb", axis=1) # The 'RGB' column is superfluous, as far as i can tell.
            batch_df.to_parquet(
                f"{self._data_cache}/working",
                compression="lz4",
                append=True,
                compute=True,
                write_metadata_file=True,
                ignore_divisions=True,
            )

        # if keeping raw data, copy raw files before modifying
        if self.keep_raw:
            shutil.copytree(f"{self._data_cache}/working", f"{self._data_cache}/raw")

        self.data = dd.read_parquet(f"{self._data_cache}/working")

        # If given a calibration curve, apply it
        if calibration_curve is not None:
            self.apply_calibration_curve(calibration_curve=calibration_curve)
        self.temp_units = temp_units

    def commit(self):
        # If data in working doesnt match current dataframe, create new file to replace working
        # if not (self.data == dd.read_parquet("cache/working",)).all().all().compute():
        commit_path = Path(f"{self._data_cache}/commit")
        working_path = Path(f"{self._data_cache}/working")
        if commit_path.exists():
            shutil.rmtree(commit_path)
        self.data.to_parquet(f"{self._data_cache}/commit", compression="lz4", write_metadata_file=True, compute=True)
        del self.data
        if working_path.exists():
            shutil.rmtree(working_path)
        commit_path.rename(f"{self._data_cache}/working")
        self.data = dd.read_parquet(f"{self._data_cache}/working")

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
        unmodified = large_hash(f"{self._data_cache}/working") == large_hash(f"{self._data_cache}/raw")
        if self.keep_raw and not unmodified:
            del self.data
            Path(f"{self._data_cache}/working").unlink(missing_ok=True)
            shutil.copytree(f"{self._data_cache}/raw", f"{self._data_cache}/working")
            self.data = dd.read_parquet(f"{self._data_cache}/working")
        elif self.keep_raw:
            self._qprint("keep_raw param is set to False, no changes have been applied")
        elif unmodified:
            self._qprint("working == raw, no changes have been applied")
    
    def _generate_metadata(self, path: Path | None = None, meta_dict: dict = {}) -> dict:
        if path is None:
            path = self._data_cache
        for f in Path(path).iterdir():
            rel_path = f.relative_to(self._data_cache)
            meta_dict[str(rel_path)] = {}
            meta_dict[str(rel_path)]["hash"] = large_hash(f)
            is_dir = f.is_dir()
            meta_dict[str(rel_path)]["is_dir"] = is_dir
            if is_dir:
                meta_dict = self._generate_metadata(f, meta_dict)
        return meta_dict
    
    @property
    def generate_metadata(self):
        return self._generate_metadata()

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
        meta = self.generate_metadata
        # Finally, compress the cache and its contents
        with tarfile.open(filepath, "w:gz") as tarball: # , compresslevel=5) as tarball:
            for p in self.progressbar(list(self._data_cache.iterdir())):
                tarball.add(p, arcname=p.name)
        add_metadata(filepath, meta)
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
                meta = read_metadata(filepath)
                if meta == self.generate_metadata:
                    self._qprint("Savefile matches current cache. Skipping load...")
                else:
                    # Finally, extract and replace cache files unless hashes prove files are identical
                    for member, fmeta in self.progressbar(meta.items()):
                        cache_path = Path(f"{self._data_cache}/{member}")
                        if not cache_path.exists() and fmeta["is_dir"]:
                            cache_path.mkdir(parents=True, exist_ok=True)
                        if fmeta["hash"] != large_hash(cache_path):
                            tarball.extract(member=member, path=self._data_cache)
                        else:
                            self._qprint(f"{member} matches existing cache. Skipping...")
            except Exception:
                self._qprint("Metadata corrupted! Attempting full overwrite...")
                shutil.rmtree(self._data_cache)
                self._data_cache.mkdir(parents=True, exist_ok=True)
                members = list(tarball.getmembers())
                for member in self.progressbar(members):
                    cache_path = Path(f"{self._data_cache}/{member}")
                    if "." in member.name:
                        cache_path.mkdir(parents=True, exist_ok=True)
                    tarball.extract(member=member, path=self._data_cache)
                
        # Finally, if present the attributes from the saved instance
        attr_path = Path(f"{self._data_cache}/attrs.pickle")
        if attr_path.exists():
            attrs = pickle.load(open(attr_path, "rb"))
            for k, v in attrs.items():
                if k in self.__dict__ and k != "cache":
                    self.__dict__[k] = v
        self.data = dd.read_parquet(f"{self._data_cache}/working")
        self._qprint("Data loaded!")
