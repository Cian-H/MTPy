"""A module for handling data statistics for the data pipeline."""

from functools import singledispatchmethod
from io import TextIOWrapper
import math
from typing import Any, Dict, Iterable, List, Optional, Tuple, TypeVar

import dask
import dask.dataframe as dd
from fsspec.spec import AbstractBufferedFile
import pandas as pd

from mtpy.utils.types import StatsDict, TOMLDict

from .abstract import AbstractProcessor

T = TypeVar("T")


class Statistics(AbstractProcessor):
    """A class that handles data statistics for the data pipeline."""

    def calculate_stats(
        self: "Statistics",
        groupby: Optional[str | Iterable[str]] = None,
        confidence_interval: float = 0.95,
    ) -> StatsDict:
        """Calculates numerical statistics for the current data.

        Args:
            groupby (Optional[str | Iterable[str]], optional): a groupby string to be applied
                to the dataframe before calculation. Defaults to None.
            confidence_interval (float, optional): The confidence interval at which to perform
                statistical calculations. Defaults to 0.95.

        Returns:
            StatsDict: A dict containing the calculated statistics.
        """
        ddf = self.loader.data
        if groupby is None:
            groupby = "overall"
            ddf = ddf.assign(overall="overall")
        group: dd.dask_expr._groupby.GroupBy = ddf.groupby(groupby)
        ops: List[dd.dask_expr._collection.Series] = [
            group.min(),
            group.max(),
            group.mean(),
            group.std(),
        ]
        results: Tuple[float, float, float, float] = dask.compute(*ops)
        _min, _max, mean, std = results
        stderr: float = std / math.sqrt(len(self.loader.data))
        ci_error: float = confidence_interval * stderr
        ci_min: float = mean - ci_error
        ci_max: float = mean + ci_error
        return StatsDict(
            min=_min,
            max=_max,
            mean=mean,
            std=std,
            stderr=stderr,
            ci_error=ci_error,
            ci_min=ci_min,
            ci_max=ci_max,
        )

    def export_datasheet(
        self: "Statistics",
        filepath: str,
        *,
        overall: bool = True,
        layers: bool = True,
        samples: bool = True,
        sample_layers: bool = True,
        confidence_interval: float = 0.95,
    ) -> None:
        """Generates a spreadsheet containing temperature data for processed samples.

        Args:
            filepath (str): the path to which a datasheet will be written.
            overall (bool, optional): whether or not to calculate statistics for the
                overall dataframe. Defaults to True.
            layers (bool, optional): whether or not to calculate statistics for each layer
                current dataframe. Defaults to True.
            samples (bool, optional): whether or not to calculate statistics for each sample
                current dataframe. Defaults to True.
            sample_layers (bool, optional): whether or not to calculate statistics for each layer
                in each individual sample in the current dataframe. Defaults to True.
            confidence_interval (float, optional): The confidence interval at which to perform
                statistical calculations. Defaults to 0.95.
        """
        # Fill a dask pipeline for efficient, optimised stat calculation
        ops: List[dd.dask_expr._collection.Series] = []
        if overall:
            ops += [
                self.loader.data.min(),
                self.loader.data.max(),
                self.loader.data.mean(),
                self.loader.data.std(),
            ]
        group: dd.dask_expr._groupby.GroupBy
        if layers:
            group = self.loader.data.groupby("z")
            ops += [group.min(), group.max(), group.mean(), group.std()]
        if samples:
            group = self.loader.data.groupby("sample")
            ops += [group.min(), group.max(), group.mean(), group.std()]
        if sample_layers:
            group = self.loader.data.groupby(["sample", "z"])
            ops += [group.min(), group.max(), group.mean(), group.std()]

        # Compute results
        combined_stats: List[dd.DataFrame] = list(dask.compute(*ops))

        # Unpack results
        stats: Dict[str, Dict[str, dd.DataFrame]] = {}
        d: Dict[str, dd.DataFrame] = {}
        if overall:
            d = {}
            d["min"], d["max"], d["mean"], d["std"], *combined_stats = combined_stats
            stats["overall"] = {k: v.to_frame() for k, v in d.items()}
        if layers:
            d = {}
            d["min"], d["max"], d["mean"], d["std"], *combined_stats = combined_stats
            stats["layers"] = d
        if samples:
            d = {}
            d["min"], d["max"], d["mean"], d["std"], *combined_stats = combined_stats
            stats["samples"] = d
        if sample_layers:
            d = {}
            d["min"], d["max"], d["mean"], d["std"], *combined_stats = combined_stats
            stats["sample_layers"] = d

        # Next, compute derived statistics
        sqrt_len: float = math.sqrt(len(d))
        for d in stats.values():
            d["stderr"] = d["std"] / sqrt_len  # type: ignore[assignment, operator]
            d["ci_error"] = confidence_interval * d["stderr"]  # type: ignore[assignment, operator]
            d["ci_min"] = d["mean"] - d["ci_error"]  # type: ignore[assignment, operator]
            d["ci_max"] = d["mean"] + d["ci_error"]  # type: ignore[assignment, operator]

        # Finally, export the datasheets based on the file extension given
        self.write_to_file(stats, filepath)
        self.logger.info(f"Datasheets generated at {filepath}!")

    def write_to_file(
        self: "Statistics",
        stats: Dict[str, Dict[str, dd.dask_expr._collection.DataFrame]],
        filepath: str,
    ) -> None:
        """Writes a dictionary of statistics to a file.

        Args:
            stats (Dict[str, Dict[str, dd.dask_expr._collection.DataFrame]]): the statistics to
                be written to file.
            filepath (str): the path to which a datasheet will be written.
        """
        with self._get_writer(filepath) as w:
            for grouping, data in stats.items():
                # combine dataframes into a single sheet
                combined_df = pd.DataFrame()
                for statistic, ddf in data.items():
                    combined_df[[f"{x}_{statistic}".strip("0_") for x in ddf]] = ddf
                # Then, write a sheet to the file for each grouping present
                self._write(w, combined_df, sheet_name=grouping)

    def _get_writer(
        self: "Statistics", filepath: str
    ) -> pd.ExcelWriter | TextIOWrapper | AbstractBufferedFile:
        file_extension = filepath.split(".")[-1]
        storage_options: TOMLDict | None = getattr(self.loader.fs, "storage_options", None)
        if file_extension in {"xls", "xlsx", "xlsm", "xlsb"}:
            return pd.ExcelWriter(filepath, engine="openpyxl", storage_options=storage_options)
        if filepath.split(".")[-1] in {"odf", "ods", "odt"}:
            return pd.ExcelWriter(filepath, engine="odf", storage_options=storage_options)
        return self._csv_writer(filepath)

    def _csv_writer(
        self: "Statistics", filepath: str, *args: Any, **kwargs: Any
    ) -> TextIOWrapper | AbstractBufferedFile:
        """A csv writer method that handles writing to a remote filesystem.

        Args:
            filepath (str): the path to which a datasheet will be written.
            *args (Any): additional arguments to be passed to the writer.
            **kwargs (Any): additional keyword arguments to be passed to the writer.

        Returns:
            TextIOWrapper | AbstractBufferedFile: A buffer to which a csv can be written.
        """
        return self.loader.fs.open(filepath, "w+")

    @singledispatchmethod
    @staticmethod
    def _write(w: T, df: pd.DataFrame, sheet_name: str) -> None:
        """A fallthrough method for attempts to write to unsupported file types.

        Args:
            w (T): the writer object to which a datasheet will be written.
            df (pd.DataFrame): the dataframe to be written to the datasheet.
            sheet_name (str): the name of the sheet to be written.

        Raises:
            NotImplementedError: Indicates this file type is not yet supported.
        """
        msg = f"Writing to {type(w)} is not supported"
        raise NotImplementedError(msg)

    @staticmethod
    @_write.register
    def _write_excel(w: pd.ExcelWriter, df: pd.DataFrame, sheet_name: str) -> None:
        """A method for handling writing to excel files.

        Args:
            w (pd.ExcelWriter): the writer object to which a datasheet will be written.
            df (pd.DataFrame): the dataframe to be written to the datasheet.
            sheet_name (str): the name of the sheet to be written.
        """
        df.to_excel(w, sheet_name=sheet_name)

    @staticmethod
    @_write.register
    def _write_csv(
        w: TextIOWrapper | AbstractBufferedFile, df: pd.DataFrame, sheet_name: str
    ) -> None:
        """A method for handling writing to csv files.

        Args:
            w (TextIOWrapper | AbstractBufferedFile): the writer object to which a datasheet will
                be written.
            df (pd.DataFrame): the dataframe to be written to the datasheet.
            sheet_name (str): the name of the heading under which the dataframe csv will be written.
        """
        w.write(f"\n{'' * 80}\n{sheet_name}\n{'' * 80}\n")
        df.to_csv(w)
