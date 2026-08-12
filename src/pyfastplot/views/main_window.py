"""Main window hosting pyFastPlot's extensible Figure workspace."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QAction, QActionGroup, QColor, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .. import __version__
from .components.figure_tab import FigureTab

if TYPE_CHECKING:
    from ..presenters.figure_presenter import FigurePresenter


class MainWindow(QMainWindow):
    """Host independent plotting workspaces in an extensible tab container."""

    figure_presenter: FigurePresenter | None

    def __init__(self) -> None:
        super().__init__()
        self.figure_presenter = None
        self.theme_name = "Light"
        self.setAcceptDrops(True)
        self.setWindowTitle(f"pyFastPlot {__version__}")
        self.resize(860, 550)
        self.setMinimumSize(860, 550)
        self._build_ui()

    def _build_ui(self) -> None:
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        self.action_new_import_format = file_menu.addAction("Add Text Import Format...")
        self.action_manage_import_formats = file_menu.addAction(
            "Manage Text Import Formats..."
        )
        options_menu = menubar.addMenu("Options")
        theme_menu = options_menu.addMenu("Theme")
        self.theme_group = QActionGroup(self)
        self.action_theme_light = theme_menu.addAction("Light")
        self.action_theme_light.setCheckable(True)
        self.theme_group.addAction(self.action_theme_light)
        self.action_theme_dark = theme_menu.addAction("Dark")
        self.action_theme_dark.setCheckable(True)
        self.theme_group.addAction(self.action_theme_dark)
        self.theme_group.triggered.connect(self._on_theme_changed)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(5, 5, 5, 5)
        self.main_tabs = QTabWidget()
        self.figure_tab = FigureTab()
        self.main_tabs.addTab(self.figure_tab, "Figure")
        self.main_tabs.tabBar().setMinimumHeight(32)
        layout.addWidget(self.main_tabs)
        self.setCentralWidget(container)
        initial_theme = self._initial_theme_name()
        self._set_theme_action_checked(initial_theme)
        self._apply_theme(initial_theme)

    def _on_theme_changed(self, action: QAction) -> None:
        self._apply_theme(action.text())

    def _initial_theme_name(self) -> str:
        """Use the same Windows default-theme detection as pyWavePlot."""
        try:
            import winreg

            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            ) as key:
                light_value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return "Light" if int(light_value) else "Dark"
        except (OSError, ValueError, TypeError):
            return "Light"

    def _set_theme_action_checked(self, theme_name: str) -> None:
        self.action_theme_light.setChecked(theme_name == "Light")
        self.action_theme_dark.setChecked(theme_name == "Dark")

    def _apply_theme(self, theme_name: str) -> None:
        """Apply pyWavePlot's reversible light and dark widget palettes."""
        self.theme_name = theme_name
        app = QApplication.instance()
        if not isinstance(app, QApplication):
            return
        app.setStyle("Fusion")
        is_dark = theme_name == "Dark"
        palette = QPalette()
        if is_dark:
            colors = {
                "window": QColor(38, 38, 38),
                "window_text": QColor(235, 235, 235),
                "base": QColor(28, 28, 28),
                "alternate": QColor(45, 45, 45),
                "button": QColor(48, 48, 48),
                "button_text": QColor(235, 235, 235),
                "text": QColor(235, 235, 235),
                "highlight": QColor(76, 124, 180),
                "tooltip_base": QColor(45, 45, 45),
                "tooltip_text": QColor(235, 235, 235),
            }
            foreground, popup, border, hover, input_background = (
                "#eeeeee",
                "#2d2d2d",
                "#666666",
                "#3a3a3a",
                "#242424",
            )
        else:
            colors = {
                "window": QColor(240, 240, 240),
                "window_text": QColor(0, 0, 0),
                "base": QColor(255, 255, 255),
                "alternate": QColor(245, 245, 245),
                "button": QColor(240, 240, 240),
                "button_text": QColor(0, 0, 0),
                "text": QColor(0, 0, 0),
                "highlight": QColor(0, 120, 215),
                "tooltip_base": QColor(255, 255, 220),
                "tooltip_text": QColor(0, 0, 0),
            }
            foreground, popup, border, hover, input_background = (
                "#202020",
                "#ffffff",
                "#a8a8a8",
                "#e0e0e0",
                "#ffffff",
            )
        palette.setColor(QPalette.ColorRole.Window, colors["window"])
        palette.setColor(QPalette.ColorRole.WindowText, colors["window_text"])
        palette.setColor(QPalette.ColorRole.Base, colors["base"])
        palette.setColor(QPalette.ColorRole.AlternateBase, colors["alternate"])
        palette.setColor(QPalette.ColorRole.Button, colors["button"])
        palette.setColor(QPalette.ColorRole.ButtonText, colors["button_text"])
        palette.setColor(QPalette.ColorRole.Text, colors["text"])
        palette.setColor(QPalette.ColorRole.Highlight, colors["highlight"])
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.ToolTipBase, colors["tooltip_base"])
        palette.setColor(QPalette.ColorRole.ToolTipText, colors["tooltip_text"])
        app.setPalette(palette)
        app.setStyleSheet(
            f"""
            QToolTip {{
                color: {foreground}; background-color: {popup};
                border: 1px solid {border};
            }}
            QMenu {{
                background-color: {popup}; color: {foreground};
                border: 1px solid {border};
            }}
            QMenu::item:selected {{ background-color: {hover}; }}
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit,
            QPlainTextEdit, QTableView, QTreeView, QListView {{
                background-color: {input_background}; color: {foreground};
                selection-background-color: #0078d7; selection-color: #ffffff;
            }}
            QHeaderView::section {{
                background-color: {popup}; color: {foreground};
                border: 1px solid {border}; padding: 3px;
            }}
            QHeaderView::section:checked, QHeaderView::section:selected {{
                background-color: #0078d7; color: #ffffff;
            }}
            """
        )
        self.menuBar().setStyleSheet(
            f"""
            QMenuBar {{ padding: 1px; margin: 0; border-bottom: 1px solid {border}; }}
            QMenuBar::item {{ padding: 2px 10px; background: transparent; }}
            QMenuBar::item:selected {{ background: {hover}; }}
            """
        )

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        if not event.mimeData().hasUrls():
            event.ignore()
            return
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path:
                self.figure_tab.file_dropped.emit(file_path)
        event.acceptProposedAction()
