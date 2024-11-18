"""The module containing the AbstractProcessor abstract base class.

This module defines an abstract base class from which all AbstractProcessors
in the MTPy module can be derived.
"""

from abc import ABCMeta
from typing import Any, Type

import loguru
from tqdm.auto import tqdm

from mtpy.base.abstract import AbstractBase
from mtpy.base.feedback.protocol import LoggerProtocol, ProgressBarProtocol

from .protocol import LoaderProtocol


# NOTE: Making this class abstract was a deliberate choice, not a mistake.
#   Even if there are no abstract methods yet i want to enforce loose coupling
#   and make sure it is as easy as possible to extend this class and allow
#   devs to build their own composites.
class AbstractProcessor(AbstractBase, metaclass=ABCMeta):
    """An abstract base class for Processors.

    An abstract base class in which shared functionality for all Processor classes in MTPy
    is defined.

    Args:
        loader (LoaderProtocol): The Loader to be attached to the AbstractProcessor
        logger (LoggerProtocol, optional): The logger to use for logging.
            Defaults to `loguru.logger`
        progressbar (Type[ProgressBarProtocol[Any]], optional):
            A passthrough iterative wrapper that updates a progress bar. Defaults to `tqdm`.
    """

    def __init__(
        self: "AbstractProcessor",
        loader: LoaderProtocol,
        logger: LoggerProtocol = loguru.logger,
        progressbar: Type[ProgressBarProtocol[Any]] = tqdm,
    ) -> None:
        super().__init__(logger=logger, progressbar=progressbar)
        self.loader = loader
