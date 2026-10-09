"""The main application class for the viewer."""

from argparse import ArgumentParser, Namespace
from pathlib import Path
from webbrowser import open as open_url

from textual import __version__ as textual_version  # pylint: disable=no-name-in-module
from textual.app import App

from .. import __version__
from ..data import load_config
from ..dialogs import ErrorDialog
from ..screens import Main
from ..widgets import Navigation
from ..utility.advertising import APPLICATION_TITLE, PACKAGE_NAME


class MarkdownViewer(App[None]):
    """The main application class."""

    TITLE = APPLICATION_TITLE
    """The main title for the application."""

    ENABLE_COMMAND_PALETTE = False

    def __init__(self, cli_args: Namespace) -> None:
        """Initialise the application.

        Args:
            cli_args: The command line arguments.
        """
        super().__init__()
        self.animation_level = "none"
        self._args = cli_args

    async def on_mount(self) -> None:
        """Set up the application after the DOM is ready."""
        # Work out the wiki directory: the configuration takes priority, and
        # after that we fall back to ~/wiki.
        config = load_config()
        wiki = (
            Path(config.wikipath).expanduser()
            if config.wikipath
            else Path("~/wiki").expanduser()
        )

        # If the wiki directory doesn't exist there's nothing we can do
        # apart from tell the user what to create and then quit.
        if not wiki.is_dir():
            self.push_screen(
                ErrorDialog(
                    "Missing wiki directory",
                    f"The wiki directory {wiki} does not exist.\n\n"
                    f"Please create it (for example with 'mkdir -p {wiki}') and "
                    "then run this application again.",
                ),
                callback=lambda _: self.exit(),
            )
            return

        main = Main(" ".join(self._args.file) if self._args.file else None)
        await self.push_screen(main)
        main.query_one(Navigation).jump_to_local_files(wiki)

    def action_visit(self, url: str) -> None:
        """Visit the given URL, via the operating system.

        Args:
            url: The URL to visit.
        """
        open_url(url)


def get_args() -> Namespace:
    """Parse and return the command line arguments.

    Returns:
        The result of parsing the arguments.
    """

    # Create the parser object.
    parser = ArgumentParser(
        prog=PACKAGE_NAME,
        description=f"{APPLICATION_TITLE} -- A Markdown viewer for the terminal.",
        epilog=f"v{__version__}",
    )

    # Add --version
    parser.add_argument(
        "-v",
        "--version",
        help="Show version information.",
        action="version",
        version=f"%(prog)s {__version__} (Textual v{textual_version})",
    )

    # The remainder is the file to view.
    parser.add_argument("file", help="The Markdown file to view", nargs="*")

    # Finally, parse the command line.
    return parser.parse_args()


def run() -> None:
    """Run the application."""
    MarkdownViewer(get_args()).run()
