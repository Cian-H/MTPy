# -*- coding: utf-8 -*-

"""Data visualisation components of the MTPy module."""

from __future__ import annotations

from .plotter2d import Plotter2D
from .plotter3d import Plotter3D


class DataPlotter(Plotter2D, Plotter3D):
    """The DataPlotter class is a wrapper for the Plotter2D and Plotter3D classes."""

    def __init__(self: "DataPlotter", **kwargs) -> None:
        """Initialises a DataPlotter object.

        Args:
            self (DataPlotter): the DataPlotter object
            **kwargs: keyword arguments to be passed to the parent class initialisers
            (`Plotter2D` and `Plotter3D`)
        """
        super().__init__(**kwargs)
