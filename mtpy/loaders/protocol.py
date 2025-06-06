"""A protocol describing the structure of a valid loader object.

This module contains the `LoaderProtocol`, which is a protocol describing
the structure of valid Loaders that can be used in the MTPy module. Aids
in type-checking, error checking, and helps developers in the process of
creating their own Loader objects that can be plugged into the broader
MTPy framework
"""

from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional, Protocol, TypeGuard, runtime_checkable

import dask.dataframe as dd
from dask.distributed import Client
from dask.distributed.deploy import Cluster
from fsspec import AbstractFileSystem

from mtpy.utils.types import CalibrationFunction


@runtime_checkable
class LoaderProtocol(Protocol):
    """The protocol for a valid Loader class.

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

    Attributes:
        fs (AbstractFileSystem): The fsspec FileSystem to load from
        data (dd.DataFrame): The dask DataFrame containing the loaded data
        temp_label (str): The label for the temperature data column
        temp_units (str): The units to be applied to the temperature data column
    """

    fs: AbstractFileSystem
    data: dd.DataFrame
    temp_label: str
    temp_units: str

    def __init__(
        self: "LoaderProtocol",
        client: Optional[Client],
        cluster: Optional[Cluster],
        fs: Optional[AbstractFileSystem],
        data_cache: Optional[Path | str],
        cluster_config: Optional[Dict[str, Any]],
    ) -> None: ...

    def read_layers(
        self: "LoaderProtocol",
        data_path: str,
        calibration_curve: Optional[CalibrationFunction],
        temp_units: str,
        chunk_size: int,
    ) -> None:
        """Reads layers from designated path on provided filesystem.

        Args:
            data_path (str): The path to the data to be loaded
            calibration_curve (Optional[CalibrationFunction]): The calibration curve to apply to
                that data
            temp_units (str): The units to be applied to the temperature column
            chunk_size (int): The target chunk size for the partitioned DataFrame at self.data
        """
        ...

    def commit(self: "LoaderProtocol") -> None:
        """Commits changes to the self.data DataFrame file cache."""
        ...

    def apply_calibration_curve(
        self: "LoaderProtocol",
        calibration_curve: Optional[CalibrationFunction],
        temp_column: str,
        units: Optional[str],
    ) -> None:
        """Applies a calibration function to the self.data DataFrame columns.

        Args:
            calibration_curve (Optional[CalibrationFunction]): The calibration curve to apply to
                that data
            temp_column (str): The self.data DataFrame column that contains the temperature data
            units (Optional[str]): The units to be applied to the temperature column
        """
        ...

    def save(self: "LoaderProtocol", filepath: Path | str) -> None:
        """Save the current analysis session to a save file.

        Args:
            filepath (Path | str): The filepath to save to
        """
        ...

    def load(self: "LoaderProtocol", filepath: Path | str) -> None:
        """Load an analysis session from a save file.

        Args:
            filepath (Path | str): The filepath to load to
        """
        ...


def is_loader_protocol(t: object) -> TypeGuard[LoaderProtocol]:
    """Type guard for loader protocols.

    Args:
        t (object): the object to check

    Returns:
        TypeGuard[LoaderProtocol]: True if the object is a loader protocol, False otherwise.
    """
    if not TYPE_CHECKING:
        return True
    return isinstance(t, LoaderProtocol)


def guarded_loader_protocol(t: object) -> LoaderProtocol:
    """A function for type guarding loader protocols.

    Args:
        t (object): the object to check

    Raises:
        TypeError: if the type fails the guard check

    Returns:
        LoaderProtocol: the object if it is a loader protocol
    """
    if not TYPE_CHECKING:
        return t
    if not is_loader_protocol(t):
        msg = "Expected a LoaderProtocol"
        raise TypeError(msg)
    return t
