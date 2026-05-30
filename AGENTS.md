# Coding Rules

- Use numpy style docstrings for public functions and classes.
- Use type hints for new or modified Python code.
- Prefer pathlib over os.path for filesystem paths.
- Use Ruff formatting.
- Keep GUI behavior changes deliberate and scoped.
- Avoid unnecessary classes and broad rewrites.
- Keep functions focused and preferably under 80 lines.

# Project Notes

- This is a PySide6/Matplotlib desktop plotting application organized around an
  MVP-style package layout under `src/pyfastplot`.
- `models` owns table data, CSV parsing, undo/redo state, and selected plot
  series state.
- `views` owns Qt widgets, table views, Matplotlib canvas rendering, and option
  panels.
- `presenters` connects Qt signals to model updates and plot refreshes.
- Treat `main.py` as the launcher/bootstrap file. The package entry point lives
  in `src/pyfastplot/app.py`.
- Avoid introducing another GUI or plotting framework unless explicitly asked.
- Do not commit build outputs, installer files, Python caches, editor settings,
  or machine-local paths.
