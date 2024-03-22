from abc import ABC

from .protocol import LoaderProtocol


class AbstractProcessor(ABC):
    def __init__(self: "DataStatistics", loader: LoaderProtocol) -> None:
        """Initialises a DataStatistics object."""
        self.loader = loader

