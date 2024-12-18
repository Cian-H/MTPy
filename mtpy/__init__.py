#!/usr/bin/env python3

"""L-PBF meltpool tomography in python.

MTPy is a module containing tools useful for the processing of metal additive
manufacturing pyrometry data and the generation of graphs and tomographs from
the resulting meltpool data.
"""

__version__ = "0.3.3"
__description__ = "A python based tool for Meltpool Tomography."
__urls__ = {"github": "https://github.com/Cian-H/I-Form_Server_Node_Deployer"}
__authors__ = ["Cian Hughes <cian.hughes@dcu.ie>"]
__license__ = "MIT"
__modpath__ = __file__[: __file__.rfind("/")]

__all__ = [
    "base",
    "loaders",
    "meltpool_tomography",
    "MeltpoolTomography",
    "proc",
    "vis",
]

from . import base, loaders, meltpool_tomography, proc, vis
from .meltpool_tomography import MeltpoolTomography
