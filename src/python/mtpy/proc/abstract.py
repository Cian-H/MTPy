"""The module containing the AbstractProcessor abstract base class.

This module defines an abstract base class from which all AbstractProcessors
in the MTPy module can be derived.
"""

from abc import ABC

from .protocol import LoaderProtocol


class AbstractProcessor(ABC):  # noqa: B024 <- This is a deliberate choice, not a mistake
    """An abstract base class for Processors.

    An abstract base class in which shared functionality for all Processor classes in MTPy
    is defined.

    Attributes:
        loader (LoaderProtocol): The Loader to be attached to the AbstractProcessor
    """

    def __init__(self: "AbstractProcessor", loader: LoaderProtocol) -> None:
        """Initialises the AbstractProcessor object.

        Args:
            self (AbstractProcessor): The AbstractProcessor object instance
            loader (LoaderProtocol): The Loader to be attached to the AbstractProcessor
        """
        self.loader = loader
