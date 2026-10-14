# Frogmouth ChangeLog

## 1.0.0 - Unreleased

### Added

- Front matter is now ignored when viewing a file.
  [#15](https://github.com/Textualize/frogmouth/issues/15)
- Added support for jumping to an internal anchor.
  [#91](https://github.com/Textualize/frogmouth/issues/91)
- Added the ability to edit the current local document in an external
  editor (`ctrl+e` or `e`). The editor is taken from the `editor`
  configuration option, falling back to `$EDITOR` and then `vim`.
- The local file browser now hides the root directory itself; its contents
  are shown as the top level of the tree.
- At startup, without an explicit command line file, the last visited local
  document is reopened; if it no longer exists, the built-in welcome
  placeholder stays on screen.
- Each location now appears at most once in the visit history: revisiting
  a document moves it to the end of the history instead of duplicating it.
  Duplicates already present in a saved history file are removed on load.
- Tree hotkeys: `+` expands the whole local file tree and `_` collapses it
  (the keys work with both the main and the numeric keypad rows).
- The document that is open in the viewer is now revealed within the local
  file tree: the branches leading to it are expanded and its entry is
  highlighted.
- The first letter of each navigation tab title is bracketed, e.g.
  `[C]ontents`, `[L]ocal`, `[B]ookmarks`, `[H]istory`.
- Full screen mode on `ctrl+f`: the viewer takes over the whole screen,
  without the pathbar, navigation, footer or margins; `Escape` (or
  `ctrl+f` again) returns to the normal view.
- The bookmarks pane can now be hidden: `show_bookmarks` in the
  configuration file controls whether the pane appears in the navigation
  (default: hidden).
- The indentation of the table of contents tree is now two characters
  per level instead of four.
- Search in the viewer on `/`: type a term, Enter cycles through the
  matching blocks, Escape closes the search bar.
- The table of contents pane moved out of the navigation sidebar to a
  separate panel docked on the right, 20 characters wide; it updates as
  documents are opened and `c`/`ctrl+t` focus it.
- The navigation sidebar has no padding.
- New file or directory creation on `n`/`ctrl+n`: the dialog has
  "File" and "Directory" tabs; for a file enter a name (the `.md`
  extension is added automatically) and optionally open it in the
  editor, for a directory just enter a name. New items are created next
  to the currently open document and the tree refreshes. Showing/hiding
  the navigation moved to `ctrl+o`.
- File deletion on `d`/`ctrl+d`: delete the file under the cursor in
  the local files tree, with a confirmation dialog; the tree refreshes
  afterwards.
- The history is now a dialog on `h`/`ctrl+y`: pick a location to visit
  it; `delete` removes an entry, `backspace` clears the history.
  The navigation sidebar is now just the local files tree.

### Removed

- Removed the address bar (omnibox). The current location is now shown in
  a static pathbar at the top of the screen.
- Removed the "About" dialog (`f2`); version information now lives only in
  the help dialog and the package metadata.
- Removed the now-unused `InformationDialog`.
- Removed the bookmarks feature: the bookmarks pane, the `b`/`ctrl+b`
  shortcuts, bookmarking the current document (`ctrl+d`), and the
  `show_bookmarks` configuration option.

### Fixed

- Fixed a crash when switching navigation tabs while focus is inside the
  navigation sidebar (`focus_tab` looked up panes by the tab ID, which
  carries a `--content-tab-` prefix in Textual 0.53).
- `Escape` no longer exits the application: it only leaves full screen
  mode (or hides the focused navigation pane). Use `ctrl+q` to quit.
- The `l` and `h` keys no longer switch navigation tabs when focus is
  inside the navigation; they now always reach the main screen
  `local_files`/`history` shortcuts.
- The `c`, `l`, `b` and `h` shortcuts no longer hide the navigation
  sidebar; they only switch to (and open, if hidden) the related pane.
  Use `Escape` or `ctrl+n` to hide the navigation.
- The scrollbars of the navigation panes (local files, bookmarks, history,
  table of contents) are now one character wide.
- The content of the viewer now sits one character from each edge of the
  viewing pane instead of the previous wide margins.

## [0.9.2] - 2023-11-28

### Changed

- Bumped to Textual v0.41.0.

## [0.9.1] - 2023-11-02

### Changed

- Bumped to Textual v0.41.0.

## [0.9.0] - 2023-08-07

### Fixed

- Fixed local documents no longer loading.
  [#74](https://github.com/Textualize/frogmouth/issues/74)

## [0.8.0] - 2023-07-20

### Changed

- Updated to work with [Textual](https://github.com/Textualize/textual)
  v0.30.0 or greater.

### Fixed

- Fixed the look and scrolling of the history navigation pane after recent
  changes to base Textual styling broke it.
  [#66](https://github.com/Textualize/frogmouth/issues/66)
- Fixed the look and scrolling of the bookmark navigation pane after recent
  changes to base Textual styling broke it.
  [#66](https://github.com/Textualize/frogmouth/issues/66)

## [0.7.0] - 2023-06-27

### Added

- Added support for using <kbd>Ctrl</kbd>+<kbd>r</kbd> to reload the current
  document.

### Fixed

- Added some extra error capture when attempting to build a forge URL while
  inferring the main branch name.
- Fixed following local file links where the file is document-relative and
  you're visiting with a CWD other than the document's.
  [#52](https://github.com/Textualize/frogmouth/issues/52)

## [0.6.0] - 2023-05-24

### Added

- Added Codeberg as a recognised forge for the "forge quick view".

### Changed

- Relaxed the required [Textual](https://github.com/Textualize/textual)
  dependency version requirement.

## [0.5.0] - 2023-05-08

### Changed

- Updated to work with [Textual](https://github.com/Textualize/textual) v0.24.0.

### Added

- Added a `changelog` command -- loads the Frogmouth ChangeLog from the
  repository for viewing.
- Added the ability to delete a single item of history from the history
  list. ([#34](https://github.com/Textualize/frogmouth/pull/34))
- Added the ability to clear down the whole of history.
  ([#34](https://github.com/Textualize/frogmouth/pull/34))
- Added toggling the navigation sidebar between left or right dock.
  ([#37](https://github.com/Textualize/frogmouth/pull/37))

### Changed

- Calling any navigation pane is now a toggle operation. If it isn't
  visible, it's made visible; if it's visible, the navigation sidebar is
  closed.

## [0.4.0] - 2023-05-03

### Added

- Added support for using <kbd>j</kbd> and <kbd>k</kbd> to scroll through
  the document.
- Added support for using <kbd>w</kbd> and <kbd>s</kbd> to scroll through the document.
- Added support for <kbd>space</kbd> to scroll through the document.
- Added <kbd>:</kbd> as a keypress for quickly getting to the input bar.
  ([#19](https://github.com/Textualize/frogmouth/pull/19))

### Changed

- Internal changes to the workings of the input dialogs, using the newer
  Textual screen result returning facility.
  ([#23](https://github.com/Textualize/frogmouth/pull/23))

## [0.3.2] - 2023-04-30

- Initial release
