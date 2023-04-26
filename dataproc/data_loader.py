#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import pickle
import tarfile
from functools import partial
from io import BytesIO
from itertools import repeat
from pathlib import Path
from types import FunctionType, SimpleNamespace

import dask
import psutil
from dask import array as da
from dask.distributed import Client, LocalCluster, as_completed
from fsspec.implementations.local import LocalFileSystem
from fsspec.implementations.dirfs import DirFileSystem

from read_layers import read_selected_layers

from ..common.base import Base
from ..utils.large_hash import large_hash
from ..utils.metadata_tagging import add_metadata, read_metadata
from ..utils.tar_handling import entry_size, parse_header, uncompressed_tarfile_size, unpack_file

# Conditional imports depending on whether a GPU is present
if "GPU" in dask.config.global_config["distributed"]["worker"]["resources"]:
    dask.config.set({"array.backend": "cupy"})
    from dask_cudf import dataframe as dd
else:
    from dask import dataframe as dd


class DataLoader(Base):
    """A class for loading and preprocessing data."""

    def __init__(
        self,
        client=None,
        cluster=None,
        fs=LocalFileSystem(),
        data_cache: Path | str | None = "cache",
        cluster_config: dict = {},
        **kwargs,
    ):
        """Initialisation of the data loader class.

        Args:
            client: A dask client to use for processing. Defaults to None.
            cluster: A dask cluster to use for processing. Defaults to None.
            fs: The filesystem on which the data to be loaded can be found.
                Defaults to LocalFileSystem().
            data_cache (Path | str | None, optional): The directory in which working
                data will be stored. Defaults to "cache".
            cluster_config (dict, optional): The configuration parameters for the dask
                cluster. Defaults to {}.
        """
        super().__init__(
            **kwargs,
        )
        if data_cache is None:
            data_cache = Path().cwd()
        if cluster is None:
            self.cluster = LocalCluster(
                n_workers=(psutil.cpu_count() - 1 * 2), threads_per_worker=1
            )
            self.cluster.adapt(minimum=1, maximum=(psutil.cpu_count() - 1 * 2))
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
        self._cache = (
            SimpleNamespace()
        )  # NOTE: DEPRECATED! Left it because i cant remember if its needed in the GUI application.
        # If unneeded will delete later.
        # Set up file handling attributes
        self.fs = fs
        if data_cache[-1] != "/":
            data_cache += "/"
        self._data_cache = data_cache
        self.fs.mkdirs(self._data_cache, exist_ok=True)
        self._data_cache_fs = DirFileSystem(path=self._data_cache, fs=self.fs)
        # Misc configuration attributes
        self._file_suffix = "mtp"

    def __del__(self, **kwargs):
        """Cloases the dask client and cluster, then deletes the cache directory."""
        # Close dask cluster and client
        # TODO: bug here if user passes dask client and intends to continue using outside MTPy?
        # Without this code though, dask clients could be left causing mem leaks.
        # Need to find a solution
        self.cluster.close()
        self.client.close()
        # Delete cache files if still present
        self.fs.rm(self._data_cache, recursive=True)
        # super().__del__(**kwargs) # Not needed currently, but will be if __del__ added to parent

    def read_layers(
        self,
        data_path: str,
        calibration_curve: FunctionType | None = None,
        temp_units: str = "mV",
        chunk_size: int = 3276800,  # chunk size calculated to result in ~100MB chunks
    ):
        """Reads layers from target directory.

        Args:
            data_path (str): Path to the target directory.
            calibration_curve (FunctionType | None, optional): Calibration curve for the data being
                read. Defaults to None.
            temp_units (str, optional): Units for the temperature data to be read. Defaults to "mV".
            chunk_size (int, optional): The chunk size for data storage once data is read. Defaults
                to 3276800.
        """
        if data_path[-1] != "/":
            data_path += "/"
        self._qprint(f"\nSearching for files at {data_path}")
        # Calculate read batches
        batches = [[]]
        acc = 0
        data_fs = DirFileSystem(path=data_path, fs=self.fs)
        # Prepare batches of files wtih total size less than memory_limit to read at once
        for p in sorted(
            data_fs.glob("*.pcd", detail=False), key=lambda x: float(x.split("/")[-1].split(".")[0])
        ):
            file_size = data_fs.size(p.strip("/"))
            try:
                mem_limit = self.cluster._memory_per_worker() // 4
            except AttributeError:
                if "_adaptive" in self.cluster.__dict__:
                    nworkers = getattr(self.cluster._adaptive, "maximum", psutil.cpu_count())
                mem_limit = psutil.virtual_memory().total // (
                    2 * self.cluster._threads_per_worker() * nworkers
                )  # aim to use half ram per worker
            assert file_size < (mem_limit), "File size too large for available RAM!"
            acc += file_size
            if acc > mem_limit:
                batches.append([])
                acc = file_size
            batches[-1].append(p)

        # Clear the cache so we can create a new one with the layers to be read
        self.fs.rm(self._data_cache, recursive=True)
        self.fs.mkdirs(f"{self._data_cache}arr", exist_ok=True)

        # Then read files (offloaded to local rust library "read_layers")
        if self.fs.protocol == "file":
            local_fs = self.fs
            read_arr_cache = f"{self._data_cache}/tmp_arr"
        else:
            local_fs = LocalFileSystem()
            read_arr_cache = "tmp_arr"
        local_fs.mkdirs(read_arr_cache, exist_ok=True)
        arr_cache_fs = DirFileSystem(path=read_arr_cache, fs=local_fs)
        for i, file_list in enumerate(self.progressbar(batches, position=2)):
            # Read each batch in rust to dask dataframe, then add df to compressed parquet table
            npy_stack_subdir = str(i)
            arr_cache_fs.mkdirs(npy_stack_subdir, exist_ok=True)

            local_file_list = [
                f"{read_arr_cache}{x}" for x in (x if x[1] == "/" else f"/{x}" for x in file_list)
            ]
            data_fs.get(
                file_list, local_file_list
            )  # maybe making this async would speed up process?
            data = read_selected_layers(local_file_list)
            darr = da.from_array(
                data,
                chunks=(
                    (
                        *tuple(repeat(chunk_size, data.shape[0] // chunk_size)),
                        data.shape[0] % chunk_size,
                    ),
                    *((x,) for x in data.shape[1:]),
                ),
            )
            da.to_npy_stack(
                f"{read_arr_cache}/{npy_stack_subdir}",
                darr,
                # storage_options=self.fs.storage_options
            )
            arr_cache_fs.rm(arr_cache_fs.glob("*.pcd"))

        darrays = []

        for npy_stack in local_fs.ls(read_arr_cache):
            darrays.append(
                da.from_npy_stack(
                    npy_stack,
                    # storage_options=self.fs.storage_options
                )
            )

        data = da.concatenate(darrays)
        data = data.rechunk(balance=True)

        self.fs.mkdirs(f"{self._data_cache}raw", exist_ok=True)

        ddf = dd.from_array(
            data,
            columns=["x", "y", "z", "t", "rgb"],
        ).drop(
            "rgb", axis=1
        )  # The 'RGB' column is superfluous, as far as i can tell.
        target_options = self.fs.storage_options.get("target_options", self.fs.storage_options)
        ddf.to_parquet(
            self.fs.unstrip_protocol(f"{self._data_cache}raw"),
            storage_options=target_options,
            compression="lz4",
            append=True,
            compute=True,
            write_metadata_file=True,
            ignore_divisions=True,
        )

        local_fs.rm(read_arr_cache, recursive=True)
        self.fs.mkdirs(f"{self._data_cache}working", exist_ok=True)

        # if keeping raw data, copy raw files before modifying
        self.fs.cp(f"{self._data_cache}raw", f"{self._data_cache}working", recursive=True)

        self.data = dd.read_parquet(
            self.fs.unstrip_protocol(f"{self._data_cache}working"),
            storage_options=self.fs.storage_options,
            parquet_file_extension=".parquet",
        )

        # If given a calibration curve, apply it
        if calibration_curve is not None:
            self.apply_calibration_curve(calibration_curve=calibration_curve)
        self.temp_units = temp_units

    def commit(self):
        """Commits working dataframe to cache."""
        # If data in working doesnt match current dataframe, create new file to replace working
        # if not (self.data == dd.read_parquet("cache/working",)).all().all().compute():
        commit_path = f"{self._data_cache}commit"
        working_path = f"{self._data_cache}working"
        if self.fs.exists(commit_path):
            self.fs.rm(commit_path, recursive=True)
        self.data.to_parquet(
            self.fs.unstrip_protocol(commit_path),
            storage_options=self.fs.storage_options,
            compression="lz4",
            write_metadata_file=True,
            compute=True,
        )
        del self.data
        if self.fs.exists(working_path):
            self.fs.rm(working_path, recursive=True)
        self.fs.mv(commit_path, working_path, recursive=True)
        self.data = dd.read_parquet(
            self.fs.unstrip_protocol(working_path),
            storage_options=self.fs.storage_options,
            parquet_file_extension=".parquet",
        )

    def apply_calibration_curve(
        self,
        calibration_curve: FunctionType | None = None,
        temp_column: str = "t",
        units: str | None = None,
    ):
        """Applies a calibration curve to the current dataframe

        Args:
            calibration_curve (FunctionType | None, optional): A calibration function to apply to a
                column. Defaults to None.
            temp_column (str, optional): The target column for the calibration_curve to be applied
                to. Defaults to "t".
            units (str | None, optional): The units of the resulting column. Will stay the same
                if given None. Defaults to None.
        """
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
        """Reloads the raw data from the cache, replacing the current dataframe."""
        working_path = f"{self._data_cache}working"
        raw_path = f"{self._data_cache}raw"
        unmodified = self.fs.checksum(working_path) == self.fs.checksum(raw_path)
        if not unmodified:
            del self.data
            self.fs.rm(working_path, recursive=True)
            self.fs.cp(raw_path, working_path, recursive=True)
            self.data = dd.read_parquet(
                self.fs.unstrip_protocol(working_path),
                storage_options=self.fs.storage_options,
                parquet_file_extension=".parquet",
            )
        elif unmodified:
            self._qprint("working == raw, no changes have been applied")

    def tree_metadata(self, path: str | None = None, meta_dict: dict | None = None) -> dict:
        """Generates a dictionary of metadata for the specified path in the cache.

        Args:
            path (str | None, optional): The path to generate metadata for. Defaults to None.
            meta_dict (dict | None, optional): An existing metadata dict to add the data to.
                Defaults to None.

        Returns:
            dict: An amended dict of metadata for the specified path.
        """
        if meta_dict is None:
            meta_dict = {}
        for f in self.fs.glob(f"{path}*"):
            rel_path = f.replace(self._data_cache, "")
            meta_dict[rel_path] = {}
            meta_dict[rel_path]["hash"] = large_hash(self.fs, f)
            is_dir = self.fs.stat(f)["type"] == "directory"
            meta_dict[rel_path]["is_dir"] = is_dir
            meta_dict[rel_path]["size"] = self.fs.size(f)
            if is_dir:
                meta_dict = self.tree_metadata(f"{f}/", meta_dict)
        return meta_dict

    def generate_metadata(self, path: str | None = None) -> dict:
        """Generates a metadata dictionary for the current cache.

        Args:
            path (str | None, optional): The path to the cache target.
                If None, generates for entire cache. Defaults to None.

        Returns:
            dict: A metadata dict for the specified cache path.
        """
        if path is None:
            path = self._data_cache
        meta_dict = {}
        meta_dict["size"] = sum(self.fs.sizes(self.fs.find(path)))
        meta_dict["tree"] = self.tree_metadata(path)
        meta_dict["archive_size"] = uncompressed_tarfile_size(meta_dict["tree"])
        return meta_dict

    # return metadata for the cache.
    # Caches last metadata result based on checksum of entire cache folder
    @property
    def cache_metadata(self) -> dict:
        """A property containing the entire metadata dict for the current cache.

        Returns:
            dict: A metadata dict for the entire cache
        """
        # Check if cache has been modified since last metadata generation.
        # If so, regenerate metadata. Otherwise, return cached metadata.
        if hasattr(self, "_cache_metadata"):
            cur_hash = large_hash(self.fs, self._data_cache)
            if self._cache_metadata[0] != cur_hash:
                self._cache_metadata = (cur_hash, self.generate_metadata())
        else:
            self._cache_metadata = (large_hash(self.fs, self._data_cache), self.generate_metadata())
        return self._cache_metadata[1]

    def save(self, filepath: Path | str = Path("data")):
        f"""Save current MTPy session to a file.

        Args:
            filepath (Path | str, optional): _description_.
                Defaults to Path("data.{self._file_suffix}").
        """
        self._qprint("Saving data...")
        # First, commit any pending changes
        self.commit()
        # Process filename before saving
        if type(filepath) is Path:
            filepath = str(filepath)
        if not filepath.split(".")[-1] == self._file_suffix:
            if filepath[-1] != ".":
                filepath += "."
            filepath += self._file_suffix
        # Check if file exists, if does save with lowest available number added
        p = filepath
        i = 1
        while self.fs.exists(p):
            p = f"{filepath[:-4]}({i}){filepath[-4:]}"
            i += 1
        if filepath != p:
            self._qprint(f"{filepath} already exists! Saving as {p}...")
            filepath = p
        # Add pickled self.__dict__ (not including temporary attrs) to the data cache
        attrs = self.__dict__.copy()
        if "cluster" in attrs:
            del attrs["cluster"]
        if "client" in attrs:
            del attrs["client"]
        if "cache" in attrs:
            del attrs["cache"]
        if "views" in attrs:
            del attrs["views"]
        pickle.dump(attrs, self.fs.open(f"{self._data_cache}attrs.pickle", "wb+"))
        # Get cache metadata, and store to tag onto tail of savefile
        metadata = self.cache_metadata
        # Finally, compress the cache and its contents
        with tarfile.open(filepath, mode="w:gz") as tarball:
            for f in self.progressbar(self.fs.get_mapper(self._data_cache)):
                with self.fs.open(f"{self._data_cache}{f}", "rb") as cache_file:
                    fileobj = BytesIO(cache_file.f.read())
                    tarinfo = tarfile.TarInfo(name=f"{f}")
                    tarinfo.size = fileobj.getbuffer().nbytes
                    tarball.addfile(tarinfo, fileobj=fileobj)
        add_metadata(self.fs, filepath, metadata)  # metadata will be used to accelerate unpacking
        self._qprint("Data saved!")

    def _unpack_savefile(self, filepath: str, blocksize: int = 512):
        """Unpacks the specified savefile into the current cache.
        Unmodified files are skipped.

        Args:
            filepath (str): path to the savefile to unpack
            blocksize (int, optional): blocksize for streaming when unpacking the
                file. Defaults to 512.

        Raises:
            no_metadata: no metadata is found in the target file
        """
        metadata = {}
        try:
            # Check for hash metadata tagged onto file
            metadata = read_metadata(self.fs, filepath)
            end = metadata["archive_size"]
        except Exception as no_metadata:
            raise no_metadata
        if metadata == self.cache_metadata:
            self._qprint("Savefile matches current cache. Skipping load...")
            return
        end = metadata["archive_size"]
        tree_metadata = metadata["tree"]
        for k, v in tree_metadata.items():
            if v["is_dir"]:
                k = k[len(self.fs.info(self._data_cache)["name"][:-5]) :]  # TEMP PATCH
                self.fs.mkdirs(k, exist_ok=True)
        pbar = self.progressbar(total=end)
        seekpos = 0
        prev_null = False
        queue = []
        with self.fs.open(filepath, mode="rb", compression="gzip") as t:
            while header := t.read(blocksize):
                seekpos += blocksize
                for byte in header:
                    if byte != 0:
                        break
                else:  # I hate the for-else syntax but it makes sense to use here :/
                    if prev_null:
                        break
                    else:
                        prev_null = True
                        continue
                prev_null = False
                entry_name = parse_header(header)["name"]
                unpack_target = f"{entry_name}"
                size = tree_metadata[f"{self.fs.info(self._data_cache)['name'][:-5]}{entry_name}"][
                    "size"
                ]  # TEMP PATCH
                size = entry_size(size, blocksize)
                if self._data_cache_fs.exists(unpack_target):
                    if self._data_cache_fs.isfile(unpack_target):
                        chk = tree_metadata.get(unpack_target, dict()).get("hash", None)
                        if chk != large_hash(self._data_cache_fs, unpack_target):
                            self._data_cache_fs.rm(unpack_target)
                            queue.append(
                                (
                                    unpack_target,
                                    seekpos,
                                    size,
                                )
                            )
                else:
                    queue.append(
                        (
                            unpack_target,
                            seekpos,
                            size,
                        )
                    )
                seekpos += size
                pbar.update(blocksize)
                t.seek(seekpos, 0)
        unpack_archive_entry = partial(unpack_file, self.fs, filepath, self._data_cache_fs)
        futures = self.client.map(unpack_archive_entry, *zip(*queue), retries=None)
        for _, readsize in as_completed(futures, with_results=True):
            pbar.update(readsize)

    def load(self, filepath: Path | str = Path("data")):
        f"""Loads the saved MTPy session from the specified file.

        Args:
            filepath (Path | str, optional): Path to the target file.
                Defaults to Path("data.{self._file_suffix}").
        """
        self._qprint("Loading data...")
        # Process filename before saving
        if type(filepath) is Path:
            filepath = str(filepath)
        self.fs.mkdirs(self._data_cache, exist_ok=True)

        self._unpack_savefile(filepath)

        # Finally, if present, load attributes from the saved instance
        attr_path = Path(f"{self._data_cache}attrs.pickle")
        if attr_path.exists():
            attrs = pickle.load(open(attr_path, "rb"))
            for k, v in attrs.items():
                if k in self.__dict__ and k != "cache":
                    self.__dict__[k] = v

        working_path = f"{self._data_cache}working"
        self.data = dd.read_parquet(
            self._data_cache_fs.unstrip_protocol(working_path),
            storage_options=self.fs.storage_options,
            parquet_file_extension=".parquet",
        )
        self._qprint("Data loaded!")
