# pyFastPlot

pyFastPlot is a lightweight PySide6 desktop application for quickly plotting
CSV or spreadsheet-style tabular data with Matplotlib. It focuses on fast data
loading, editable tables, practical plot styling, and one-click export for
reports, papers, and presentations.

## Project Layout

```text
.
|-- main.py
|-- assets/
|-- docs/
|-- packaging/
|-- src/
|   `-- pyfastplot/
|       |-- app.py
|       |-- constants.py
|       |-- models/
|       |-- presenters/
|       `-- views/
`-- tests/
```

The application follows an MVP-style structure:

- `models` stores table data, CSV parsing, undo/redo state, and plotted series.
- `views` builds Qt widgets, table views, option panels, and Matplotlib canvas
  rendering.
- `presenters` connects Qt signals to model updates and plot refreshes.
- `main.py` is the launcher; `src/pyfastplot/app.py` is the package entry point.

## Features

- Drag-and-drop CSV loading.
- Editable in-memory tables.
- Spreadsheet paste with `Ctrl+V`.
- Text Import Wizard with `Ctrl+Shift+V`.
- Column rename, row/column deletion, undo/redo, and row-to-header promotion.
- Index or selected-column X axis.
- Plot replacement and overlay plotting.
- Line color, style, width, marker, fill, and label controls.
- Figure size, DPI, font, axis labels, log-scale, axis-limit, and legend options.
- Matplotlib toolbar support.
- Copy plot image to clipboard.
- Save plot as PNG or SVG.
- Application logging under `%USERPROFILE%\.pyfastplot\pyfastplot.log`.

## Documentation

- [English manual](docs/user_manual_en.md)
- [Korean manual](docs/user_manual_ko.md)
- [Changelog](CHANGELOG.md)

## Requirements

- Python 3.11 or newer
- PySide6
- Matplotlib
- NumPy

Install runtime dependencies:

```powershell
python -m pip install -r requirements.txt
```

For development, install the package in editable mode with optional tooling:

```powershell
python -m pip install -e ".[dev]"
```

## Run

```powershell
python main.py
```

Logs are written to:

```text
%USERPROFILE%\.pyfastplot\pyfastplot.log
```

## Test

```powershell
python -m pytest
```

## Format And Lint

```powershell
ruff format src tests
ruff check src tests
```

## Windows Build

Install build dependencies:

```powershell
python -m pip install -e ".[build]"
```

Build a standalone Nuitka distribution:

```powershell
$env:PYTHONPATH = "src"
python -m nuitka `
    --standalone `
    --enable-plugins=pyside6,matplotlib,anti-bloat `
    --noinclude-qt-plugins=webengine,pdf,network `
    --include-data-dir=assets=assets `
    --windows-console-mode=disable `
    --windows-icon-from-ico=assets\pyfastplot_icon.ico `
    --output-dir=build `
    --output-filename=pyFastPlot `
    main.py
```

The executable is generated at:

```text
build\main.dist\pyFastPlot.exe
```

Build the NSIS setup installer after the Nuitka build:

```powershell
& "C:\Program Files (x86)\NSIS\makensis.exe" packaging\nsis\script.nsi
```

The installer output is:

```text
packaging\nsis\pyFastPlot_v1.1.0_Win64_Setup.exe
```

See [packaging/README.md](packaging/README.md) for packaging details.

## Notes

- Windows packaging uses `assets\pyfastplot_icon.ico` for the executable,
  installer, uninstaller, and shortcuts.
- Build outputs, installer executables, Python caches, logs, and editor
  settings are ignored by Git.
