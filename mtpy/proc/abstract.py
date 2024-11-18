"""The module containing the AbstractProcessor abstract base class.

This module defines an abstract base class from which all AbstractProcessors
in the MTPy module can be derived.
"""

from abc import ABCMeta

from mtpy.base.abstract import AbstractBase

from .protocol import LoaderProtocol


# NOTE: Making this class abstract was a deliberate choice, not a mistake.
#   Even if there are no abstract methods yet i want to enforce loose coupling
#   and make sure it is as easy as possible to extend this class and allow
#   devs to build their own composites.
class AbstractProcessor(AbstractBase, metaclass=ABCMeta):
    """An abstract base class for Processors.

    An abstract base class in which shared functionality for all Processor classes in MTPy
    is defined.

    Args:
        loader (LoaderProtocol): The Loader to be attached to the AbstractProcessor
    """

    def __init__(self: "AbstractProcessor", loader: LoaderProtocol) -> None:
        super().__init__()
        self.loader = loader
