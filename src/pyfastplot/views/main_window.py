from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from .. import __version__
from .components.file_list import FileListWidget
from .components.plot_canvas import AspectRatioWidget, MplCanvas
from .components.plot_options import PlotOptionsWidget
from .components.table import TableWidget


class MainWindow(QMainWindow):
    """
    MainWindow orchestrates the main UI layout and acts as the View in the MVP pattern.
    It assembles UI components and exposes their signals for the Presenter.
    """

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setupUI()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith(".csv"):
                    self.table_list_widget.file_dropped_signal.emit(file_path)

    def setupUI(self):
        self.setWindowTitle(f"pyFastPlot {__version__}")
        self.resize(1000, 800)
        self.setMinimumSize(800, 600)

        main_splitter = QSplitter(Qt.Orientation.Vertical)
        main_splitter.setChildrenCollapsible(False)

        top_widget = self._create_top_layout()
        main_splitter.addWidget(top_widget)

        bottom_widget = self._create_bottom_layout()
        main_splitter.addWidget(bottom_widget)

        # Give the top (graph) more initial space than the bottom (tables)
        main_splitter.setSizes([500, 300])

        # Wrap the main splitter in a container to provide outer margins
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(5, 5, 5, 5)
        container_layout.addWidget(main_splitter)

        self.setCentralWidget(container)

    def _create_top_layout(self):
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        graph_widget = QWidget()
        graph_layout = QVBoxLayout(graph_widget)
        graph_layout.setContentsMargins(0, 0, 0, 0)

        self.sc = MplCanvas(self, width=5, height=4, dpi=100)
        self.toolbar = NavigationToolbar2QT(self.sc, self)

        self.aspect_wrapper = AspectRatioWidget(self.sc, 5, 4)
        # Prevent the graph from disappearing if scaled too small
        self.aspect_wrapper.setMinimumSize(300, 200)

        graph_layout.addWidget(self.toolbar)
        graph_layout.addWidget(self.aspect_wrapper)

        option_widget = QWidget()
        option_layout = QVBoxLayout(option_widget)
        option_layout.setContentsMargins(0, 0, 0, 0)

        self.plot_options = PlotOptionsWidget()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.plot_options)
        scroll.setMinimumWidth(350)

        button_layout = QHBoxLayout()
        self.plot_button = QPushButton("Update Plot")
        self.plot_button.setMinimumHeight(40)
        self.copy_button = QPushButton("Copy to Clipboard")
        self.copy_button.setMinimumHeight(40)
        self.save_button = QPushButton("Save Plot")
        self.save_button.setMinimumHeight(40)

        button_layout.addWidget(self.plot_button)
        button_layout.addWidget(self.copy_button)
        button_layout.addWidget(self.save_button)

        option_layout.addWidget(scroll)
        option_layout.addLayout(button_layout)

        splitter.addWidget(graph_widget)
        splitter.addWidget(option_widget)

        # Set initial horizontal sizes so the options panel uses remaining space.
        splitter.setSizes([600, 400])

        return splitter

    def _create_bottom_layout(self):
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # 1. File Selection
        file_widget = QWidget()
        file_layout = QVBoxLayout(file_widget)
        file_layout.setContentsMargins(0, 0, 0, 0)

        title_label = QLabel("Data Table")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        file_layout.addWidget(title_label)

        from PySide6.QtWidgets import QGridLayout

        button_grid = QGridLayout()
        self.add_input_btn = QPushButton("Generate")
        self.clear_table_btn = QPushButton("Clear")
        self.remove_all_btn = QPushButton("Remove All")

        button_grid.addWidget(self.add_input_btn, 0, 0, 1, 2)
        button_grid.addWidget(self.clear_table_btn, 1, 0)
        button_grid.addWidget(self.remove_all_btn, 1, 1)

        file_layout.addLayout(button_grid)

        self.table_list_widget = FileListWidget()
        self.table_list_widget.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        file_layout.addWidget(self.table_list_widget)

        # 2. Table Widget
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        table_layout.setContentsMargins(0, 0, 0, 0)
        self.tableWidget = TableWidget()
        table_layout.addWidget(self.tableWidget)

        # 3. Data Selection Options
        data_widget = QWidget()
        data_layout = QVBoxLayout(data_widget)
        data_layout.setContentsMargins(0, 0, 0, 0)

        sel_title = QLabel("Data Selection")
        sel_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        data_layout.addWidget(sel_title)

        x_layout = QHBoxLayout()
        x_layout.addWidget(QLabel("X:"))
        self.combo_x = QComboBox()
        x_layout.addWidget(self.combo_x)
        data_layout.addLayout(x_layout)

        y_layout = QHBoxLayout()
        y_layout.addWidget(QLabel("Y:"))
        self.combo_y = QComboBox()
        y_layout.addWidget(self.combo_y)
        data_layout.addLayout(y_layout)

        label_layout = QHBoxLayout()
        label_layout.addWidget(QLabel("Label:"))
        self.line_label_input = QLineEdit()
        self.line_label_input.setPlaceholderText("Custom line label")
        label_layout.addWidget(self.line_label_input)
        data_layout.addLayout(label_layout)

        self.new_plot_btn = QPushButton("Plot New")
        self.new_plot_btn.setMinimumHeight(30)
        data_layout.addWidget(self.new_plot_btn)

        self.overlay_plot_btn = QPushButton("Overlay Plot")
        self.overlay_plot_btn.setMinimumHeight(30)
        data_layout.addWidget(self.overlay_plot_btn)

        self.warning_label = QLabel("")
        self.warning_label.setStyleSheet(
            "color: red; font-size: 12px; margin-top: 5px;"
        )
        self.warning_label.setWordWrap(True)
        data_layout.addWidget(self.warning_label)

        data_layout.addStretch()

        splitter.addWidget(file_widget)
        splitter.addWidget(table_widget)
        splitter.addWidget(data_widget)

        # Balance the Data Table, Spreadsheet, and Data Selection panels.
        # Giving slightly less space to the right panel (Data Selection).
        splitter.setSizes([100, 720, 180])

        return splitter

    def update_selection_ui(self, labels):
        curr_x = self.combo_x.currentText()
        curr_y = self.combo_y.currentText()

        self.combo_x.blockSignals(True)
        self.combo_y.blockSignals(True)

        self.combo_x.clear()
        self.combo_y.clear()

        if labels:
            self.combo_x.addItem("Index")
            for label in labels:
                self.combo_x.addItem(label)
                self.combo_y.addItem(label)

            # Restore X
            if curr_x:
                idx = self.combo_x.findText(curr_x)
                if idx >= 0:
                    self.combo_x.setCurrentIndex(idx)
                else:
                    self.combo_x.setCurrentIndex(1 if len(labels) >= 1 else 0)
            elif len(labels) >= 1:
                self.combo_x.setCurrentIndex(1)

            # Restore Y
            if curr_y:
                idx = self.combo_y.findText(curr_y)
                if idx >= 0:
                    self.combo_y.setCurrentIndex(idx)
                else:
                    self.combo_y.setCurrentIndex(1 if len(labels) >= 2 else 0)
            elif len(labels) >= 1:
                if len(labels) >= 2:
                    self.combo_y.setCurrentIndex(1)
                else:
                    self.combo_y.setCurrentIndex(0)

        self.combo_x.blockSignals(False)
        self.combo_y.blockSignals(False)

    def restore_selections(self, x_sel, y_sels):
        self.combo_x.blockSignals(True)
        idx = self.combo_x.findText(x_sel)
        if idx >= 0:
            self.combo_x.setCurrentIndex(idx)
        self.combo_x.blockSignals(False)

        self.combo_y.blockSignals(True)
        if y_sels and len(y_sels) > 0:
            y_sel = y_sels[0]
            idx_y = self.combo_y.findText(y_sel)
            if idx_y >= 0:
                self.combo_y.setCurrentIndex(idx_y)
        self.combo_y.blockSignals(False)

    def draw_plot(self, x_plot, y_plot, label_text, **kwargs):
        self.sc.axes.plot(x_plot, y_plot, label=label_text, **kwargs)

    def clear_plot(self):
        self.sc.axes.clear()
        self.sc.init_annot()

    def apply_global_plot_settings(self, settings):
        import platform

        import matplotlib as mpl

        # Apply Font Settings
        has_korean = settings.get("has_korean", False)
        font_selection = settings.get("font_selection", "Auto")
        is_mac = platform.system() == "Darwin"
        kor_font = "AppleGothic" if is_mac else "Malgun Gothic"
        actual_font = ""

        if font_selection == "Auto":
            if has_korean:
                mpl.rcParams["font.family"] = kor_font
                actual_font = f"{kor_font} (Auto-detected Korean)"
            else:
                mpl.rcParams["font.family"] = "sans-serif"
                actual_font = "DejaVu Sans (Default)"
        elif font_selection == "DejaVu Sans (Default)":
            mpl.rcParams["font.family"] = "sans-serif"
            actual_font = "DejaVu Sans (Default)"
        elif font_selection == "Korean (System Default)":
            mpl.rcParams["font.family"] = kor_font
            actual_font = kor_font
        else:
            mpl.rcParams["font.family"] = font_selection
            actual_font = font_selection

        mpl.rcParams["axes.unicode_minus"] = False

        title = settings.get("title", "")
        if title:
            self.sc.axes.set_title(title, fontsize=settings.get("title_size", 12))

        self.sc.axes.set_xlabel(
            settings.get("xlabel", ""), fontsize=settings.get("label_size", 10)
        )
        self.sc.axes.set_ylabel(
            settings.get("ylabel", ""), fontsize=settings.get("label_size", 10)
        )

        self.sc.axes.tick_params(
            axis="both", which="major", labelsize=settings.get("tick_size", 10)
        )

        if settings.get("xmin") or settings.get("xmax"):
            left = float(settings["xmin"]) if settings["xmin"] else None
            right = float(settings["xmax"]) if settings["xmax"] else None
            self.sc.axes.set_xlim(left=left, right=right)

        if settings.get("ymin") or settings.get("ymax"):
            bottom = float(settings["ymin"]) if settings["ymin"] else None
            top = float(settings["ymax"]) if settings["ymax"] else None
            self.sc.axes.set_ylim(bottom=bottom, top=top)

        self.sc.axes.set_xscale("log" if settings.get("x_log") else "linear")
        self.sc.axes.set_yscale("log" if settings.get("y_log") else "linear")

        if settings.get("show_legend"):
            self.sc.axes.legend(
                fontsize=settings.get("legend_size", 10),
                loc=settings.get("legend_loc", "best"),
                framealpha=1.0,
                fancybox=False,
                frameon=True,
                edgecolor="black",
            )
        else:
            leg = self.sc.axes.get_legend()
            if leg:
                leg.remove()

        return actual_font

    def update_plot(self):
        self.sc.axes.grid(True)
        self.sc.draw()
