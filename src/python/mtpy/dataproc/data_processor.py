# -*- coding: utf-8 -*-

"""A class that handles data processing for the data pipeline."""

from __future__ import annotations

from .data_statistics import DataStatistics
from .data_thresholder import DataThresholder


class DataProcessor(DataStatistics, DataThresholder):
    """A class that handles data processing for the data pipeline."""

    def __init__(self: "DataProcessor", **kwargs) -> None:
        """Initialises a DataProcessor object."""
        super().__init__(**kwargs)
