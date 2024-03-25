"""This module defines the protocol that valid MTPy Processors must implement."""

from typing import Protocol, runtime_checkable

from mtpy.loaders.protocol import LoaderProtocol


@runtime_checkable
class ProcessorProtocol(Protocol):
    """The MTPy Processor protocol specification.

    Attributes:
        loader (LoaderProtocol): The loader containing the data being handled
    """

    loader: LoaderProtocol
