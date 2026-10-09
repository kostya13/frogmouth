"""Provides the navigation panel widget."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.message import Message
from textual.reactive import var
from textual.widgets import TabbedContent, Tabs
from typing_extensions import Self

from ..data import load_config, save_config
from .navigation_panes.bookmarks import Bookmarks
from .navigation_panes.history import History
from .navigation_panes.local_files import LocalFiles
from .navigation_panes.navigation_pane import NavigationPane
from .navigation_panes.table_of_contents import TableOfContents


class Navigation(Vertical, can_focus=False, can_focus_children=True):
    """A navigation panel widget."""

    DEFAULT_CSS = """
    Navigation {
        width: 44;
        background: $panel;
        display: block;
        dock: left;
    }

    Navigation.hidden {
        display: none;
    }

    TabbedContent {
        height: 100% !important;
        scrollbar-size: 1 1;
    }

    ContentSwitcher {
        height: 1fr !important;
    }
    """

    BINDINGS = [
        Binding("comma,a,ctrl+left,shift+left", "previous_tab", "", show=False),
        Binding("full_stop,d,ctrl+right,shift+right", "next_tab", "", show=False),
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
        self._history = History()
        with TabbedContent() as tabs:
            self._tabs = tabs
            yield self._local_files
            yield self._history

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

    @property
    def history(self) -> History:
        """The history widget."""
        return self._history

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
        self._local_files.activate()
        self.call_after_refresh(self.focus_tab)
        return self


    def jump_to_history(self) -> Self:
        """Switch to and focus the history pane.

        Returns:
            Self.
        """
        self.popped_out = True
        self._history.activate()
        self.call_after_refresh(self.focus_tab)
        return self


    def action_previous_tab(self) -> None:
        """Switch to the previous tab in the navigation pane."""
        self.query_one(Tabs).action_previous_tab()
        self.call_after_refresh(self.focus_tab)

    def action_next_tab(self) -> None:
        """Switch to the next tab in the navigation pane."""
        self.query_one(Tabs).action_next_tab()
        self.call_after_refresh(self.focus_tab)

    def action_toggle_dock(self) -> None:
        """Toggle the dock side for the navigation."""
        config = load_config()
        config.navigation_left = not config.navigation_left
        save_config(config)
        self.docked_left = config.navigation_left

    def focus_tab(self) -> None:
        """Focus the currently active tab."""
        if active := self._tabs.active:
            self.query_one(
                f"NavigationPane#{active}", NavigationPane
            ).set_focus_within()


class NavSide(Vertical, can_focus=False, can_focus_children=True):
    """The right-hand navigation panel (contents and bookmarks)."""

    DEFAULT_CSS = """
    NavSide {
        width: 44;
        background: $panel;
        display: block;
        dock: right;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the right-hand navigation panes.

        Returns:
            The result of composing the panel.
        """
        self._contents = TableOfContents()
        with TabbedContent() as tabs:
            self._tabs = tabs
            yield self._contents
            if load_config().show_bookmarks:
                self._bookmarks = Bookmarks()
                yield self._bookmarks

    @property
    def table_of_contents(self) -> TableOfContents:
        """The table of contents widget."""
        return self._contents

    @property
    def bookmarks(self) -> Bookmarks | None:
        """The bookmarks widget, if it is shown; `None` if hidden."""
        return getattr(self, "_bookmarks", None)

    def jump_to_contents(self) -> Self:
        """Switch to and focus the table of contents pane.

        Returns:
            Self.
        """
        self._contents.activate()
        self.call_after_refresh(self.focus_tab)
        return self

    def jump_to_bookmarks(self) -> Self:
        """Switch to and focus the bookmarks pane, if it is shown.

        Returns:
            Self.
        """
        if getattr(self, "_bookmarks", None) is None:
            return self
        self._bookmarks.activate()
        self.call_after_refresh(self.focus_tab)
        return self

    def focus_tab(self) -> None:
        """Focus the currently active tab."""
        if active := self._tabs.active:
            self.query_one(
                f"NavigationPane#{active}", NavigationPane
            ).set_focus_within()
