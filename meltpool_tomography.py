#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .dataproc.data_processor import DataProcessor
from .datavis.data_plotter import DataPlotter


class MeltpoolTomography(DataProcessor, DataPlotter):

    def __init__(self, **kwargs):
        # Then call super and set attributes
        super().__init__(**kwargs)
        # Initialize bool for suppressing certain prints during callbacks
        self._quiet_callback = False
