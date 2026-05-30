# Packaging pyFastPlot

This folder contains the Windows packaging files for pyFastPlot.

## Prerequisites

- A Windows Python environment with project build dependencies:

```powershell
python -m pip install -e ".[build]"
```

- NSIS installed. The default installer path is:

```text
C:\Program Files (x86)\NSIS\makensis.exe
```

## Build The Nuitka Standalone Folder

From the project root:

```powershell
if (Test-Path -LiteralPath "build") {
    Remove-Item -LiteralPath "build" -Recurse -Force
}

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

This creates:

```text
build\main.dist\pyFastPlot.exe
```

`PYTHONPATH=src` lets Nuitka find the package under `src/pyfastplot`.

## Build The NSIS Installer

After the Nuitka build exists:

```powershell
& "C:\Program Files (x86)\NSIS\makensis.exe" packaging\nsis\script.nsi
```

The installer output is written to:

```text
packaging\nsis\pyFastPlot_v1.1.0_Win64_Setup.exe
```

## Notes

- The NSIS script installs every file under `build\main.dist`.
- The NSIS script requires 64-bit Windows, installs to `Program Files`, and uses
  the 64-bit registry view.
- The installer writes to `Program Files` and uses HKLM uninstall registry keys,
  so it requires administrator permission.
- The finish page does not auto-run pyFastPlot. This avoids launching the app
  elevated from the installer, which can break drag-and-drop from Explorer.
- Shortcuts use an installed copy of `pyfastplot_icon.ico` rather than relying
  only on the executable icon resource.
- Generated installer `.exe` files are ignored by Git via `.gitignore`.
