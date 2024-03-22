from abc import ABC

from .protocol import LoaderProtocol


class AbstractProcessor(ABC): # noqa: B024 <- This is a deliberate choice, not a mistake
    def __init__(self: "AbstractProcessor", loader: LoaderProtocol) -> None:
        """Initialises a AbstractProcessor object."""
        self.loader = loader
