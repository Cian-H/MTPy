"""Data handling and processing components of the MTPy module."""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from functools import partial
from io import BytesIO
from pathlib import Path
import pickle
import tarfile
from typing import Any, Dict, Optional, Tuple, cast

import dask
from dask.distributed import Client, LocalCluster, as_completed
from dask.distributed.deploy import Cluster
from fsspec import AbstractFileSystem
from fsspec.implementations.dirfs import DirFileSystem
from fsspec.implementations.local import LocalFileSystem
import psutil

from mtpy.base.abstract import AbstractBase
from mtpy.utils.large_hash import large_hash
from mtpy.utils.log_intercept import LoguruPlugin
from mtpy.utils.metadata_tagging import add_metadata, read_metadata
from mtpy.utils.tar_handling import entry_size, parse_header, uncompressed_tarfile_size, unpack_file
from mtpy.utils.types import CalibrationFunction, JSONData, PathMetadata, PathMetadataTree

# Conditional imports depending on whether a GPU is present
# Lots of type: ignore comments here because mypy is not happy with these conditional imports
if "GPU" in dask.config.global_config["distributed"]["worker"]["resources"]:
    dask.config.set({"array.backend": "cupy"})
    from dask_cudf import dataframe as dd
else:
    from dask import dataframe as dd


