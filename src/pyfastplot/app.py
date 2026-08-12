"""Application bootstrap for pyFastPlot."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from .models.data_model import DataModel
from .models.figure_model import FigureModel
from .presenters.figure_presenter import FigurePresenter
from .views.main_window import MainWindow


def resource_path(relative_path: str | Path) -> Path:
    """Return a resource path for source-tree and bundled execution."""
    if getattr(sys, "frozen", False) or "NUITKA_PYTHON_EXE" in os.environ:
        base_path = Path(sys.executable).resolve().parent
    else:
        base_path = Path(__file__).resolve().parents[2]
    return base_path / relative_path


def main() -> None:
    """Run the pyFastPlot desktop application."""
    app = QApplication(sys.argv)
    icon_path = resource_path(Path("assets") / "pyfastplot_icon.png")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    view = MainWindow()
    presenter = FigurePresenter(
        view.figure_tab,
        FigureModel(),
        DataModel(),
    )
    view.figure_presenter = presenter
    view.action_new_import_format.triggered.connect(
        presenter.on_new_import_format_clicked
    )
    view.action_manage_import_formats.triggered.connect(
        presenter.on_manage_import_formats_clicked
    )
    view.show()
    sys.exit(app.exec())
