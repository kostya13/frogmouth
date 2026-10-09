"""Provides the local files navigation pane."""

from __future__ import annotations

import asyncio

from collections.abc import Callable
from pathlib import Path
from typing import Iterable

from httpx import URL
from textual.app import ComposeResult
from textual.message import Message
from textual.timer import Timer
from textual.widgets import DirectoryTree

from ...utility import maybe_markdown
from .navigation_pane import NavigationPane


class FilteredDirectoryTree(DirectoryTree):  # pylint:disable=too-many-ancestors
    """A `DirectoryTree` filtered for the Markdown viewer."""

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        """Filter the directory tree for the Markdown viewer.

        Args:
            paths: The paths to be filtered.

        Returns:
            The parts filtered for the Markdown viewer.

        The filtered set will include all filesystem entries that aren't
        hidden (in a Unix sense of hidden) which are either a directory or a
        file that looks like it could be a Markdown document.
        """
        try:
            return [
                path
                for path in paths
                if not path.name.startswith(".")
                and path.is_dir()
                or (path.is_file() and maybe_markdown(path))
            ]
        except PermissionError:
            return []

    EXPAND_PASSES: Final[int] = 5
    """How many times to retry expanding as the tree loads lazily."""
    EXPAND_PASS_DELAY: Final[float] = 0.25
    """The delay between expansion passes, in seconds."""

    def __init__(self, *args, **kwargs) -> None:
        """Initialise the filtered directory tree."""
        super().__init__(*args, **kwargs)
        self._expand_generation: int = 0
        """Counter to invalidate expansion passes started earlier."""
        self._pending_reveal: Path | None = None
        """File to reveal after the tree root is switched."""
        self._root_switched: bool = False
        """Whether chdir() has already pointed the tree at its real root."""

    async def watch_path(self) -> None:
        """React to the tree root being switched via `chdir()`."""
        self._root_switched = True
        await super().watch_path()
        if self._pending_reveal is not None:
            pending, self._pending_reveal = self._pending_reveal, None
            self.call_after_refresh(self.reveal, pending)

    def expand_all(self) -> None:
        """Expand every directory in the tree.

        `DirectoryTree` loads directories lazily, so one pass only opens
        the levels loaded so far; a few timed passes let the expansion
        reach the full depth of the tree.
        """
        self._run_passes(self.root.expand_all, "expand")

    def collapse_all(self) -> None:
        """Collapse every directory in the tree.

        Pending directory loads re-expand their node as they complete
        (`DirectoryTree` expands nodes when it populates them), so the
        collapse also runs as a few timed passes.
        """
        self._run_passes(self._collapse_roots, "collapse")

    async def reveal(self, target: Path) -> None:
        """Expand the branches leading to a file and place the cursor on it.

        The directory tree loads lazily, so this walks down the path one
        level at a time, waiting for each directory to load before moving
        to the next.

        Args:
            target: The file to reveal within the tree.
        """
        # The tree loads lazily and reloads when the root is switched, so
        # the walk can lose a race with the loading queue; a few attempts
        # make the reveal stable.
        for _attempt in range(3):
            try:
                parts = target.absolute().relative_to(
                    self.path.absolute()
                ).parts
            except ValueError:
                if self._pending_reveal is None and not self._root_switched:
                    self._pending_reveal = target
                return
            if await self._reveal(parts):
                return
            await asyncio.sleep(0.5)

    async def _reveal(self, parts: tuple[str, ...]) -> bool:
        """Walk down the tree along the given path parts, expand the
        branches and place the cursor on the last node.

        Args:
            parts: The target path parts relative to the tree root.

        Returns:
            `True` if the target was revealed and selected.
        """
        node = self.root
        for part in parts:
            wanted = node.data.path / part if node.data else self.path / part
            # Wait for the node's children to arrive; the tree loads
            # directories in workers.
            for _ in range(30):
                children = list(node.children)
                if children:
                    break
                await asyncio.sleep(0.1)
            else:
                return False
            node = next(
                (
                    child
                    for child in children
                    if child.data is not None
                    and child.data.path == wanted
                ),
                None,
            )
            if node is None:
                return False
            if node.allow_expand and not node.is_expanded:
                node.expand()
                # Wait for the directory to load (its children appear).
                for _ in range(30):
                    if list(node.children):
                        break
                    await asyncio.sleep(0.1)
        # Wait until the target node has a display line, then select it.
        for _ in range(30):
            if node.line != -1:
                self.select_node(node)
                self.scroll_to_node(node, animate=False)
                return True
            await asyncio.sleep(0.1)
        return False

    def _collapse_roots(self) -> None:
        """Collapse the children of the tree's root."""
        for child in self.root.children:
            child.collapse_all()

    def _run_passes(
        self, operation: Callable[[], None], direction: str
    ) -> None:
        """Run a tree operation now, and a few more times as nodes load.

        Args:
            operation: The operation to run on each pass.
            direction: Either `"expand"` or `"collapse"`.
        """
        self._expand_generation += 1
        self._pass(self._expand_generation, 0, operation, direction)

    def _pass(
        self,
        generation: int,
        pass_number: int,
        operation: Callable[[], None],
        direction: str,
    ) -> None:
        """Run one pass of the given operation, scheduling more as needed.

        Args:
            generation: The generation this pass belongs to.
            pass_number: The number of this pass.
            operation: The operation to run on each pass.
            direction: Either `"expand"` or `"collapse"`.
        """
        if generation != self._expand_generation:
            return
        operation()
        if pass_number < self.EXPAND_PASSES:
            self.set_timer(
                self.EXPAND_PASS_DELAY,
                lambda: self._pass(
                    generation, pass_number + 1, operation, direction
                ),
            )


class LocalFiles(NavigationPane):
    """Local file picking navigation pane."""

    DEFAULT_CSS = """
    LocalFiles {
        height: 100%;
    }
    LocalFiles > DirectoryTree {
        background: $panel;
        width: 1fr;
        scrollbar-size: 1 1;
    }

    LocalFiles > DirectoryTree:focus .tree--cursor, LocalFiles > DirectoryTree .tree--cursor {
        background: $accent 50%;
        color: $text;
    }
    """

    def __init__(self) -> None:
        """Initialise the local files navigation pane."""
        super().__init__("[L]ocal")
        self.border_title = "Tree"

    def compose(self) -> ComposeResult:
        """Compose the child widgets."""
        tree = FilteredDirectoryTree(Path("~").expanduser())
        # Don't show the root directory itself; show its content as the
        # top level of the tree.
        tree.show_root = False
        tree.auto_expand = True
        yield tree

    def chdir(self, path: Path) -> None:
        """Change the filesystem view to the given directory.

        Args:
            path: The path to change to.
        """
        self.query_one(FilteredDirectoryTree).path = path

    def set_focus_within(self) -> None:
        """Focus the directory tree.."""
        self.query_one(DirectoryTree).focus(scroll_visible=False)

    class Goto(Message):
        """Message that requests the viewer goes to a given location."""

        def __init__(self, location: Path | URL) -> None:
            """Initialise the history goto message.

            Args:
                location: The location to go to.
            """
            super().__init__()
            self.location = location
            """The location to go to."""

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        """Handle a file being selected in the directory tree.

        Args:
            event: The direct tree selection event.
        """
        event.stop()
        self.post_message(self.Goto(Path(event.path)))
