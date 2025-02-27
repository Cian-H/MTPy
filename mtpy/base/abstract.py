"""An abstract base class defining core shared functionality for MTPy classes."""

from abc import ABCMeta
from typing import Any, Type

import loguru
from tqdm.auto import tqdm

from mtpy.base.feedback.protocol import LoggerProtocol, ProgressBarProtocol


class AbstractBase(metaclass=ABCMeta):  # noqa B024
    """Functionality shared by all classes in this package.

    Args:
        logger (LoggerProtocol, optional): The logger to use for logging.
            Defaults to `loguru.logger`
        progressbar (Type[ProgressBarProtocol[Any]], optional):
            A passthrough iterative wrapper that updates a progress bar. Defaults to `tqdm`.
    """

    def __init__(
        self: "AbstractBase",
        logger: LoggerProtocol = loguru.logger,
        progressbar: Type[ProgressBarProtocol[Any]] = tqdm,
    ) -> None:
        self.logger = logger
        self.progressbar = progressbar
