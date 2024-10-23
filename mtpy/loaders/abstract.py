"""Data handling and processing components of the MTPy module."""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from functools import partial
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import dask
from dask.distributed import Client, LocalCluster, as_completed
from dask.distributed.deploy import Cluster
import flatbuffers
from fsspec import AbstractFileSystem
from fsspec.implementations.dirfs import DirFileSystem
from fsspec.implementations.local import LocalFileSystem
import h5py
import psutil

from mtpy.base.abstract import AbstractBase
from mtpy.utils.hdf5_operations import read_bytes_from_hdf_dataset, write_bytes_to_hdf_dataset
from mtpy.utils.large_hash import large_hash
from mtpy.utils.log_intercept import LoguruPlugin
from mtpy.utils.metadata_tagging import read_tree_metadata
from mtpy.utils.tree_metadata import Metadata, Sha1, TreeFile
from mtpy.utils.type_guards import guarded_bytearray
from mtpy.utils.types import CalibrationFunction, PathMetadata, PathMetadataTree

# Conditional imports depending on whether a GPU is present
# Lots of type: ignore comments here because mypy is not happy with these conditional imports
if "GPU" in dask.config.global_config["distributed"]["worker"]["resources"]:
    dask.config.set({"array.backend": "cupy"})
    from dask_cudf import dataframe as dd
else:
    from dask import dataframe as dd


