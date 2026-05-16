# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
