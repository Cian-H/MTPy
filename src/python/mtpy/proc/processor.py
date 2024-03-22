# -*- coding: utf-8 -*-

"""A class that handles data processing for the data pipeline."""

from __future__ import annotations

from .statistics import Statistics
from .thresholder import Thresholder


class Processor(Statistics, Thresholder):
    pass
