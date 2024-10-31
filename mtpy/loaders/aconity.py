"""Data handling and processing components of the MTPy module."""

from itertools import repeat
from pathlib import Path
from typing import List, cast

import dask
from dask import array as da
from fsspec.implementations.dirfs import DirFileSystem
from fsspec.implementations.local import LocalFileSystem
import psutil
from read_aconity_layers import read_selected_layers

from .abstract import AbstractLoader

# Conditional imports depending on whether a GPU is present
# Lots of type: ignore comments here because mypy is not happy with these conditional imports
if "GPU" in dask.config.global_config["distributed"]["worker"]["resources"]:
    dask.config.set({"array.backend": "cupy"})
    from dask_cudf import dataframe as dd
else:
    from dask import dataframe as dd


class AconityLoader(AbstractLoader):
    """A class for loading and preprocessing data."""

    def construct_cached_ddf(
        self: "AconityLoader", data_path: str, chunk_size: int = 3276800
    ) -> None:
        """Constructs a cached dask dataframe from the data at the specified path.

        Args:
            data_path (str): The path to the target directory.
            chunk_size (int, optional): The chunk size for data storage once data is read. Defaults
                to 3276800 (~100MB chunks).
        """
        # Calculate read batches
        batches: List[List[str]] = [[]]
        acc = 0
        data_fs = DirFileSystem(path=data_path, fs=self.fs)
        # Prepare batches of files with total size less than memory_limit to read at once
        pcd_files = data_fs.glob("*.pcd", detail=False)
        for p in sorted(pcd_files, key=lambda x: float(x.split("/")[-1].split(".")[0])):
            file_size = data_fs.size(p.strip("/"))
            try:
                mem_limit = (
                    getattr(
                        self.client.cluster,
                        "_memory_per_worker",
                        lambda: psutil.virtual_memory().available,
                    )()
                    // 4
                )
            except AttributeError:
                mem_limit = self.get_memory_limit()
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
            read_arr_cache = f"{self._data_cache}tmp_arr"
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
            layer_data = read_selected_layers([str(Path(f)) for f in local_file_list])
            darr = da.from_array(
                layer_data,
                chunks=cast(  # Necessary because the type annotation on this arg is incorrect
                    str,
                    (
                        (
                            *tuple(repeat(chunk_size, layer_data.shape[0] // chunk_size)),
                            layer_data.shape[0] % chunk_size,
                        ),
                        *((x,) for x in layer_data.shape[1:]),
                    ),
                ),
            )
            da.to_npy_stack(
                f"{read_arr_cache}/{npy_stack_subdir}",
                darr,
                # storage_options=self.fs.storage_options
            )
            arr_cache_fs.rm(arr_cache_fs.glob("*.pcd"))

        darrays = [da.from_npy_stack(npy_stack) for npy_stack in local_fs.ls(read_arr_cache)]

        from mtpy.utils.type_guards import guarded_dask_array

        data = guarded_dask_array(da.concatenate(darrays))
        data = data.rechunk(balance=True)

        self.fs.mkdirs(f"{self._data_cache}raw", exist_ok=True)

        ddf = dd.from_array(
            data,
            columns=["x", "y", "z", "t", "rgb"],
        ).drop("rgb", axis=1)  # The 'RGB' column is superfluous, as far as i can tell.
        storage_options = getattr(self.fs, "storage_options", {})
        target_options = storage_options.get("target_options", storage_options)
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

        from mtpy.utils.type_guards import guarded_dask_dataframe

        self.data = guarded_dask_dataframe(
            dd.read_parquet(
                self.fs.unstrip_protocol(f"{self._data_cache}working"),
                storage_options=storage_options,
                parquet_file_extension=".parquet",
            )
        )
