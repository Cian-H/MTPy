"""A base class on which all other classes in this package are built."""

from typing import Protocol

from mtpy.base.feedback.protocol import LoggerProtocol, ProgressBarProtocol


class BaseProtocol(Protocol):
    """A base class on which all other classes in this package are built."""

    logger: LoggerProtocol
    progressbar: ProgressBarProtocol[object]
