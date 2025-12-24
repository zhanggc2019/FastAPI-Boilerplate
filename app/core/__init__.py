"""Core infrastructure exports for application wiring."""

from .config import config
from .logging import logger, set_custom_logfile, setup_logging
__all__ = [
    "config",
    "logger",
    "set_custom_logfile",
    "setup_logging",
]
