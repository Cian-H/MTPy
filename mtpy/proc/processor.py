"""A class that handles data processing for the data pipeline."""

from __future__ import annotations

from .statistics import Statistics
from .thresholder import Thresholder


class Processor(Statistics, Thresholder):
    """This class combines the functionality the other proc classes.

    This class combines the functionality of the of the `MTPy.proc.statistics.Statistics`
    class and the `MTPy.proc.thresholder.Threshdoler` class in a single class
    """

    pass
