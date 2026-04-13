"""
Centralized logging for DataLens.

Goals:
- Provide a reliable log file for end users (installed/frozen builds) and devs
- Avoid scattering ad-hoc print() and silent exception swallowing
- Keep logging lightweight (no external dependencies)
"""

from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional


_CONFIGURED = False


def _default_log_dir() -> str:
    """Return an appropriate, user-writable directory for logs."""
    if getattr(sys, "frozen", False):
        base = os.path.join(
            os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
            "DataLens",
        )
    else:
        # In dev mode keep logs alongside the repo for convenience.
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    return os.path.join(base, "logs")


def init_logging(
    *,
    log_dir: Optional[str] = None,
    level: int = logging.INFO,
    filename: str = "datalens.log",
) -> str:
    """Configure the root logger once and return the log file path."""
    global _CONFIGURED
    if _CONFIGURED:
        return os.path.join(log_dir or _default_log_dir(), filename)

    log_dir = log_dir or _default_log_dir()
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, filename)

    root = logging.getLogger()
    root.setLevel(level)

    fmt = logging.Formatter(
        fmt="%(asctime)s.%(msecs)03d | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Rotating file log (primary signal).
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=2_000_000,  # ~2MB
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)

    # Console logs help dev runs; in frozen mode there's usually no console.
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(fmt)
    root.addHandler(stream_handler)

    _CONFIGURED = True
    root.debug("Logging initialized at %s", log_path)
    return log_path


def get_logger(name: str) -> logging.Logger:
    """Get a named logger (ensures base logging is initialized)."""
    if not _CONFIGURED:
        init_logging()
    return logging.getLogger(name)

