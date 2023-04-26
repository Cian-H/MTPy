from __future__ import annotations

import dask
from functools import partial
import math
import pandas as pd
from pathlib import Path

from .data_loader import DataLoader


class DataStatistics(DataLoader):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def calculate_stats(
        self,
        groupby: str | list[str] | None = None,
        confidence_interval: float = 0.95,
    ) -> dict:
        group = self.data.groupby(groupby)
        ops = [group.min(), group.max(), group.mean(), group.std()]
        stats = dict(zip(("min", "max", "mean", "std"), dask.compute(*ops)))
        stats["stderr"] = stats["std"] / math.sqrt(len(stats))
        stats["ci_error"] = confidence_interval * stats["stderr"]
        stats["ci_min"] = stats["mean"] - stats["ci_error"]
        stats["ci_max"] = stats["mean"] + stats["ci_error"]
        return stats

    def export_datasheet(
        self,
        filepath: str,
        overall: bool = True,
        layers: bool = True,
        samples: bool = True,
        sample_layers: bool = True,
        confidence_interval: float = 0.95,
    ) -> None:
        "Generates a spreadsheet containing temperature data for processed samples"

        # Fill a dask pipeline for efficient, optimised stat calculation
        ops = []
        if overall:
            ops += [self.data.min(), self.data.max(), self.data.mean(), self.data.std()]
        if layers:
            group = self.data.groupby("z")
            ops += [group.min(), group.max(), group.mean(), group.std()]
        if samples:
            group = self.data.groupby("sample")
            ops += [group.min(), group.max(), group.mean(), group.std()]
        if sample_layers:
            group = self.data.groupby(["sample", "z"])
            ops += [group.min(), group.max(), group.mean(), group.std()]

        # Compute results
        combined_stats = dask.compute(*ops)

        # Unpack results
        stats = {}
        if overall:
            d = {}
            d["min"], d["max"], d["mean"], d["std"], *combined_stats = combined_stats
            stats["overall"] = { k: v.to_frame() for k, v in d.items() }
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
        sqrt_len = math.sqrt(len(d))
        for d in stats.values():
            d["stderr"] = d["std"] / sqrt_len
            d["ci_error"] = confidence_interval * d["stderr"]
            d["ci_min"] = d["mean"] - d["ci_error"]
            d["ci_max"] = d["mean"] + d["ci_error"]

        # Finally, export the datasheets based on the file extension given
        if filepath.split(".")[-1] in ("xls" , "xlsx" , "xlsm" , "xlsb"):
            writer = partial(pd.ExcelWriter, engine="openpyxl", storage_options=self.fs.storage_options)
            write_func = self._to_excel
        elif filepath.split(".")[-1] in ("odf" , "ods" , "odt"):
            writer = partial(pd.ExcelWriter, engine="odf", storage_options=self.fs.storage_options)
            write_func = self._to_excel
        else:
            writer = self._csv_writer
            write_func = self._to_csv
        
        with writer(filepath) as w:
            for grouping, data in stats.items():
                # combine dataframes into a single sheet
                df = pd.DataFrame()
                for statistic, dd in data.items():
                    df[[f"{x}_{statistic}".strip("0_") for x in dd.keys()]] = dd
                # Then, write a sheet to the file for each grouping present
                write_func(w, df, sheet_name=grouping)

        self._qprint(f"Datasheets generated at {filepath}!")
        
    @staticmethod
    def _to_excel(w, df, sheet_name):
        df.to_excel(w, sheet_name=sheet_name)

    @staticmethod
    def _to_csv(w, df, sheet_name):
        w.write(f"\n{''*80}\n{sheet_name}\n{''*80}\n")
        df.to_csv(w)

    def _csv_writer(self, filepath, *args, **kwargs):
        return self.fs.open(filepath, "w+")
