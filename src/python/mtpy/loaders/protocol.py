from pathlib import Path
from typing import Optional, Protocol

import dask.dataframe as dd
from fsspec import AbstractFileSystem
from mtpy.utils.types import CalibrationFunction


class LoaderProtocol(Protocol):
    fs: AbstractFileSystem
    data: dd.DataFrame
    temp_label: str
    temp_units: str

    def read_layers(
        self: "LoaderProtocol",
        data_path: str,
        calibration_curve: Optional[CalibrationFunction],
        temp_units: str,
        chunk_size: int,
    ) -> None:
        ...

    def commit(self: "LoaderProtocol") -> None:
        ...

    def apply_calibration_curve(
        self: "LoaderProtocol",
        calibration_curve: Optional[CalibrationFunction],
        temp_column: str,
        units: Optional[str],
    ) -> None:
        ...

    def save(self: "LoaderProtocol", filepath: Path | str) -> None:
        ...

    def load(self: "LoaderProtocol", filepath: Path | str) -> None:
        ...
