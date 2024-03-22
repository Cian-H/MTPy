from typing import Protocol

from ..loaders.protocol import LoaderProtocol


class ProcessorProtocol(Protocol):
    data: LoaderProtocol
