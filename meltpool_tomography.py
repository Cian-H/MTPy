#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .dataproc.data_processor import DataProcessor
from .datavis.data_plotter import DataPlotter


class MeltpoolTomography(DataProcessor, DataPlotter):
    """a class for handling the data pipeline and visualisation of meltpool tomography data"""

    def __init__(self, **kwargs):
        """Initialises a MeltpoolTomography object."""
        # Then call super and set attributes
        super().__init__(**kwargs)
        # Initialize bool for suppressing certain prints during callbacks
        self._quiet_callback = False
