# Changelog

All notable changes to pyFastPlot are documented in this file.

This project follows a simple Keep a Changelog style:

- `Added` for new features
- `Changed` for behavior or UI changes
- `Fixed` for bug fixes
- `Removed` for removed features

## [Unreleased]

### Added
- Placeholder for changes after the initial 1.0.0 project snapshot.

## [1.0.0] - 2026-05-30

### Added
- Initial pyFastPlot desktop application.
- CSV loading and editable in-memory tables.
- Clipboard paste with `Ctrl+V`.
- Text Import Wizard with `Ctrl+Shift+V`.
- Table row/column deletion, cell clearing, column renaming, undo/redo, and
  row-to-label promotion.
- Index or selected-column X-axis plotting.
- Plot replacement and overlay plotting.
- Matplotlib figure options for size, DPI, font, title, axis labels, axis
  limits, log scales, legend, and line styling.
- Plot image copy to clipboard.
- PNG/SVG plot export.
- Application logging under `%USERPROFILE%\.pyfastplot\pyfastplot.log`.
- AGENTS.md with repository-specific coding-agent guidance.
- pyproject.toml with package metadata, Ruff configuration, pytest settings, and
  optional development/build dependencies.
- .gitattributes for stable text and binary file handling.
- English and Korean user manuals.
- Packaging README with direct Nuitka and NSIS commands.
- Minimal pytest coverage for the data model and resource path resolution.
- Transparent-background pyFastPlot icon PNG/ICO files.

### Changed
- Standardized the repository layout and documentation.
- Moved build-only packages out of requirements.txt and into the `build`
  optional dependency group.
- Updated NSIS packaging to use 64-bit Program Files, 64-bit registry view,
  application icons, stable shortcut icons, and no finish-page auto-run.
- Reworked launcher and resource path handling to avoid machine-local paths.
- Kept the presenter instance alive so Qt signal connections remain active.
- Applied Ruff formatting and safe lint cleanups across the source tree.

### Removed
- Removed the architecture document in favor of user manuals.
- Removed the standalone icon-conversion utility from scripts.
- Removed legacy data-analytics icon assets.
