"""Provides useful dialogs for the application."""

from .error import ErrorDialog
from .help_dialog import HelpDialog
from .history_dialog import HistoryDialog
from .input_dialog import InputDialog
from .new_file_dialog import NewFileDialog
from .yes_no_dialog import YesNoDialog

__all__ = [
    "ErrorDialog",
    "HelpDialog",
    "HistoryDialog",
    "InputDialog",
    "NewFileDialog",
    "YesNoDialog",
]
