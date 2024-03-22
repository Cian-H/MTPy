from pathlib import Path
from typing import Optional

import dask.dataframe as dd
from fsspec.implementations.local import LocalFileSystem
from mtpy.utils.types import CalibrationFunction


class DummyLoader:
    def read_layers(
        self: "DummyLoader",
        data_path: str,
        calibration_curve: Optional[CalibrationFunction],
        temp_units: str,
        chunk_size: int,
    ) -> None:
        self.fs = LocalFileSystem()
        self.data = dd.DataFrame.from_dict({})
        self.temp_label = ""
        self.temp_units = ""

    def commit(self: "DummyLoader") -> None:
        pass

    def apply_calibration_curve(
        self: "DummyLoader",
        calibration_curve: Optional[CalibrationFunction],
        temp_column: str,
        units: Optional[str],
    ) -> None:
        pass

    def save(self: "DummyLoader", filepath: Path | str) -> None:
        pass

    def load(self: "DummyLoader", filepath: Path | str) -> None:
        pass
