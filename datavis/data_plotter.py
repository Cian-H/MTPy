from pathlib import Path
import panel as pn

from .plotter2d import Plotter2D
from .plotter3d import Plotter3D


class DataPlotter(Plotter2D, Plotter3D):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        