# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- AGENTS.md with repository-specific coding-agent guidance.
- pyproject.toml with package metadata, Ruff configuration, pytest settings, and
  optional development/build dependencies.
- .gitattributes for stable text and binary file handling.
- English and Korean user manuals.
- Packaging README with direct Nuitka and NSIS commands.
- Minimal pytest coverage for the data model and resource path resolution.

### Changed
- Updated README to match the current project layout, build process, and docs.
- Moved build-only packages out of requirements.txt and into the `build`
  optional dependency group.
- Updated NSIS packaging to use 64-bit Program Files, 64-bit registry view,
  application icons, stable shortcut icons, and no finish-page auto-run.
- Reworked launcher and resource path handling to avoid machine-local paths.
- Applied Ruff formatting and safe lint cleanups across the source tree.
- Replaced the legacy icon assets with transparent-background pyFastPlot icon
  PNG/ICO files.

### Removed
- Removed the architecture document in favor of user manuals.
- Removed the standalone icon-conversion utility from scripts.

## [1.1.0] - 2026-05-17
### Added
- Text Import Wizard for advanced clipboard data pasting.
- Log Scale options for X and Y axes in the Global settings tab.
- Error logging system tracking to `~/.pyfastplot/pyfastplot.log`.

### Changed
- Project renamed from **Data Visualizer** to **pyFastPlot**.
- Updated window title to dynamically reflect the current version.
- Centralized version management in `src/pyfastplot/__init__.py`.
- **UI Architecture:** Extracted all UI magic strings and hardcoded dimensions into `constants.py`.
- **MVP Refactoring:** Decoupled `matplotlib` logic from `MainPresenter`, ensuring the View handles all plotting rendering commands internally.
- **Performance:** Debounced the `resizeEvent` with a `QTimer` to prevent circular layout loops between Qt and Matplotlib's `tight_layout()`.
- **UI Layout:** Reduced the default width of the Data Table panel and reorganized the action buttons using a grid layout to maximize spreadsheet space.

## [1.0.0] - 2026-05-09
### Added
- Initial release under the name **Data Visualizer**.
- Basic CSV loading and clipboard support.
- Interactive plotting with Matplotlib.
- Table-based data management and header editing.
