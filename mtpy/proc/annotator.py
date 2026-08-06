"""A module for handling scanline annotation for the data pipeline."""

from __future__ import annotations

import pandas as pd
from scanline_annotator import annotate_scanlines

from mtpy.base.abstract import AbstractBase

from .abstract import AbstractProcessor


class Annotator(AbstractProcessor, AbstractBase):
    """A class that handles scanline annotation for the data pipeline."""

    def annotate_scanlines(
        self: "Annotator",
        x_col: str = "x",
        y_col: str = "y",
        output_col: str = "scanline_id",
    ) -> None:
        """Annotates raster scanlines on the loader's Dask DataFrame.

        Args:
            x_col (str, optional): Name of the x-coordinate column. Defaults to "x".
            y_col (str, optional): Name of the y-coordinate column. Defaults to "y".
            output_col (str, optional): Name of the column to store scanline IDs.
                Defaults to "scanline_id".
        """

        def _annotate_partition(df: pd.DataFrame) -> pd.Series:
            x = df[x_col].to_numpy()
            y = df[y_col].to_numpy()
            scanline_ids = annotate_scanlines(x, y)
            return pd.Series(scanline_ids, index=df.index, name=output_col)

        self.logger.info("Annotating scanlines")
        self.loader.data[output_col] = self.loader.data.map_partitions(
            _annotate_partition, meta=(output_col, "int32")
        )
