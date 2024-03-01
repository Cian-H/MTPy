#!/usr/bin/env python3
# *_* coding: utf-8 *_*

"""
MTPy is a module containing tools useful for the processing of metal additive
manufacturing pyrometry data and the generation of graphs and tomographs from
the resulting meltpool data
"""

# TEMPORARY FIX FOR WARNINGS
import warnings


warnings.filterwarnings("ignore")
warnings.filterwarnings("ignore", module="bokeh")

__version__ = "0.1.0"
__license__ = "MIT"
__status__ = "Prototype"
__modpath__ = __file__[: __file__.rfind("/")]

from . import meltpool_tomography  # noqa
