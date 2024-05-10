"""A dummy processor for constructing test objects or objects without a processor."""

from mtpy.loaders.dummy import DummyLoader


class DummyProcessor:
    """A dummy processor placeholding for a functional processor.

    Attributes:
        loader (DummyLoader): The loader containing the data being handled
    """

    def __init__(self: "DummyProcessor") -> None:
        """Initializes a dummy placeholder object."""
        self.loader = DummyLoader()
