"""Provides a dialog for browsing and selecting from the visit history."""

from __future__ import annotations

from functools import partial
from httpx import URL
from pathlib import Path

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import OptionList
from textual.widgets.option_list import Option

from .yes_no_dialog import YesNoDialog


class Entry(Option):
    """An entry in the history."""

    def __init__(self, history_id: int, location: Path | URL) -> None:
        """Initialise the history entry item.

        Args:
            history_id: The ID of the item of history.
            location: The location being added to history.
        """
        super().__init__(self._as_prompt(location))
        self.history_id = history_id
        """The ID of the item of history."""
        self.location = location
        """The location for this entry in the history."""

    @staticmethod
    def _as_prompt(location: Path | URL) -> Text:
        """Depict the location as a decorated prompt.

        Args:
            location: The location to depict.

        Returns:
            A prompt with icon, etc.
        """
        if isinstance(location, Path):
            return Text.from_markup(
                f":page_facing_up: [bold]{location.name}[/]\n[dim]{location.parent}[/]",
                overflow="ellipsis",
            )
        return Text.from_markup(
            f":globe_with_meridians: [bold]{Path(location.path).name}[/]"
            f"\n[dim]{Path(location.path).parent}\n{location.host}[/]",
            overflow="ellipsis",
        )


class HistoryDialog(ModalScreen[None]):
    """Modal dialog that shows the visit history."""

    DEFAULT_CSS = """
    HistoryDialog {
        align: center middle;
    }

    HistoryDialog > Vertical {
        border: thick $primary 50%;
        width: 60%;
        height: 80%;
        background: $boost;
    }

    HistoryDialog > Vertical > OptionList {
        height: 1fr;
        margin: 1 2;
    }
    """

    BINDINGS = [
        Binding("escape", "dismiss(None)", "", show=False),
        Binding("delete", "delete", "Delete the history item"),
        Binding("backspace", "clear", "Clear the history"),
    ]
    """Bindings for the history dialog."""

    class Delete(Message):
        """Message that requests the viewer to delete an item of history."""

        def __init__(self, history_id: int) -> None:
            """Initialise the history delete message.

            Args:
                history_id: The ID of the item of history to delete.
            """
            super().__init__()
            self.history_id = history_id
            """The ID of the item of history to delete."""

    class Clear(Message):
        """Message that requests that the history be cleared."""

    def __init__(self, locations: list[Path | URL]) -> None:
        """Initialise the history dialog.

        Args:
            locations: The locations in the history.
        """
        super().__init__()
        self._locations = locations

    def compose(self) -> ComposeResult:
        """Compose the child widgets."""
        with Vertical():
            yield OptionList()

    def on_mount(self) -> None:
        """Populate the option list once the DOM is set up."""
        option_list = self.query_one(OptionList)
        for history_id, location in reversed(list(enumerate(self._locations))):
            option_list.add_option(Entry(history_id, location))
        if option_list.option_count:
            option_list.highlighted = 0
        option_list.focus()

    def on_option_list_option_selected(
        self, event: OptionList.OptionSelected
    ) -> None:
        """Handle an entry in the history being selected.

        Args:
            event: The event to handle.
        """
        assert isinstance(event.option, Entry)
        self.dismiss(event.option.location)

    def delete_history(self, history_id: int, delete_it: bool) -> None:
        """Delete a given history entry.

        Args:
            history_id: The ID of the item of history to delete.
            delete_it: Should it be deleted?
        """
        if delete_it:
            self.post_message(self.Delete(history_id))

    def action_delete(self) -> None:
        """Delete the highlighted item from history."""
        history = self.query_one(OptionList)
        if (item := history.highlighted) is not None:
            assert isinstance(entry := history.get_option_at_index(item), Entry)
            self.app.push_screen(
                YesNoDialog(
                    "Delete history entry?",
                    "Are you sure you want to delete the history entry?",
                ),
                partial(self.delete_history, entry.history_id),
            )

    def clear_history(self, clear_it: bool) -> None:
        """Perform a history clear.

        Args:
            clear_it: Should it be cleared?
        """
        if clear_it:
            self.post_message(self.Clear())

    def action_clear(self) -> None:
        """Clear out the whole history."""
        self.app.push_screen(
            YesNoDialog(
                "Clear history?",
                "Are you sure you want to clear everything out of history?",
            ),
            self.clear_history,
        )
