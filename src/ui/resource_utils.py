"""
Shared path helpers for dev and PyInstaller (frozen) builds.

The app loads assets (icons/images) and templates from the project root in
development, and from the PyInstaller extraction directory (``sys._MEIPASS``)
when frozen. Centralizing this avoids subtle mismatches across modules.
"""

from __future__ import annotations

import os
import sys
from typing import Union


def app_base_path() -> str:
    """Return the base directory where packaged resources live."""
    # PyInstaller creates a temp folder and stores the absolute path in _MEIPASS.
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return meipass

    # Development mode: repository root (two levels above src/ui/*).
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def resource_path(*parts: Union[str, os.PathLike]) -> str:
    """Build an absolute path to a resource shipped with the app.

    Usage:
        resource_path("assets", "DataLens_Logo.ico")
        resource_path("templates", "report_template.html")
    """
    base = app_base_path()
    # Allow callers to pass a single "a/b/c" string or multiple parts.
    if len(parts) == 1:
        return os.path.join(base, os.fspath(parts[0]))
    return os.path.join(base, *[os.fspath(p) for p in parts])

