"""An abstract base class defining core shared functionality fo MTPy classes."""

from abc import ABCMeta

import loguru
from tqdm.auto import tqdm

from mtpy.base.feedback.protocol import LoggerProtocol, ProgressBarProtocol


class AbstractBase(metaclass=ABCMeta):  # noqa B024
    def __init__(
        self: "AbstractBase",
        *,
        logger: LoggerProtocol = loguru.logger,
        progressbar: type[ProgressBarProtocol] = tqdm,
    ) -> None:
        """Initialisation shared by all classes in this package.

        Args:
            self (Base): The class instance.
            logger (LoggerProtocol, optional): The logger to use for logging.
                Defaults to `loguru.logger`
            progressbar (type[ProgressBarProtocol], optional):
                A passthrough iterative wrapper that updates a progress bar. Defaults to `tqdm`.
        """
        self.logger = logger
        self.progressbar = progressbar
