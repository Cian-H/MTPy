from typing import Protocol

from mtpy.loaders.protocol import LoaderProtocol


class ProcessorProtocol(Protocol):
    data: LoaderProtocol