class AbstractLoader(AbstractBase, metaclass=ABCMeta):
    """A class for loading and preprocessing data."""

    __slots__ = [
        "_cache",
        "_cache_metadata",
        "_data_cache",
        "_data_cache_fs",
        "_file_suffix",
        "client",
        "cluster",
        "data",
        "fs",
        "temp_label",
        "temp_units",
    ]

    def __init__(
        self: "AbstractLoader",
        client: Optional[Client] = None,
        cluster: Optional[Cluster] = None,
        fs: Optional[AbstractFileSystem] = None,
        data_cache: Optional[Path | str] = "cache",
        cluster_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialisation of the data loader class.

        Args:
            client (Optional[Client], optional): A dask client to use for processing.
                Defaults to None.
            cluster (Optional[SpecCluster], optional): A dask cluster to use for processing.
                Defaults to None.
            fs (Optional[AbstractFileSystem], optional): The filesystem on which the data to be
                loaded can be found. If None will default to LocalFileSystem().
            data_cache (Optional[Path | str], optional): The directory in which working
                data will be stored. Defaults to "cache".
            cluster_config (Dict[str, Any], optional): The configuration parameters for the dask
                cluster. Defaults to {}.
            kwargs: Additional keyword arguments to be passed to the parent class (`Base`).
        """
        super().__init__()

        loguru_plugin = LoguruPlugin()

        if fs is None:
            fs = LocalFileSystem()
        if cluster_config is None:
            cluster_config = {}
        if data_cache is None:
            data_cache = Path().cwd()
        if (cluster is None) and (client is None):
            self.cluster: Cluster = LocalCluster(
                n_workers=(psutil.cpu_count() - 1 * 2),
                threads_per_worker=1,
                plugins=(loguru_plugin,),
            )
            self.cluster.adapt(minimum=1, maximum=(psutil.cpu_count() - 1 * 2))
        else:
            self.cluster = cluster
        if client is None:
            self.client = Client(self.cluster)
        else:
            self.client = client
        self.client.register_plugin(loguru_plugin)
        # Stores location from which to read data
        # Set default labels for t axis
        self.temp_label = "Pyrometer Response"
        self.temp_units = ""

        # Let's set up an empty data field, mostly for static checking purposes
        self.data = dd.DataFrame.from_dict({}, npartitions=1)
        # Set up file handling attributes
        self.fs = fs
        if isinstance(data_cache, str) and data_cache[-1] != "/":
            data_cache += "/"
        self._data_cache = data_cache
        self.fs.mkdirs(self._data_cache, exist_ok=True)
        self._data_cache_fs = DirFileSystem(path=self._data_cache, fs=self.fs)
        # Misc configuration attributes
        self._file_suffix = "mtp"

    def get_memory_limit(self: "AbstractLoader") -> int:
        """Get the memory limit for the current cluster.

        Args:
            self (DataLoader): The current DataLoader object.

        Returns:
            int: The memory limit for the current cluster in bytes.
        """
        if "_adaptive" in self.client.cluster.__dict__:
            nworkers = getattr(
                getattr(self.client.cluster, "_adaptive", None),
                "maximum",
                1,
            )
        return psutil.virtual_memory().total // (
            2
            * getattr(self.client.cluster, "_threads_per_worker", lambda: psutil.cpu_count() - 1)()
            * nworkers
        )  # aim to use half ram per worker

    @abstractmethod
    def construct_cached_ddf(
        self: "AbstractLoader", data_path: str, chunk_size: int = 3276800
    ) -> None:
        """Constructs a cached dask dataframe from the data at the specified path.

        Args:
            self (DataLoader): The current DataLoader object.
            data_path (str): The path to the target directory.
            chunk_size (int, optional): The chunk size for data storage once data is read. Defaults
                to 3276800 (~100MB chunks).

        Raises:
            TypeError: If the glob pattern is not a string.
        """
        ...

    def read_layers(
        self: "AbstractLoader",
        data_path: str,
        calibration_curve: Optional[CalibrationFunction] = None,
        temp_units: str = "mV",
        chunk_size: int = 3276800,  # chunk size calculated to result in ~100MB chunks
    ) -> None:
        """Reads layers from target directory.

        Args:
            data_path (str): Path to the target directory.
            calibration_curve (Optional[CalibrationFunction], optional):
                A calibration function to apply to a column. Defaults to None.
            temp_units (str, optional): Units for the temperature data to be read. Defaults to "mV".
            chunk_size (int, optional): The chunk size for data storage once data is read. Defaults
                to 3276800 (~100MB chunks).
        """
        if data_path[-1] != "/":
            data_path += "/"
        self.logger.info(f"Searching for files at {data_path}")
        self.construct_cached_ddf(data_path, chunk_size)

        # If given a calibration curve, apply it
        if calibration_curve is not None:
            self.apply_calibration_curve(calibration_curve=calibration_curve)
        self.temp_units = temp_units

    def commit(self: "AbstractLoader") -> None:
        """Commits working dataframe to cache."""
        # If data in working doesnt match current dataframe, create new file to replace working
        # if not (self.data == dd.read_parquet("cache/working",)).all().all().compute():
        commit_path = f"{self._data_cache}commit"
        working_path = f"{self._data_cache}working"
        if self.fs.exists(commit_path):
            self.fs.rm(commit_path, recursive=True)
        storage_options = getattr(self.fs, "storage_options", None)
        self.data.to_parquet(
            self.fs.unstrip_protocol(commit_path),
            storage_options=storage_options,
            compression="lz4",
            write_metadata_file=True,
            compute=True,
        )
        del self.data
        if self.fs.exists(working_path):
            self.fs.rm(working_path, recursive=True)
        self.fs.mv(commit_path, working_path, recursive=True)

        from mtpy.utils.type_guards import guarded_dask_dataframe

        self.data = guarded_dask_dataframe(
            dd.read_parquet(
                self.fs.unstrip_protocol(working_path),
                storage_options=storage_options,
                parquet_file_extension=".parquet",
            )
        )

    def apply_calibration_curve(
        self: "AbstractLoader",
        calibration_curve: Optional[CalibrationFunction] = None,
        temp_column: Optional[str] = "t",
        units: Optional[str] = None,
    ) -> None:
        """Applies a calibration curve to the current dataframe.

        Args:
            calibration_curve (Optional[CalibrationFunction], optional):
                A calibration function to apply to a column. Defaults to None.
            temp_column (str, optional): The target column for the calibration_curve to be applied
                to. Defaults to "t".
            units (optional[str], optional): The units of the resulting column. Will stay the same
                if given None. Defaults to None.
        """
        # if a calibration curve is given
        if calibration_curve is not None:
            # Set temp_column to calibrated values
            self.logger.info("Applying calibration curve")
            self.data[temp_column] = calibration_curve(
                self.data["x"],
                self.data["y"],
                self.data["z"],
                self.data[temp_column],
            )
            self.commit()
            if units is not None:
                self.temp_units = units
            self.logger.info("Calibrated!")
        # otherwise, set to raw values from datafiles
        else:
            self.logger.info("No calibration curve given!")

    def reload_raw(self: "AbstractLoader") -> None:
        """Reloads the raw data from the cache, replacing the current dataframe."""
        working_path = f"{self._data_cache}working"
        raw_path = f"{self._data_cache}raw"
        unmodified = self.fs.checksum(working_path) == self.fs.checksum(raw_path)
        storage_options = getattr(self.fs, "storage_options", None)
        if not unmodified:
            del self.data
            self.fs.rm(working_path, recursive=True)
            self.fs.cp(raw_path, working_path, recursive=True)

            from mtpy.utils.type_guards import guarded_dask_dataframe

            self.data = guarded_dask_dataframe(
                dd.read_parquet(
                    self.fs.unstrip_protocol(working_path),
                    storage_options=storage_options,
                    parquet_file_extension=".parquet",
                )
            )
        elif unmodified:
            self.logger.info("working == raw, no changes have been applied")

    def tree_metadata(
        self: "AbstractLoader",
        path: Optional[str] = None,
        meta_dict: Optional[PathMetadataTree] = None,
    ) -> PathMetadataTree:
        """Generates a tree of metadata for the specified path in the cache.

        Args:
            path (Optional[str], optional): The path to generate metadata for. Defaults to None.
            meta_dict (Optional[Dict[str, str]], optional): An existing metadata dict to add the
                data to. Defaults to None.

        Returns:
            dict: An amended dict of metadata for the specified path.
        """
        if meta_dict is None:
            meta_dict = {}
        for f in self.fs.glob(f"{path}*"):
            if isinstance(f, Path):
                f_as_str = str(f)
            elif not isinstance(f, str):
                msg = "This code is only intended to work with single pattern globs."
                raise TypeError(msg)
            else:
                f_as_str = f
            rel_path = f_as_str.replace(str(self._data_cache), "")
            is_dir = self.fs.stat(f_as_str)["type"] == "directory"
            path_metadata = PathMetadata(
                hash=large_hash(self.fs, f_as_str),
                is_dir=is_dir,
                size=self.fs.size(f_as_str),
            )
            # type: ignore # This is happening becuase python doesn't support recursive types
            meta_dict[rel_path] = path_metadata
            if is_dir:
                meta_dict = self.tree_metadata(f"{f_as_str}/", meta_dict)
        return meta_dict

    def generate_metadata(self: "AbstractLoader", path: Optional[str] = None) -> PathMetadataTree:
        """Generates a metadata dictionary for the current cache.

        Args:
            path (Optional[str], optional): The path to the cache target.
                If None, generates for entire cache. Defaults to None.

        Returns:
            JSONDict: A metadata dict for the specified cache path.
        """
        if path is None:
            path = str(self._data_cache)
        meta_dict = {}
        meta_dict["size"] = sum(self.fs.sizes(self.fs.find(path)))
        meta_dict["tree"] = self.tree_metadata(path)
        meta_dict["archive_size"] = uncompressed_tarfile_size(meta_dict["tree"])
        return meta_dict

    # return metadata for the cache.
    # Caches last metadata result based on checksum of entire cache folder
    @property
    def cache_metadata(self: "AbstractLoader") -> PathMetadataTree:
        """A property containing the entire metadata dict for the current cache.

        Returns:
            PathMetadataTree: A metadata dict for the entire cache
        """
        # Check if cache has been modified since last metadata generation.
        # If so, regenerate metadata. Otherwise, return cached metadata.
        if hasattr(self, "_cache_metadata"):
            cur_hash = large_hash(self.fs, str(self._data_cache))
            if self._cache_metadata[0] != cur_hash:
                self._cache_metadata: Tuple[int, PathMetadataTree] = (
                    cur_hash,
                    self.generate_metadata(),
                )
        else:
            self._cache_metadata = (
                large_hash(self.fs, str(self._data_cache)),
                self.generate_metadata(),
            )
        return self._cache_metadata[1]

    def save(self: "AbstractLoader", filepath: Path | str = Path("data")) -> None:
        """Save current MTPy session to a file.

        Args:
            filepath (Path | str, optional): _description_.
                Defaults to Path(f"data.{self._file_suffix}").
        """
        self.logger.info("Saving data...")
        # First, commit any pending changes
        self.commit()
        # Process filename before saving
        if isinstance(filepath, Path):
            filepath = str(filepath)
        if filepath.split(".")[-1] != self._file_suffix:
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
            self.logger.info(f"{filepath} already exists! Saving as {p}...")
            filepath = p
        # Add pickled self.__dict__ (not including temporary attrs) to the data cache
        attrs = self.__dict__.copy()
        for k in ("cluster", "client", "cache", "views"):
            if k in attrs:
                del attrs[k]
        pickle.dump(attrs, self.fs.open(f"{self._data_cache}attrs.pickle", "wb+"))
        # Get cache metadata, and store to tag onto tail of savefile
        metadata = self.cache_metadata
        # Finally, compress the cache and its contents
        with tarfile.open(filepath, mode="w:gz") as tarball:
            for f in self.progressbar(self.fs.get_mapper(str(self._data_cache))):
                with self.fs.open(f"{self._data_cache}{f}", "rb") as cache_file:
                    # Type checker is wrong below. The attribute `f` DEFINITELY exists here
                    fileobj = BytesIO(cache_file.f.read())
                    tarinfo = tarfile.TarInfo(name=f"{f}")
                    tarinfo.size = fileobj.getbuffer().nbytes
                    tarball.addfile(tarinfo, fileobj=fileobj)

        from mtpy.utils.type_guards import guarded_json_data

        # metadata will be used to accelerate unpacking
        add_metadata(self.fs, filepath, guarded_json_data(metadata))
        self.logger.info("Data saved!")

    def _extract_cache(
        self: "AbstractLoader",
        end: int,
        filepath: str,
        blocksize: int,
        tree_metadata: PathMetadataTree,
    ) -> None:
        """Extracts the cache from the specified file.

        Args:
            self (DataLoader): The current DataLoader object.
            end (int): The end of the file to extract.
            filepath (str): The path to the target file.
            blocksize (int): The blocksize for streaming when unpacking the file.
            tree_metadata (PathMetadataTree): The metadata for the cache to be extracted.
        """
        pbar = self.progressbar(total=end)
        seekpos = 0
        prev_null = False
        queue = []
        with self.fs.open(filepath, mode="rb", compression="gzip") as t:
            # cast here because since mode="rb" we know this will be bytes
            while header := cast(bytes, t.read(blocksize)):
                seekpos += blocksize
                for byte in header:
                    if byte != 0:
                        break
                else:  # I hate the for-else syntax but it makes sense to use here :/
                    if prev_null:
                        break
                    prev_null = True
                    continue
                prev_null = False
                entry_name = parse_header(header)["name"]
                unpack_target = f"{entry_name}"
                size = tree_metadata[f"{self.fs.info(self._data_cache)['name'][:-5]}{entry_name}"][
                    "size"
                ]
                size = entry_size(size, blocksize)
                if self._data_cache_fs.exists(unpack_target):
                    if self._data_cache_fs.isfile(unpack_target):
                        chk = tree_metadata.get(
                            unpack_target,
                            PathMetadata(hash=0, is_dir=False, size=0),
                        )["hash"]
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
        futures = self.client.map(unpack_archive_entry, *zip(*queue, strict=False), retries=None)
        for _, readsize in as_completed(futures, with_results=True):
            pbar.update(readsize)

    def _unpack_savefile(self: "AbstractLoader", filepath: str, blocksize: int = 512) -> None:
        """Unpacks the specified savefile into the current cache.

        Unpacks the specified savefile into the current cache directory. Unmodified files are
        skipped based on saved hashing values.

        Args:
            filepath (str): path to the savefile to unpack
            blocksize (int, optional): blocksize for streaming when unpacking the
                file. Defaults to 512.

        Raises:
            no_metadata: no metadata is found in the target file
        """
        metadata_tag: Optional[JSONData] = None
        try:
            # Check for hash metadata tagged onto file
            metadata_tag = read_metadata(self.fs, filepath)
        except Exception as no_metadata:
            raise no_metadata
        if metadata_tag == self.cache_metadata:
            self.logger.info("Savefile matches current cache. Skipping load...")
            return

        from mtpy.utils.type_guards import guarded_int, guarded_json_dict, guarded_pathmetadatatree

        metadata = guarded_json_dict(metadata_tag)
        end = guarded_int(metadata["archive_size"])
        tree_metadata: PathMetadataTree = guarded_pathmetadatatree(metadata["tree"])
        for k, v in tree_metadata.items():
            if v["is_dir"]:
                k_path = k[len(self.fs.info(self._data_cache)["name"][:-5]) :]
                self.fs.mkdirs(k_path, exist_ok=True)
        self._extract_cache(end, filepath, blocksize, tree_metadata)

    def load(self: "AbstractLoader", filepath: Path | str = Path("data")) -> None:
        """Loads the saved MTPy session from the specified file.

        Args:
            filepath (Path | str, optional): Path to the target file.
                Defaults to Path(f"data.{self._file_suffix}").
        """
        self.logger.info("Loading data...")
        # Process filename before saving
        if type(filepath) is Path:
            filepath = str(filepath)
        self.fs.mkdirs(self._data_cache, exist_ok=True)

        self._unpack_savefile(str(filepath))

        # Finally, if present, load attributes from the saved instance
        attr_path = Path(f"{self._data_cache}attrs.pickle")
        if attr_path.exists():
            attrs = pickle.load(attr_path.open("rb"))
            for k, v in attrs.items():
                if k in self.__dict__ and k != "cache":
                    self.__dict__[k] = v

        working_path = f"{self._data_cache}working"

        from mtpy.utils.type_guards import guarded_dask_dataframe

        self.data = guarded_dask_dataframe(
            dd.read_parquet(
                working_path,
                storage_options=getattr(self.fs, "storage_options", None),
                parquet_file_extension=".parquet",
            )
        )
        self.logger.info("Data loaded!")