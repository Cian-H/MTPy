"""A class that handles data processing for the data pipeline."""

from __future__ import annotations

from .annotator import Annotator
from .statistics import Statistics
from .thresholder import Thresholder


class Processor(Statistics, Thresholder, Annotator):
    """This class combines the functionality of the other proc classes.

    This class combines the functionality of the `MTPy.proc.statistics.Statistics`
    class, the `MTPy.proc.thresholder.Thresholder` class, and the
    `MTPy.proc.annotator.Annotator` class in a single class.
    """

    pass
