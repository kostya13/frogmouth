"""Provides a dialog for creating a new Markdown file."""

from __future__ import annotations

from textual import events, on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Input, Label


class NewFileDialog(ModalScreen[tuple[str, bool]]):
    """Modal dialog for creating a new Markdown file."""

    DEFAULT_CSS = """
    NewFileDialog {
        align: center middle;
    }

    NewFileDialog > Vertical {
        background: $panel;
        height: auto;
        width: auto;
        border: thick $primary;
    }

    NewFileDialog > Vertical > * {
        width: auto;
        height: auto;
    }

    NewFileDialog Input {
        width: 40;
        margin: 1;
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
            with Vertical(id="input"):
                yield Label("Name of the new Markdown file (without extension):")
                yield Input()
                yield Checkbox("Open for editing", id="open-for-editing")
            with Horizontal(id="buttons"):
                yield Button("OK", id="ok", variant="primary")
                yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        """Set up the dialog once the DOM is ready."""
        self.query_one(Input).focus()

    @on(Button.Pressed, "#cancel")
    def cancel_input(self) -> None:
        """Cancel the input operation."""
        self.app.pop_screen()

    @on(Input.Submitted)
    @on(Button.Pressed, "#ok")
    def accept_input(self) -> None:
        """Accept and return the requested file name."""
        if name := self.query_one(Input).value.strip():
            self.dismiss((name, self.query_one(Checkbox).value))

    def on_key(self, event: events.Key) -> None:
        """Handle enter/return on widgets that don't submit the input.

        Args:
            event: The key event.
        """
        if event.key in ("enter", "return") and not isinstance(
            app.focused if (app := self.app) else None, Input
        ):
            self.accept_input()
