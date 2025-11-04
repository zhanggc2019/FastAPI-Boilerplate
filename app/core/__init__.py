"""Core infrastructure exports for application wiring."""

from .config import config
from .logging import logger, set_custom_logfile, setup_logging
from .register import register_init

__all__ = [
    "config",
    "logger",
    "set_custom_logfile",
    "setup_logging",
    "register_init",
]

