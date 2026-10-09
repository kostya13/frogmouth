"""The main screen for the application."""

from __future__ import annotations

from os import getenv
from shlex import split as shlex_split
from subprocess import run as run_process
from functools import partial
from pathlib import Path
from typing import Awaitable, Callable

from httpx import URL
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.events import Paste
from textual.screen import Screen
from textual.widgets import Footer, Markdown

from ..data import load_config, load_history, save_config, save_history
from ..dialogs import ErrorDialog, HelpDialog, HistoryDialog
from ..utility import is_likely_url, maybe_markdown
from ..utility.advertising import APPLICATION_TITLE, PACKAGE_NAME
from ..widgets import Navigation, Pathbar, Viewer
from ..widgets.navigation_panes import LocalFiles, TableOfContents
from ..widgets.navigation_panes.local_files import FilteredDirectoryTree


class Main(Screen[None]):  # pylint:disable=too-many-public-methods
    """The main screen for the application."""

    DEFAULT_CSS = """
    .focusable {
        border: blank;
    }

    .focusable:focus {
        border: heavy $accent !important;
    }


    Screen Tabs {
        border: blank;
        height: 5;
    }

    Screen Tabs:focus {
        border: heavy $accent !important;
        height: 5;
    }

    Screen TabbedContent TabPane {
        padding: 0;
        border: blank;
    }

    #viewer-host {
        height: 1fr;
    }

    #viewer-host TableOfContents {
        dock: right;
        width: 20;
        background: $panel;
        border: blank;
        padding: 0 !important;
    }

    #viewer-host TableOfContents:focus {
        border: heavy $accent !important;
    }

    #viewer-host TableOfContents > MarkdownTableOfContents {
        height: 100%;
    }

    /* Full screen mode: the viewer takes over the whole screen. */
    #viewer-host.full-screen {
        width: 100%;
        height: 100%;
        layers: fullscreen;
        layer: fullscreen;
    }

    #viewer-host.full-screen Navigation,
    #viewer-host.full-screen TableOfContents {
        display: none;
    }

    .full-screen-hidden {
        display: none;
    }

    #viewer-host.full-screen Viewer:focus {
        border: none !important;
    }

    #viewer-host.full-screen Viewer Markdown {
        margin: 0;
    }

    """

    BINDINGS = [
        Binding("c", "table_of_contents", "Contents", show=False),
        Binding("l", "local_files", "Local", show=False),
        Binding("h", "history", "History", show=False),
        Binding("e", "edit", "Edit", show=False),
        Binding("ctrl+l", "local_files", "", show=False),
        Binding("ctrl+left", "backward", "", show=False),
        Binding("ctrl+right", "forward", "", show=False),
        Binding("ctrl+e", "edit", "", show=False),
        Binding("ctrl+r", "reload", "", show=False),
        Binding("ctrl+t", "table_of_contents", "", show=False),
        Binding("ctrl+f", "full_screen", "Full screen"),
        Binding("escape", "escape", "", show=False),
        Binding("f1", "help", "Help"),
        Binding("plus", "expand_tree", "Expand all"),
        Binding("underscore", "collapse_tree", "Collapse all"),
        Binding("ctrl+n", "navigation", "Navigation"),
        Binding("ctrl+q", "app.quit", "Quit"),
        Binding("f10", "toggle_theme", "", show=False),
    ]
    """The keyboard bindings for the main screen."""

    def __init__(self, initial_location: str | None = None) -> None:
        """Initialise the main screen.

        Args:
            initial_location: The initial location to view.
        """
        super().__init__()
        self._initial_location = initial_location

    def compose(self) -> ComposeResult:
        """Compose the main screen.

        Returns:
            The result of composing the screen.
        """
        yield Pathbar()
        with Horizontal(id="viewer-host"):
            yield Navigation()
            yield Viewer(classes="focusable")
            yield TableOfContents()
        yield Footer()

    def visit(self, location: Path | URL, remember: bool = True) -> None:
        """Visit the given location.

        Args:
            location: The location to visit.
            remember: Should the visit be added to the history?
        """
        # If the location we've been given looks like it is markdown, be it
        # locally in the filesystem or out on the web...
        if maybe_markdown(location):
            # ...attempt to visit it in the viewer.
            self.query_one(Viewer).visit(location, remember)
        elif isinstance(location, Path):
            # So, it's not Markdown, but it *is* a Path of some sort. If the
            # resource seems to exist...
            if location.exists():
                # ...ask the OS to open it.
                open_url(f"file:///{location.absolute()}")
            else:
                # It's a Path but it doesn't exist, there's not much else we
                # can do with it.
                self.app.push_screen(
                    ErrorDialog(
                        "Does not exist",
                        f"Unable to open {location} because it does not exist.",
                    )
                )
        else:
            # By this point all that's left is it's a URL that, on the
            # surface, doesn't look like a Markdown file. Let's hand off to
            # the operating system anyway.
            open_url(str(location), new=2, autoraise=True)

    async def on_mount(self) -> None:
        """Set up the main screen once the DOM is ready."""

        # Currently Textual's Markdown can steal focus, which gets confusing
        # as it's not obvious *what* is focused. So let's stop it from
        # allowing the content to get focus.
        #
        # https://github.com/Textualize/textual/issues/2380
        self.query_one(Markdown).can_focus_children = False

        # Load up any history that might be saved.
        if history := load_history():
            self.query_one(Viewer).load_history(history)

        # If we've been tasked to start up looking at a very specific
        # location, start up looking at that.
        if self._initial_location is not None:
            location: Path | URL = (
                Path(self._initial_location).expanduser()
                if not is_likely_url(self._initial_location)
                else URL(self._initial_location)
            )
            self.visit(location)
        else:
            # Fall back to the last visited local document; if it no longer
            # exists, the built-in welcome placeholder stays on screen.
            last = next(
                (item for item in reversed(history) if isinstance(item, Path)),
                None,
            )
            if last is not None and last.exists():
                self.visit(last, remember=False)

    def on_navigation_hidden(self) -> None:
        """React to the navigation sidebar being hidden."""
        self.query_one(Viewer).focus()

    def on_local_files_goto(self, event: LocalFiles.Goto) -> None:
        """Visit a local file in the viewer.

        Args:
            event: The local file visit request event.
        """
        self.visit(event.location)

    def show_history(self) -> None:
        """Show the history dialog."""
        self.app.push_screen(
            HistoryDialog(self.query_one(Viewer).history.locations),
            callback=self._visit_from_history,
        )

    def _visit_from_history(self, location: Path | URL | None) -> None:
        """Visit a location chosen from the history dialog.

        Args:
            location: The location to visit, `None` if the dialog was
                cancelled.
        """
        if location is None:
            return
        self.visit(location, remember=location != self.query_one(Viewer).location)

    def on_history_dialog_delete(self, event: HistoryDialog.Delete) -> None:
        """Handle a request to delete an item from history.

        Args:
            event: The event to handle.
        """
        self.query_one(Viewer).delete_history(event.history_id)

    def on_history_dialog_clear(self) -> None:
        """handle a request to clear down all of history."""
        self.query_one(Viewer).clear_history()

    def on_viewer_location_changed(self, event: Viewer.LocationChanged) -> None:
        """Update for the location being changed.

        Args:
            event: The location change event.
        """
        # Update the pathbar with whatever is appropriate for the new
        # location.
        self.query_one(Pathbar).location = Pathbar.display_text(
            event.viewer.location
        )
        # If the newly-arrived-at location is a local file, reveal it within
        # the local files tree.
        if isinstance(event.viewer.location, Path):
            tree = self.query_one(Navigation).query_one(FilteredDirectoryTree)
            tree.call_after_refresh(tree.reveal, event.viewer.location)
        # Having safely arrived at a new location, that implies that we want
        # to focus on the viewer.
        self.query_one(Viewer).focus()

    def on_viewer_history_updated(self, event: Viewer.HistoryUpdated) -> None:
        """Handle the viewer updating the history.

        Args:
            event: The history update event.
        """
        save_history(event.viewer.history.locations)

    def on_markdown_table_of_contents_updated(
        self, event: Markdown.TableOfContentsUpdated
    ) -> None:
        """Handle the table of contents of the document being updated.

        Args:
            event: The table of contents update event to handle.
        """
        self.query_one(TableOfContents).on_table_of_contents_updated(event)

    def on_markdown_table_of_contents_selected(
        self, event: Markdown.TableOfContentsSelected
    ) -> None:
        """Handle the user selecting something from the table of contents.

        Args:
            event: The table of contents selection event to handle.
        """
        self.query_one(Viewer).scroll_to_block(event.block_id)

    def on_markdown_link_clicked(self, event: Markdown.LinkClicked) -> None:
        """Handle a link being clicked in the Markdown document.

        Args:
            event: The Markdown link click event to handle.
        """
        # We'll be using the current location to help work out some relative
        # things.
        current_location = self.query_one(Viewer).location
        # If the link we're to handle obviously looks like URL...
        if is_likely_url(event.href):
            # ...handle it as such. No point in trying to do anything else.
            self.visit(URL(event.href))
        elif isinstance(current_location, URL):
            # Seems we're currently visiting a remote location, and the href
            # looks like a simple file path, so let's make a best effort to
            # visit the file at the remote location.
            self.visit(current_location.copy_with().join(event.href))
        elif (local_file := Path(event.href)).exists():
            # It looks like a local file and it exists...
            self.visit(local_file)
        elif (
            isinstance(current_location, Path)
            and (local_file := (current_location.parent / Path(event.href)))
            .absolute()
            .exists()
        ):
            # It looks like a local file, and tested relative to the
            # document we found it exists in the local filesystem, so let's
            # assume that's what we're supposed to handle.
            self.visit(local_file)
        elif event.href.startswith("#") and event.markdown.goto_anchor(event.href[1:]):
            # The href started with a # and the remains of it were satisfied
            # as an anchor within the document of the Markdown. We should
            # have scrolled to about the right spot in the document so we
            # don't need to do anything else.
            pass
        else:
            # Yeah, not sure *what* this link is. Rather than silently fail,
            # let's let the user know we don't know how to process this.
            self.app.push_screen(
                ErrorDialog(
                    "Unable to handle link",
                    f"Unable to work out how to handle this link:\n\n{event.href}",
                )
            )

    def on_paste(self, event: Paste) -> None:
        """Handle a paste event.

        Args:
            event: The paste event.

        This method is here to capture paste events that look like the name
        of a local file (later I may add URL support too). The main purpose
        of this is to handle drag/drop into the terminal.
        """
        if (candidate_file := Path(event.text)).exists():
            self.visit(candidate_file)

    def action_navigation(self) -> None:
        """Toggle the availability of the navigation sidebar."""
        self.query_one(Navigation).toggle()

    def _set_full_screen(self, full_screen: bool) -> None:
        """Turn full screen viewing of the document on or off.

        Args:
            full_screen: Should the viewer take over the whole screen?
        """
        host = self.query_one("#viewer-host")
        host.set_class(full_screen, "full-screen")
        self.query_one(Pathbar).set_class(full_screen, "full-screen-hidden")
        self.query_one(Footer).set_class(full_screen, "full-screen-hidden")

    def action_full_screen(self) -> None:
        """Toggle full screen viewing of the document."""
        self._set_full_screen(
            not self.query_one("#viewer-host").has_class("full-screen")
        )

    def action_escape(self) -> None:
        """Process the escape key."""
        # Escape only leaves full screen mode; it never exits the
        # application. If the navigation is focused it gets hidden.
        if self.query_one("#viewer-host").has_class("full-screen"):
            self._set_full_screen(False)
        elif self.query("Navigation:focus-within"):
            self.query_one(Navigation).popped_out = False

    def action_focus_navigation(self) -> None:
        """Move focus to the navigation sidebar."""
        self.query_one(Navigation).focus_tab()

    def action_table_of_contents(self) -> None:
        """Focus the table of contents pane."""
        self.query_one(TableOfContents).set_focus_within()

    def action_local_files(self) -> None:
        """Display and focus the local files selection pane."""
        self.query_one(Navigation).jump_to_local_files()

    def action_history(self) -> None:
        """Show the history dialog."""
        self.show_history()

    def action_backward(self) -> None:
        """Go backward in the history."""
        self.query_one(Viewer).back()

    def action_forward(self) -> None:
        """Go forward in the history."""
        self.query_one(Viewer).forward()

    def action_help(self) -> None:
        """Show the help."""
        self.app.push_screen(HelpDialog())

    def action_expand_tree(self) -> None:
        """Expand every directory in the local file tree."""
        self.query_one(Navigation).query_one(FilteredDirectoryTree).expand_all()

    def action_collapse_tree(self) -> None:
        """Collapse every directory in the local file tree."""
        self.query_one(Navigation).query_one(FilteredDirectoryTree).collapse_all()

    def action_toggle_theme(self) -> None:
        """Toggle the light/dark mode theme."""
        config = load_config()
        config.light_mode = not config.light_mode
        save_config(config)
        # pylint:disable=attribute-defined-outside-init
        self.app.dark = not config.light_mode

    def action_reload(self) -> None:
        """Reload the current document."""
        self.query_one(Viewer).reload()

    def action_edit(self) -> None:
        """Open the current document in an external editor."""
        location = self.query_one(Viewer).location

        # Only local files can be edited; anything else (or nothing at all)
        # is an error.
        if not isinstance(location, Path):
            self.app.push_screen(
                ErrorDialog(
                    "Not an editable location",
                    "The current view isn't a local file, so it can't be edited.",
                )
            )
            return

        # Work out the editor command: the configuration takes priority, and
        # after that we fall back to $EDITOR, and then to vim.
        editor = load_config().editor or getenv("EDITOR") or "vim"

        # Hand the terminal over to the editor, then reload the document in
        # case the user changed it.
        with self.app.suspend():
            run_process([*shlex_split(editor), str(location)])
        self.query_one(Viewer).reload()
