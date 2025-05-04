import functools
import logging
import os
import sys
import threading

from logging import (
    CRITICAL,  # NOQA
    DEBUG,  # NOQA
    ERROR,  # NOQA
    FATAL,  # NOQA
    INFO,  # NOQA
    NOTSET,  # NOQA
    WARN,  # NOQA
    WARNING,  # NOQA
)
from logging import captureWarnings as _captureWarnings
from typing import Optional


_lock = threading.Lock()
_default_handler: Optional[logging.Handler] = None

log_levels = {
    "detail": logging.DEBUG,  # will also print filename and line number
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}

_default_log_level = logging.WARNING


def _get_default_log_level():
    return log_levels.get(os.getenv("DEFAULT_LOG_LEVEL"), logging.INFO)


def _get_library_name() -> str:
    return __name__.split(".")[0]


def _get_library_root_logger() -> logging.Logger:
    return logging.getLogger(_get_library_name())


def _configure_library_root_logger() -> None:

    with _lock:
        if sys.stderr is None:
            sys.stderr = open(os.devnull, "w")

        # Apply our default configuration to the library root logger.
        library_root_logger = _get_library_root_logger()
        library_root_logger.setLevel(_get_default_log_level())

        library_root_logger.propagate = True


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Return a logger with the specified name.

    This function is not supposed to be directly accessed unless you are writing a custom transformers module.
    """

    if name is None:
        name = _get_library_name()
    else:
        name = name.split(".")[0]

    _configure_library_root_logger()

    base_logger = logging.getLogger(name)
    base_logger.setLevel(_get_default_log_level())
    # Add a stdout handler / stderr handler
    if os.getenv("FLUSH_TO_CONSOLE").lower() in ["yeah", "true", "1", "yes"]:

        if not any(isinstance(h, logging.StreamHandler) and h.stream == sys.stdout for h in base_logger.handlers):

            handler = logging.StreamHandler(sys.stdout)
            handler_format = logging.Formatter("[%(levelname)s|%(filename)s:%(lineno)s] %(asctime)s >> %(message)s")
            handler.setFormatter(handler_format)
            handler.setLevel(_get_default_log_level())
            base_logger.addHandler(handler)
    else:
        if not any(isinstance(h, logging.StreamHandler) and h.stream == sys.stderr for h in base_logger.handlers):

            handler = logging.StreamHandler(sys.stderr)
            handler_format = logging.Formatter("[%(levelname)s|%(filename)s:%(lineno)s] %(asctime)s >> %(message)s")
            handler.setFormatter(handler_format)
            handler.setLevel(_get_default_log_level())
            base_logger.addHandler(handler)

    return base_logger


