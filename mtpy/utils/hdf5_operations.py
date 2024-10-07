"""A collection of functions for interacting with HDF5 files."""

import h5py
import numpy as np


def read_bytes_from_hdf_dataset(ds: h5py._hl.dataset.Dataset) -> bytes:
    """Reads raw bytes from a dataset field in a HDF5 file.

    Args:
        ds (h5py._hl.dataset.Dataset): The dataset to be read from.

    Returns:
        bytes: The raw bytes of the dataset.
    """
    buf = np.empty(ds.shape, dtype=ds.dtype)
    ds.read_direct(buf)
    return buf.tobytes()


def write_bytes_to_hdf_dataset(
    group: h5py._hl.group.Group,
    ds_key: str,
    b: bytes | bytearray,
) -> None:
    """Writes raw bytes to a dataset field in a HDF5 file.

    Args:
        group (h5py._hl.group.Group): The group into which to write the dataset.
        ds_key (str): The key under which the dataset bytes should be written.
        b (bytes | bytearray): The bytes to be written.
    """
    group[ds_key] = np.frombuffer(b, dtype=np.uint8)
