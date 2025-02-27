"""Data handling and processing components of the MTPy module."""

from pathlib import Path
from typing import Any, Dict, Optional

import dask
from dask.distributed import Client
from dask.distributed.deploy import Cluster
from fsspec import AbstractFileSystem

from .abstract import AbstractLoader

# Conditional imports depending on whether a GPU is present
# Lots of type: ignore comments here because mypy is not happy with these conditional imports
if "GPU" in dask.config.global_config["distributed"]["worker"]["resources"]:
    dask.config.set({"array.backend": "cupy"})
    from dask_cudf import dataframe as dd
else:
    from dask import dataframe as dd


class CSVLoader(AbstractLoader):
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

    def __init__(
        self: "CSVLoader",
        client: Optional[Client] = None,
        cluster: Optional[Cluster] = None,
        fs: Optional[AbstractFileSystem] = None,
        data_cache: Optional[Path | str] = "cache",
        cluster_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            client=client,
            cluster=cluster,
            fs=fs,
            data_cache=data_cache,
            cluster_config=cluster_config,
        )
        if __name__ == "__main__":
            scattered_logger = self.client.scatter(self.logger)

            def set_logger(obj: "CSVLoader") -> None:
                obj.logger = scattered_logger

            self.client.submit(set_logger, self)

    def construct_cached_ddf(self: "CSVLoader", data_path: str, chunk_size: int = 3276800) -> None:
        """Constructs a cached dask dataframe from the data at the specified path.

        Args:
            data_path (str): The path to the target directory.
            chunk_size (int, optional): The chunk size for data storage once data is read. Defaults
                to 3276800 (~100MB chunks).
        """
        # Clear the cache so we can create a new one with the layers to be read
        self.fs.rm(self._data_cache, recursive=True)
        self.fs.mkdirs(f"{self._data_cache}/arr", exist_ok=True)

        from mtpy.utils.type_guards import guarded_dask_dataframe

        data_path = f"{data_path}/" if data_path[-1] != "/" else data_path
        data_path = f"{data_path}*.csv" if Path(data_path).is_dir() else data_path
        ddf = guarded_dask_dataframe(dd.read_csv(data_path))
        ddf = ddf.repartition(partition_size=str(chunk_size))

        self.fs.mkdirs(f"{self._data_cache}/raw", exist_ok=True)

        storage_options = getattr(self.fs, "storage_options", {})
        target_options = storage_options.get("target_options", storage_options)
        ddf.to_parquet(
            self.fs.unstrip_protocol(f"{self._data_cache}/raw"),
            storage_options=target_options,
            compression="lz4",
            append=True,
            compute=True,
            write_metadata_file=True,
            ignore_divisions=True,
        )

        self.fs.mkdirs(f"{self._data_cache}/working", exist_ok=True)

        # if keeping raw data, copy raw files before modifying
        self.fs.cp(f"{self._data_cache}/raw", f"{self._data_cache}/working", recursive=True)

        from mtpy.utils.type_guards import guarded_dask_dataframe

        self.data = guarded_dask_dataframe(
            dd.read_parquet(
                self.fs.unstrip_protocol(f"{self._data_cache}/working"),
                storage_options=storage_options,
                parquet_file_extension=".parquet",
            )
        )
