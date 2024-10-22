"""An abstract base class defining core shared functionality fo MTPy classes."""

from abc import ABCMeta

import loguru
from tqdm.auto import tqdm

from mtpy.base.feedback.protocol import LoggerProtocol, ProgressBarProtocol


class AbstractBase(metaclass=ABCMeta):  # noqa B024
    """Functionality shared by all classes in this package.

    Args:
        logger (LoggerProtocol, optional): The logger to use for logging.
            Defaults to `loguru.logger`
        progressbar (type[ProgressBarProtocol], optional):
            A passthrough iterative wrapper that updates a progress bar. Defaults to `tqdm`.
    """

    def __init__(
        self: "AbstractBase",
        logger: LoggerProtocol = loguru.logger,
        progressbar: type[ProgressBarProtocol] = tqdm,
    ) -> None:
        self.logger = logger
        self.progressbar = progressbar
