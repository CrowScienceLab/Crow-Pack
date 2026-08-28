# Changelog

## [1.0d] - 2026-08-28

### Added

- Custom archive context menu with bounded image thumbnails and safe copy-out actions.
- ZIP-only delete and move-out actions; ISO and other read-only formats remain copy-only.
- Lossless PDF stream and duplicate-object optimization with signature protection.
- Home-toolbar update status and Windows per-user file-association controls.

### Fixed

- Checkbox clicks no longer toggle twice through the containing table row.
- Native file drags restore the neon drop-zone feedback through a Qt-to-JavaScript signal.
- Disabled Chromium's unrelated `View page source` context menu.

### Changed

- Expanded directory selection to include descendant archive entries.

## [1.0.0] - 2026-08-28

### Added

- Read-only ISO image browsing and safe file copying for ISO 9660, Joliet, Rock Ridge, and UDF bridge images.
- A dedicated ISO-open button on the home toolbar.

### Fixed

- Native file drops now retain their absolute Windows paths when dropped on the WebEngine home view.

### Removed

- The redundant new-compression toolbar button.
- File-association registration and update-check controls from the information dialog.

## [0.9.0] - 2026-08-28

### Added

- AES-256 ZIP encryption through `pyzipper` 0.4.0 or newer.
- Shared extraction policy for traversal, link, collision, and decompression-bomb protection.
- Security regression tests and GitHub Actions checks.
- Release metadata, dependency bounds, security policy, and repository hygiene files.

### Changed

- Restricted the privileged Qt WebEngine page to bundled local resources.
- Rendered archive-controlled names as text instead of HTML.
- Replaced shell-based Windows commands with argument-safe process calls.
- Updated minimum secure versions for `py7zr` and `rarfile`.
- Standardized the public version label as `v0.9.0`.

### Removed

- Legacy Crow Press launch and one-time folder rename scripts.
- Python bytecode and cache artifacts from the release tree.
