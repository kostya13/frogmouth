"""Provides the navigation panel widget."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.message import Message
from textual.reactive import var
from typing_extensions import Self

from ..data import load_config, save_config
from .navigation_panes.local_files import LocalFiles


class Navigation(Vertical, can_focus=False, can_focus_children=True):
    """A navigation panel widget."""

    DEFAULT_CSS = """
    Navigation {
        width: 34;
        background: $panel;
        display: block;
        dock: left;
    }

    Navigation.hidden {
        display: none;
    }

    Navigation > LocalFiles {
        height: 100%;
        border: round $panel-lighten-2;
        padding: 0 !important;
    }
    """

    BINDINGS = [
        Binding("\\", "toggle_dock", "Dock left/right"),
    ]
    """Bindings local to the navigation pane."""

    popped_out: var[bool] = var(False)
    """Is the navigation popped out?"""

    docked_left: var[bool] = var(True)
    """Should navigation be docked to the left side of the screen?"""

    def compose(self) -> ComposeResult:
        """Compose the content of the navigation pane."""
        self.popped_out = False
        # pylint:disable=attribute-defined-outside-init
        self._local_files = LocalFiles()
        yield self._local_files

    def on_mount(self) -> None:
        """Configure navigation once the DOM is set up."""
        self.docked_left = load_config().navigation_left

    class Hidden(Message):
        """Message sent when the navigation is hidden."""

    def watch_popped_out(self) -> None:
        """Watch for changes to the popped out state."""
        self.set_class(not self.popped_out, "hidden")
        if not self.popped_out:
            self.post_message(self.Hidden())

    def toggle(self) -> None:
        """Toggle the popped/unpopped state."""
        self.popped_out = not self.popped_out

    def watch_docked_left(self) -> None:
        """Watch for changes to the left-docking status."""
        self.styles.dock = "left" if self.docked_left else "right"

    @property
    def local_files(self) -> LocalFiles:
        """The local files widget."""
        return self._local_files

    def jump_to_local_files(self, target: Path | None = None) -> Self:
        """Switch to and focus the local files pane.

        Args:
            target: Optional directory to switch the local file browser to.

        Returns:
            Self.
        """
        self.popped_out = True
        if target is not None:
            self._local_files.chdir(target)
        self._local_files.set_focus_within()
        return self

    def action_toggle_dock(self) -> None:
        """Toggle the dock side for the navigation."""
        config = load_config()
        config.navigation_left = not config.navigation_left
        save_config(config)
        self.docked_left = config.navigation_left

