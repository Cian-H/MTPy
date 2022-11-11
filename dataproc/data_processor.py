from .data_statistics import DataStatistics
from .data_thresholder import DataThresholder


class DataProcessor(DataStatistics, DataThresholder):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)