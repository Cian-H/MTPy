from __future__ import annotations

from .plotter2d import Plotter2D
from .plotter3d import Plotter3D


class DataPlotter(Plotter2D, Plotter3D):
    """The DataPlotter class is a wrapper for the Plotter2D and Plotter3D classes."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
