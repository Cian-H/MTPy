#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A module for handling L-PBF meltpool tomography data."""

from .dataproc.data_processor import DataProcessor
from .datavis.data_plotter import DataPlotter


class MeltpoolTomography(DataProcessor, DataPlotter):
    """a class for handling the data pipeline and visualisation of meltpool tomography data."""

    def __init__(self: "MeltpoolTomography", **kwargs) -> None:
        """Initialises a MeltpoolTomography object.

        Args:
            self (MeltpoolTomography): The MeltpoolTomography object.
            **kwargs: keyword arguments to be passed to the parent class initialisers
        """
        # Then call super and set attributes
        super().__init__(**kwargs)
        # Initialize bool for suppressing certain prints during callbacks
        self._quiet_callback = False
