"""Provides the pathbar widget; displays the current location."""

from __future__ import annotations

from pathlib import Path

from httpx import URL
from textual.reactive import var
from textual.widgets import Static


class Pathbar(Static):
    """A static display of the current location."""

    DEFAULT_CSS = """
    Pathbar {
        dock: top;
        padding: 0 1;
        height: 1;
        color: $text-muted;
        background: $surface;
    }
    """
    """Default styling for the pathbar."""

    location: var[str] = var("")
    """The location that is being viewed."""

    def watch_location(self) -> None:
        """Watch the location reactive variable."""
        self.update(self.location)

    @staticmethod
    def display_text(location: Path | URL | None) -> str:
        """Work out the display text for a given location.

        Args:
            location: The location to display.

        Returns:
            The text to display for the location.
        """
        return str(location) if location is not None else ""
