import os
import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from .models.data_model import DataModel
from .presenters.main_presenter import MainPresenter
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

    model = DataModel()
    view = MainWindow()
    presenter = MainPresenter(view, model)
    view.presenter = presenter

    view.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
