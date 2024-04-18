#!/usr/bin/env python3

"""L-PBF meltpool tomography in python.

MTPy is a module containing tools useful for the processing of metal additive
manufacturing pyrometry data and the generation of graphs and tomographs from
the resulting meltpool data.
"""

__version__ = "0.1.0"
__license__ = "MIT"
__status__ = "Prototype"
__modpath__ = __file__[: __file__.rfind("/")]

from . import base, loaders, meltpool_tomography, proc, utils, vis

__all__ = ["base", "loaders", "proc", "utils", "vis", "meltpool_tomography"]

from .meltpool_tomography import MeltpoolTomography  # noqa
from mtpy.utils.log_intercept import InterceptHandler, redirect_logging_to_loguru
import dask.distributed as ddist

# Here, we redirect default logging to loguru to make logging faster
# And easier to handle
redirect_logging_to_loguru()
ddist.core.logger.addHandler(InterceptHandler())
ddist.worker.logger.addHandler(InterceptHandler())
ddist.scheduler.logger.addHandler(InterceptHandler())
ddist.nanny.logger.addHandler(InterceptHandler())
