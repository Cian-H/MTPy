from pathlib import Path
from matplotlib import pyplot as plt

from .plotter2d import Plotter2D
from .plotter3d import Plotter3D

# This piece of init code prevents a warning resulting from generation of
#   many matplotlib "figure" objects. This is unimportant on my current
#   computer as i have plenty of RAM but if becomes an issue in future may need
#   to write a singleton wrapper object for plt.figure
# plt.rcParams.update({"figure.max_open_warning": 0})

class DataPlotter(Plotter2D, Plotter3D):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)