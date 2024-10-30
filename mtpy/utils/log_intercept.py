"""A handler for redirecting standard library logging to loguru."""

import logging
import sys

from dask import distributed as ddist
from loguru import logger


# This solution for this problem was found at:
#   https://stackoverflow.com/questions/66769431/how-to-use-loguru-with-standard-loggers
class InterceptHandler(logging.Handler):
    """Add logging handler to augment python stdlib logging.

    Logs which would otherwise go to stdlib logging are redirected through
    loguru.
    """

    @logger.catch(default=True, onerror=lambda _: sys.exit(1))
    def emit(self: "InterceptHandler", record: logging.LogRecord) -> None:
        """Converts std.logging emits to loguru emits.

        Args:
            record (logging.LogRecord): The record being intercepted.
        """
        # Get corresponding Loguru level if it exists.
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = str(record.levelno)

        # Find caller from where originated the logged message.
        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            next_frame = frame.f_back
            if next_frame is not None:
                frame = next_frame
            else:
                break
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


# Redirects all errors inside the module to loguru instead of std.logging
def redirect_logging_to_loguru() -> None:
    """A function that redirects stdlib logging in the current module to loguru."""
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)


class LoguruPlugin(ddist.WorkerPlugin):
    """A dask worker plugin that redirects worker logs to loguru."""

    def setup(self: "LoguruPlugin", worker: ddist.Worker) -> None:
        """Sets up the appropriate interceptor for redirecting logging to loguru.

        Args:
            worker (ddist.Worker): The dask worker to apply the plugin to
        """
        redirect_logging_to_loguru()
