"""A dummy processor for constructing test objects or objects without a processor."""

from mtpy.loaders.dummy import DummyLoader


class DummyProcessor:
    """A dummy processor placeholding for a functional processor."""

    def __init__(self: "DummyProcessor") -> None:
        self.loader = DummyLoader()