class AbstractLoader(AbstractBase, metaclass=ABCMeta):
    """A class for loading and preprocessing data.

    Args:
        client (Optional[Client], optional): A dask client to use for processing.
            Defaults to None.
        cluster (Optional[Cluster], optional): A dask cluster to use for processing.
            Defaults to None.
        fs (Optional[AbstractFileSystem], optional): The filesystem on which the data to be
            loaded can be found. If None will default to LocalFileSystem().
        data_cache (Optional[Path | str], optional): The directory in which working
            data will be stored. Defaults to "cache".
        cluster_config (Optional[Dict[str, Any]], optional): The configuration parameters for the
            dask cluster. Defaults to {}.
    """

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
        super().__init__()

        loguru_plugin = LoguruPlugin()

        if fs is None:
            fs = LocalFileSystem()
        if cluster_config is None:
            cluster_config = {}
        if data_cache is None:
            data_cache = Path().cwd()
        if client is None:
            if cluster is None:
                cluster = LocalCluster(
                    n_workers=(psutil.cpu_count() - 1 * 2),
                    threads_per_worker=1,
                    plugins=(loguru_plugin,),
                )
                cluster.adapt(minimum=1, maximum=(psutil.cpu_count() - 1 * 2))
            self.cluster: Cluster = cluster
            self.client: Client = Client(self.cluster)
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
        self._file_suffix = "hdf5"

    def get_memory_limit(self: "AbstractLoader") -> int:
        """Get the memory limit for the current cluster.

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
            temp_column (Optional[str], optional): The target column for the calibration_curve to be
                applied to. Defaults to "t".
            units (Optional[str], optional): The units of the resulting column. Will stay the same
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
            meta_dict (Optional[PathMetadataTree], optional): An existing metadata dict to add the
                data to. Defaults to None.

        Returns:
            PathMetadataTree: An amended dict of metadata for the specified path.

        Raises:
            TypeError: If a path search results in an invalid file during iteration.
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
            rel_path = self.filepath_relative_to_cache(f_as_str)
            is_dir = self.fs.stat(f_as_str)["type"] == "directory"
            path_metadata = PathMetadata(
                hash=large_hash(self.fs, f_as_str),
                is_dir=is_dir,
                size=self.fs.size(f_as_str),
            )
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
            PathMetadataTree: A metadata dict for the specified cache path.
        """
        if path is None:
            path = str(self._data_cache)
        meta_dict = {}
        meta_dict["size"] = sum(self.fs.sizes(self.fs.find(path)))
        meta_dict["tree"] = self.tree_metadata(path)
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
        filepath_obj = Path(filepath)
        # Check if file exists, if does save with lowest available number added
        p = filepath
        i = 1
        while self.fs.exists(p):
            p = str(filepath_obj.parent / f"{filepath_obj.stem}({i}){filepath_obj.suffix}")
            i += 1
        if filepath != p:
            self.logger.info(f"{filepath} already exists! Saving as {p}...")
            filepath = p
        # metadata will be used to accelerate unpacking
        metadata = self.cache_metadata
        # Finally, compress the cache and its contents
        self.fs.touch(filepath)
        # To do this, add metadata
        with h5py.File(self.fs.open(filepath, mode="wb"), mode="w") as hdf:
            cache_group = hdf.create_group("cache")
            write_bytes_to_hdf_dataset(
                cache_group, "metadata", self.create_metadata_buffer(metadata)
            )
        # Then add working data
        self.data.to_hdf(self.fs.open(filepath), "cache/data/working")
        # Lastly, add raw data
        storage_options = getattr(self.fs, "storage_options", None)
        raw_path = f"{self._data_cache}raw"
        dd.read_parquet(
            self.fs.unstrip_protocol(raw_path),
            storage_options=storage_options,
            parquet_file_extension=".parquet",
        ).to_hdf(self.fs.open(filepath), "cache/data/raw")
        self.logger.info("Data saved!")

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
        metadata_tag: Optional[PathMetadataTree] = None
        try:
            # Check for hash metadata tagged onto file
            metadata_tag = read_tree_metadata(self.fs, filepath)
        except Exception as no_metadata:
            raise no_metadata
        if metadata_tag == self.cache_metadata:
            self.logger.info("Savefile matches current cache. Skipping load...")
            return

        from mtpy.utils.type_guards import guarded_json_dict, guarded_pathmetadatatree

        metadata = guarded_json_dict(metadata_tag)
        tree_metadata: PathMetadataTree = guarded_pathmetadatatree(metadata["tree"])
        for k, v in tree_metadata.items():
            if v["is_dir"]:
                k_path = k[len(self.fs.info(self._data_cache)["name"][:-5]) :]
                self.fs.mkdirs(k_path, exist_ok=True)
        self._extract_cache(filepath, blocksize, tree_metadata)

    @staticmethod
    def _unpack_file(
        fs: AbstractFileSystem, save_filepath: str, unpack_filepath: str, size: int
    ) -> int:
        with h5py.File(fs.open(save_filepath), "r") as hdf, Path(unpack_filepath).open("wb") as f:
            f.write(read_bytes_from_hdf_dataset(hdf["cache"]["tree"][unpack_filepath]))
        return size

    def _extract_cache(
        self: "AbstractLoader",
        filepath: str,
        blocksize: int,
        tree_metadata: PathMetadataTree,
    ) -> None:
        """Extracts the cache from the specified file.

        Args:
            filepath (str): The path to the target file.
            blocksize (int): The blocksize for streaming when unpacking the file.
            tree_metadata (PathMetadataTree): The metadata for the cache to be extracted.
        """
        pbar = self.progressbar(total=sum(v["size"] for k, v in tree_metadata.items()))
        queue = [
            (filepath, metadata["size"])
            for save_filepath, metadata in tree_metadata.items()
            if metadata["hash"] != self.cache_metadata["tree"]["hash"]
        ]
        unpack_archive_entry = partial(self._unpack_file, self.fs, filepath, self._data_cache_fs)
        futures = self.client.map(unpack_archive_entry, *zip(*queue, strict=False), retries=None)
        for _, readsize in as_completed(futures, with_results=True):
            pbar.update(readsize)

    def filepath_relative_to_cache(self: "AbstractLoader", filepath: str) -> str:
        """Converts a filepath to be relative to the current cache.

        Args:
            filepath (str): The filepath to be converted.

        Returns:
            str: The filepath relative to the current cache folder.
        """
        return str(Path(filepath).relative_to(Path(self._data_cache).resolve()))

    @staticmethod
    def create_tree_file(builder: flatbuffers.Builder, path: str, file_meta: PathMetadata) -> int:
        """Creates a TreeFile buffer according to the tree_metadata flatbuffer schema.

        Args:
            builder (flatbuffers.Builder): The flatbuffer builder object.
            path (str): The filepath for the file.
            file_meta (PathMetadata): The metadata for the file.

        Returns:
            int: The id of the TreeFile buffer for the given file.
        """
        pathbuf = builder.CreateString(path)
        TreeFile.Start(builder)
        TreeFile.AddFilepath(builder, pathbuf)
        TreeFile.AddHash(
            builder, Sha1.CreateSha1(builder, file_meta["hash"].to_bytes(length=20))
        )  # sha1 always produces a 20 byte int
        TreeFile.AddIsDir(builder, file_meta["is_dir"])
        TreeFile.AddSize(builder, file_meta["size"])
        return TreeFile.End(builder)

    def create_metadata_buffer(self: "AbstractLoader", metadata: PathMetadataTree) -> bytearray:
        """Creates a bytearray flatbuffer from cache tree metadata.

        Args:
            metadata (PathMetadataTree): The cache tree metadata.

        Returns:
            bytearray: A flatbuffer bytearray containing the metadata given.
        """
        builder = flatbuffers.Builder()
        from mtpy.utils.type_guards import guarded_int, guarded_pathmetadata

        tree = [
            self.create_tree_file(builder, k, guarded_pathmetadata(v))
            for k, v in metadata["tree"].items()
        ]
        Metadata.StartTreeVector(builder, len(tree))
        for file in reversed(tree):
            builder.PrependUOffsetTRelative(file)
        treebuff = builder.EndVector()

        Metadata.Start(builder)
        Metadata.AddSize(builder, guarded_int(metadata["size"]))
        Metadata.AddTree(builder, treebuff)
        m = Metadata.End(builder)
        builder.Finish(m)
        return guarded_bytearray(builder.Output())

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

        from mtpy.utils.type_guards import guarded_dask_dataframe

        storage_options = getattr(self.fs, "storage_options", None)
        working_path = f"{self._data_cache}working"
        raw_path = f"{self._data_cache}raw"

        # Unpack working and raw into the cache in parallel
        dask.compute(
            dd.read_hdf(self.fs.open(filepath), "cache/data/working").to_parquet(
                self.fs.unstrip_protocol(working_path),
                storage_options=storage_options,
                compression="lz4",
                write_metadata_file=True,
                compute=False,
            ),
            dd.read_hdf(self.fs.open(filepath), "cache/data/raw").to_parquet(
                self.fs.unstrip_protocol(raw_path),
                storage_options=storage_options,
                compression="lz4",
                write_metadata_file=True,
                compute=False,
            ),
        )

        self.data = guarded_dask_dataframe(
            dd.read_parquet(
                self.fs.unstrip_protocol(working_path),
                storage_options=storage_options,
                parquet_file_extension=".parquet",
            )
        )
        self.logger.info("Data loaded!")
