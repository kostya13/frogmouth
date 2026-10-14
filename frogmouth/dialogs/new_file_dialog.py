"""Provides a dialog for creating a new Markdown file or directory."""

from __future__ import annotations

from textual import events, on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Input, Label, TabPane, TabbedContent


class NewFileDialog(ModalScreen[tuple[str, str, bool]]):
    """Modal dialog for creating a new Markdown file or directory.

    The result is a tuple of the kind of thing to create (`file` or
    `directory`), the name for it, and the open-for-editing choice. If the
    dialog is cancelled the result is `None`.
    """

    DEFAULT_CSS = """
    NewFileDialog {
        align: center middle;
    }

    NewFileDialog > Vertical {
        background: $panel;
        height: auto;
        width: 50%;
        border: thick $primary;
    }

    NewFileDialog > Vertical > * {
        width: 100%;
        height: auto;
    }

    NewFileDialog Input {
        width: 1fr;
        margin: 1 2;
    }

    NewFileDialog Label {
        margin-left: 2;
    }

    NewFileDialog Checkbox {
        margin: 1 2;
    }

    NewFileDialog Button {
        margin-right: 1;
    }

    NewFileDialog #buttons {
        width: 100%;
        align-horizontal: right;
        padding-right: 1;
    }
    """
    """The default styling for the new file dialog."""

    BINDINGS = [
        Binding("escape", "app.pop_screen", "", show=False),
    ]
    """Bindings for the dialog."""

    def compose(self) -> ComposeResult:
        """Compose the child widgets."""
        with Vertical():
            with TabbedContent(initial="file"):
                with TabPane("File", id="file"):
                    yield Label(
                        "Name of the new Markdown file (without extension):"
                    )
                    yield Input(id="file-name")
                    yield Checkbox("Open for editing", id="open-for-editing")
                with TabPane("Directory", id="directory"):
                    yield Label("Name of the new directory:")
                    yield Input(id="directory-name")
            with Horizontal(id="buttons"):
                yield Button("OK", id="ok", variant="primary")
                yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        """Set up the dialog once the DOM is ready."""
        self.query_one("#file-name", Input).focus()

    @on(TabbedContent.TabActivated)
    def tab_switched(self, event: TabbedContent.TabActivated) -> None:
        """Focus the input of the newly activated tab.

        Args:
            event: The tab activation event.
        """
        input_id = (
            "#file-name" if event.pane.id == "file" else "#directory-name"
        )
        self.query_one(input_id, Input).focus()

    @on(Button.Pressed, "#cancel")
    def cancel_input(self) -> None:
        """Cancel the input operation."""
        self.app.pop_screen()

    @property
    def _active_tab_id(self) -> str:
        """The ID of the currently active tab."""
        return self.query_one(TabbedContent).active

    def accept_input(self) -> None:
        """Accept and return the requested name and options."""
        input_id = (
            "#file-name" if self._active_tab_id == "file" else "#directory-name"
        )
        if name := self.query_one(input_id, Input).value.strip():
            if self._active_tab_id == "file":
                self.dismiss(
                    ("file", name, self.query_one("#open-for-editing", Checkbox).value)
                )
            else:
                self.dismiss(("directory", name, False))

    @on(Input.Submitted)
    @on(Button.Pressed, "#ok")
    def submit_input(self, event: events.Event) -> None:
        """Submit the dialog from any widget.

        Args:
            event: The event that triggered the submission.
        """
        self.accept_input()

    def on_key(self, event: events.Key) -> None:
        """Handle enter/return on widgets that don't submit the input.

        Args:
            event: The key event.
        """
        if event.key in ("enter", "return") and not isinstance(
            app.focused if (app := self.app) else None, Input
        ):
            self.accept_input()
