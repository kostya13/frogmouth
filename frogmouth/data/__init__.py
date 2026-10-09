"""Provides tools for saving and loading application data."""

from .history import load_history, save_history
from .config import Config, load_config, save_config

__all__ = [
    "Config",
    "load_config",
    "load_history",
    "save_config",
    "save_history",
]
