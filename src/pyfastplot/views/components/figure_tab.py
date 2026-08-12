"""Independent Matplotlib-based workspace for publication-ready figures."""

from __future__ import annotations

import numpy as np
from matplotlib.backends.backend_qt import NavigationToolbar2QT
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.text import Annotation
from PySide6.QtCore import QSignalBlocker, Qt, QTimer, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)

from .file_list import FileListWidget

LineOptions = dict[str, str | float]
SeriesKey = tuple[str, str]
SERIES_LABEL_ROLE = Qt.ItemDataRole.UserRole + 20


class LineOptionsButton(QToolButton):
    """Compact per-line stroke editor that keeps the table width stable."""

    options_changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.style_combo = QComboBox()
        self.style_combo.addItems(["-", "--", "-.", ":", "None"])
        self.width_input = QDoubleSpinBox()
        self.width_input.setRange(0.1, 10.0)
        self.width_input.setSingleStep(0.1)
        self.width_input.setValue(1.5)
        self._build_menu()
        self.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.style_combo.currentTextChanged.connect(self._emit_options_changed)
        self.width_input.valueChanged.connect(self._emit_options_changed)
        self._update_button_text()

    def _build_menu(self) -> None:
        menu = QMenu(self)
        page = QWidget(menu)
        layout = QFormLayout(page)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addRow("Style", self.style_combo)
        layout.addRow("Width", self.width_input)
        action = QWidgetAction(menu)
        action.setDefaultWidget(page)
        menu.addAction(action)
        self.setMenu(menu)

    def line_style(self) -> str:
        """Return the Matplotlib line style."""
        return self.style_combo.currentText()

    def line_width(self) -> float:
        """Return the Matplotlib line width in points."""
        return self.width_input.value()

    def set_options(self, style: str, width: float) -> None:
        """Restore saved line options without changing their meaning."""
        self.style_combo.setCurrentText(style)
        self.width_input.setValue(width)
        self._update_button_text()

    def _emit_options_changed(self) -> None:
        self._update_button_text()
        self.options_changed.emit()

    def _update_button_text(self) -> None:
        style = self.line_style()
        self.setText("Line" if style == "-" else f"{style} {self.line_width():g}")


class MarkerOptionsButton(QToolButton):
    """Compact per-line marker editor that keeps the table width stable."""

    options_changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.shape_combo = QComboBox()
        self.shape_combo.addItems(["None", "o", "s", "^", "x"])
        self.size_input = QDoubleSpinBox()
        self.size_input.setRange(1.0, 40.0)
        self.size_input.setSingleStep(0.5)
        self.size_input.setValue(6.0)
        self.fillstyle_combo = QComboBox()
        self.fillstyle_combo.addItems(
            ["full", "none", "left", "right", "bottom", "top"]
        )
        self._build_menu()
        self.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        for widget in (self.shape_combo, self.fillstyle_combo):
            widget.currentTextChanged.connect(self._emit_options_changed)
        self.size_input.valueChanged.connect(self._emit_options_changed)
        self._update_button_text()

    def _build_menu(self) -> None:
        menu = QMenu(self)
        page = QWidget(menu)
        layout = QFormLayout(page)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addRow("Shape", self.shape_combo)
        layout.addRow("Size", self.size_input)
        layout.addRow("Fill", self.fillstyle_combo)
        action = QWidgetAction(menu)
        action.setDefaultWidget(page)
        menu.addAction(action)
        self.setMenu(menu)

    def marker(self) -> str:
        """Return the Matplotlib marker symbol."""
        return self.shape_combo.currentText()

    def marker_size(self) -> float:
        """Return the Matplotlib marker size in points."""
        return self.size_input.value()

    def fillstyle(self) -> str:
        """Return the Matplotlib marker fill style."""
        return self.fillstyle_combo.currentText()

    def set_options(self, marker: str, size: float, fillstyle: str) -> None:
        """Restore saved marker options without changing their meaning."""
        self.shape_combo.setCurrentText(marker)
        self.size_input.setValue(size)
        self.fillstyle_combo.setCurrentText(fillstyle)
        self._update_button_text()

    def _emit_options_changed(self) -> None:
        self._update_button_text()
        self.options_changed.emit()

    def _update_button_text(self) -> None:
        marker = self.marker()
        self.setText("Marker" if marker == "None" else f"{marker} ...")


class FigureTab(QWidget):
    """View for separately styling and exporting post-processed data."""

    plot_requested = Signal()
    copy_requested = Signal()
    save_requested = Signal()
    reset_requested = Signal()
    file_dropped = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._building_line_table = False
        self._build_ui()

    def _build_ui(self) -> None:
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        data_panel = self._build_data_panel()
        plot_panel = self._build_plot_panel()
        settings_panel = self._build_settings_panel()
        self.splitter.addWidget(data_panel)
        self.splitter.addWidget(plot_panel)
        self.splitter.addWidget(settings_panel)
        self.splitter.setSizes([205, 790, 190])
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setStretchFactor(2, 0)
        layout = QVBoxLayout(self)
        # The shared tab container already supplies the outer five-pixel margin.
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.splitter)

    def _build_data_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        data_group = QGroupBox("Data")
        self._style_panel_group(data_group)
        data_layout = QVBoxLayout(data_group)
        filter_layout = QHBoxLayout()
        self.data_filter = QLineEdit()
        self.data_filter.setPlaceholderText("Find...")
        self.load_file_button = QPushButton("Load File")
        filter_layout.addWidget(self.data_filter, 1)
        filter_layout.addWidget(self.load_file_button)
        self.dataset_tree = FileListWidget()
        self.dataset_tree.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.data_filter.textChanged.connect(self.dataset_tree.set_filter_text)
        data_layout.addLayout(filter_layout)
        data_layout.addWidget(self.dataset_tree)
        layout.addWidget(data_group, 1)
        panel.setMinimumWidth(215)
        panel.setMaximumWidth(320)
        return panel

    def _build_plot_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        self.figure = Figure(constrained_layout=True)
        self.axes = self.figure.add_subplot(111)
        self.preview = ScaledFigurePreview()
        self.preview.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.canvas_scroll = QScrollArea()
        self.canvas_scroll.setWidget(self.canvas)
        self.canvas_scroll.setWidgetResizable(False)
        self.canvas_scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.canvas.mpl_connect("motion_notify_event", self._show_canvas_hover)
        self._canvas_annotation = None
        self.display_stack = QStackedWidget()
        self.display_stack.addWidget(self.preview)
        self.display_stack.addWidget(self.canvas_scroll)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self.toolbar.hide()
        buttons = QHBoxLayout()
        copy_button = QPushButton("Copy image")
        save_button = QPushButton("Save PNG / SVG")
        copy_button.clicked.connect(self.copy_requested)
        save_button.clicked.connect(self.save_requested)
        self.display_mode = QComboBox()
        self.display_mode.addItems(
            ["Preview (scaled)", "Canvas (actual size)", "Canvas (fit panel)"]
        )
        self.display_mode.currentIndexChanged.connect(self._update_display_mode)
        buttons.addWidget(copy_button)
        buttons.addWidget(save_button)
        buttons.addWidget(self.display_mode)
        buttons.addStretch()
        layout.addLayout(buttons)
        layout.addWidget(self.toolbar)
        self.plot_splitter = QSplitter(Qt.Orientation.Vertical)
        self.plot_splitter.setChildrenCollapsible(False)
        self.display_stack.setMinimumHeight(100)
        line_settings = self._build_line_settings()
        line_settings.setMinimumHeight(70)
        self.plot_splitter.addWidget(self.display_stack)
        self.plot_splitter.addWidget(line_settings)
        self.plot_splitter.setSizes([520, 180])
        self.plot_splitter.setStretchFactor(0, 1)
        self.plot_splitter.setStretchFactor(1, 0)
        self.plot_splitter.setHandleWidth(8)
        layout.addWidget(self.plot_splitter, 1)
        panel.setMinimumWidth(380)
        return panel

    def set_preview_image(self, pixmap: QPixmap) -> None:
        """Show an exported-size Figure image scaled only for on-screen viewing."""
        self.preview.set_source_pixmap(pixmap)

    def display_mode_name(self) -> str:
        """Return the requested Figure display behavior."""
        return self.display_mode.currentText()

    def update_canvas_display(self) -> None:
        """Size the actual Matplotlib canvas for the selected display mode."""
        if self.display_mode_name() == "Canvas (actual size)":
            width = int(self.width_input.value() * self.dpi_input.value())
            height = int(self.height_input.value() * self.dpi_input.value())
            self.canvas.setFixedSize(width, height)
            self.canvas_scroll.setWidgetResizable(False)
            return
        self.canvas.setMinimumSize(1, 1)
        self.canvas.setMaximumSize(16_777_215, 16_777_215)
        self.canvas.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.canvas_scroll.setWidgetResizable(True)
        self.canvas.updateGeometry()
        QTimer.singleShot(0, self._fit_canvas_to_viewport)

    def _update_display_mode(self) -> None:
        preview_mode = self.display_mode_name() == "Preview (scaled)"
        self.display_stack.setCurrentIndex(0 if preview_mode else 1)
        self.toolbar.setVisible(not preview_mode)
        self.update_canvas_display()
        if preview_mode:
            self.plot_requested.emit()

    def _fit_canvas_to_viewport(self) -> None:
        """Restore a fit-mode canvas after an export redraw changes its size."""
        if self.display_mode_name() != "Canvas (fit panel)":
            return
        viewport_size = self.canvas_scroll.viewport().size()
        if not viewport_size.isEmpty():
            self.canvas.resize(viewport_size)

    def prepare_canvas_hover(self) -> None:
        """Create the hover annotation for the current Canvas plot lines."""
        self._canvas_annotation = self.axes.annotate(
            "",
            xy=(0, 0),
            xytext=(12, 12),
            textcoords="offset points",
            bbox={"boxstyle": "round,pad=0.4", "fc": "lightyellow", "alpha": 0.9},
            arrowprops={"arrowstyle": "->"},
        )
        # A hover label must float over the axes, not participate in
        # constrained-layout calculations that would resize the plotted area.
        self._canvas_annotation.set_in_layout(False)
        self._canvas_annotation.set_visible(False)

    def _show_canvas_hover(self, event) -> None:
        annotation = self._canvas_annotation
        if event.inaxes != self.axes or annotation is None:
            self._hide_canvas_hover()
            return
        for line in self.axes.get_lines():
            contains, details = line.contains(event)
            if not contains:
                continue
            index = details["ind"][0]
            x_data, y_data = line.get_data()
            x_values = np.asarray(x_data, dtype=float)
            y_values = np.asarray(y_data, dtype=float)
            x_value = float(x_values[index])
            y_value = float(y_values[index])
            annotation.xy = (x_value, y_value)
            self._position_hover_label(annotation, x_value, y_value)
            annotation.set_text(
                f"{line.get_label()}\nX: {x_value:.6g}\nY: {y_value:.6g}"
            )
            annotation.set_visible(True)
            self.canvas.draw_idle()
            return
        self._hide_canvas_hover()

    def _position_hover_label(
        self, annotation: Annotation, x_value: float, y_value: float
    ) -> None:
        """Keep the Canvas hover label inside the visible axes bounds."""
        point_x, point_y = self.axes.transData.transform((x_value, y_value))
        bounds = self.axes.get_window_extent()
        place_left = point_x > bounds.x1 - 130
        place_below = point_y > bounds.y1 - 70
        annotation.set_position(
            ((-12 if place_left else 12), (-12 if place_below else 12))
        )
        annotation.set_horizontalalignment("right" if place_left else "left")
        annotation.set_verticalalignment("top" if place_below else "bottom")

    def _hide_canvas_hover(self) -> None:
        if (
            self._canvas_annotation is not None
            and self._canvas_annotation.get_visible()
        ):
            self._canvas_annotation.set_visible(False)
            self.canvas.draw_idle()

    def _build_settings_panel(self) -> QWidget:
        panel = QGroupBox("Figure Settings")
        panel.setStyleSheet(
            "QGroupBox { margin-top: 12px; padding: 2px; }"
            "QGroupBox::title {"
            "subcontrol-origin: margin; left: 6px; padding: 0 3px;"
            "}"
        )
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(2, 3, 2, 3)
        layout.addWidget(self._build_global_settings())
        panel.setMinimumWidth(175)
        panel.setMaximumWidth(235)
        return panel

    def _style_panel_group(self, group: QGroupBox) -> None:
        """Match the title spacing used by Post-processing side panels."""
        group.setStyleSheet(
            "QGroupBox { margin-top: 12px; padding: 6px; }"
            "QGroupBox::title {"
            "subcontrol-origin: margin; left: 10px; padding: 0 4px;"
            "}"
        )

    def _build_global_settings(self) -> QWidget:
        page = QWidget()
        layout = QFormLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(3)
        layout.setVerticalSpacing(3)
        self.title_input = QLineEdit()
        self.xlabel_input = QLineEdit()
        self.ylabel_input = QLineEdit()
        self.width_input = QDoubleSpinBox()
        self.height_input = QDoubleSpinBox()
        self.dpi_input = QSpinBox()
        self.font_size_input = QSpinBox()
        for widget, value in ((self.width_input, 5.0), (self.height_input, 4.0)):
            widget.setRange(1.0, 30.0)
            widget.setValue(value)
        self.dpi_input.setRange(72, 1200)
        self.dpi_input.setValue(100)
        self.font_size_input.setRange(6, 48)
        self.font_size_input.setValue(10)
        self.legend_check = QCheckBox()
        self.x_log_check = QCheckBox()
        self.y_log_check = QCheckBox()
        self.legend_location = QComboBox()
        self.legend_location.addItems(
            ["best", "upper right", "upper left", "lower right", "lower left"]
        )
        self.x_min = QLineEdit()
        self.x_max = QLineEdit()
        self.y_min = QLineEdit()
        self.y_max = QLineEdit()
        layout.addRow("Title", self.title_input)
        layout.addRow("X label", self.xlabel_input)
        layout.addRow("Y label", self.ylabel_input)
        layout.addRow("Width (in)", self.width_input)
        layout.addRow("Height (in)", self.height_input)
        layout.addRow("DPI", self.dpi_input)
        layout.addRow("Font size", self.font_size_input)
        layout.addRow("Show legend", self.legend_check)
        layout.addRow("Legend location", self.legend_location)
        layout.addRow("X minimum", self.x_min)
        layout.addRow("X maximum", self.x_max)
        layout.addRow("Y minimum", self.y_min)
        layout.addRow("Y maximum", self.y_max)
        layout.addRow("Log X axis", self.x_log_check)
        layout.addRow("Log Y axis", self.y_log_check)
        self.reset_settings_button = QPushButton("Reset")
        self.reset_settings_button.clicked.connect(self.reset_requested)
        layout.addRow(self.reset_settings_button)
        for widget in (
            self.title_input,
            self.xlabel_input,
            self.ylabel_input,
            self.x_min,
            self.x_max,
            self.y_min,
            self.y_max,
        ):
            widget.textChanged.connect(self._request_plot_update)
        for widget in (
            self.width_input,
            self.height_input,
            self.dpi_input,
            self.font_size_input,
        ):
            widget.valueChanged.connect(self._request_plot_update)
        for widget in (self.legend_check, self.x_log_check, self.y_log_check):
            widget.stateChanged.connect(self._request_plot_update)
        self.legend_location.currentTextChanged.connect(self._request_plot_update)
        return page

    def reset_global_settings(self) -> None:
        """Restore only the Figure Settings controls to their defaults."""
        widgets = (
            self.title_input,
            self.xlabel_input,
            self.ylabel_input,
            self.width_input,
            self.height_input,
            self.dpi_input,
            self.font_size_input,
            self.legend_check,
            self.legend_location,
            self.x_min,
            self.x_max,
            self.y_min,
            self.y_max,
            self.x_log_check,
            self.y_log_check,
        )
        blockers = [QSignalBlocker(widget) for widget in widgets]
        self.title_input.clear()
        self.xlabel_input.clear()
        self.ylabel_input.clear()
        self.width_input.setValue(5.0)
        self.height_input.setValue(4.0)
        self.dpi_input.setValue(100)
        self.font_size_input.setValue(10)
        self.legend_check.setChecked(False)
        self.legend_location.setCurrentText("best")
        self.x_min.clear()
        self.x_max.clear()
        self.y_min.clear()
        self.y_max.clear()
        self.x_log_check.setChecked(False)
        self.y_log_check.setChecked(False)
        del blockers

    def _build_line_settings(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        self.line_table = QTableWidget(0, 5)
        self.line_table.setHorizontalHeaderLabels(
            ["Source", "Label", "Color", "Line", "Marker"]
        )
        self.line_table.verticalHeader().setVisible(False)
        self.line_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        header = self.line_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        for column, width in enumerate([96, 88, 56, 76, 58]):
            self.line_table.setColumnWidth(column, width)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.line_table.itemChanged.connect(self._request_plot_update)
        layout.addWidget(self.line_table)
        return page

    def update_datasets(
        self,
        datasets: dict[str, tuple[str, ...]],
        selections: dict[str, tuple[str, list[str]]],
    ) -> None:
        """Populate the independent dataset tree."""
        self.dataset_tree.clear()
        for name, labels in datasets.items():
            if not labels:
                continue
            x_label, y_labels = selections.get(name, (labels[0], []))
            self.dataset_tree.add_table_item(name, is_file_based=True)
            self.dataset_tree.update_table_columns(
                name, list(labels), x_label, y_labels
            )

    def update_series_table(
        self,
        series: list[tuple[str, str]],
        saved_options: dict[SeriesKey, LineOptions] | None = None,
    ) -> None:
        """Rebuild editable style rows for plotted series."""
        options_by_series = (
            saved_options if saved_options is not None else self.series_options()
        )
        self._building_line_table = True
        self.line_table.setRowCount(0)
        for row, (label, dataset) in enumerate(series):
            self.line_table.insertRow(row)
            source = QTableWidgetItem(dataset)
            source.setFlags(Qt.ItemFlag.ItemIsEnabled)
            source.setToolTip(f"Source data: {dataset}")
            self.line_table.setItem(row, 0, source)
            label_item = QTableWidgetItem(label)
            label_item.setData(SERIES_LABEL_ROLE, label)
            self.line_table.setItem(row, 1, label_item)
            self._add_line_combo(
                row, 2, ["auto", "blue", "orange", "green", "red", "black"]
            )
            self._add_line_options(row)
            self._add_marker_options(row)
            self._restore_line_options(row, options_by_series.get((dataset, label)))
            self.line_table.setToolTip(f"Source: {dataset}")
        self._building_line_table = False

    def series_options(self) -> dict[SeriesKey, LineOptions]:
        """Return current settings keyed by their stable data source and label."""
        options: dict[SeriesKey, LineOptions] = {}
        for row in range(self.line_table.rowCount()):
            source = self.line_table.item(row, 0)
            label = self.line_table.item(row, 1)
            if source is not None and label is not None:
                series_label = label.data(SERIES_LABEL_ROLE)
                if isinstance(series_label, str):
                    options[(source.text(), series_label)] = self.line_options(row)
        return options

    def line_options(self, row: int) -> LineOptions:
        """Return style values for a selected plot series row."""
        label = self.line_table.item(row, 1)
        color = self.line_table.cellWidget(row, 2)
        line = self.line_table.cellWidget(row, 3)
        marker = self.line_table.cellWidget(row, 4)
        return {
            "label": label.text() if label is not None else "",
            "color": color.currentText() if isinstance(color, QComboBox) else "auto",
            "linestyle": (
                line.line_style() if isinstance(line, LineOptionsButton) else "-"
            ),
            "linewidth": (
                line.line_width() if isinstance(line, LineOptionsButton) else 1.5
            ),
            "marker": marker.marker()
            if isinstance(marker, MarkerOptionsButton)
            else "None",
            "markersize": marker.marker_size()
            if isinstance(marker, MarkerOptionsButton)
            else 6.0,
            "fillstyle": marker.fillstyle()
            if isinstance(marker, MarkerOptionsButton)
            else "full",
        }

    def _add_line_combo(self, row: int, column: int, values: list[str]) -> None:
        combo = QComboBox()
        combo.addItems(values)
        combo.currentTextChanged.connect(self._request_plot_update)
        self.line_table.setCellWidget(row, column, combo)

    def _add_line_options(self, row: int) -> None:
        line_options = LineOptionsButton()
        line_options.options_changed.connect(self._request_plot_update)
        self.line_table.setCellWidget(row, 3, line_options)

    def _add_marker_options(self, row: int) -> None:
        marker_options = MarkerOptionsButton()
        marker_options.options_changed.connect(self._request_plot_update)
        self.line_table.setCellWidget(row, 4, marker_options)

    def _restore_line_options(self, row: int, options: LineOptions | None) -> None:
        """Restore a previous row's settings when its series remains selected."""
        if options is None:
            return
        label = self.line_table.item(row, 1)
        color = self.line_table.cellWidget(row, 2)
        line = self.line_table.cellWidget(row, 3)
        marker = self.line_table.cellWidget(row, 4)
        if label is not None:
            label.setText(str(options["label"]))
        if isinstance(color, QComboBox):
            color.setCurrentText(str(options["color"]))
        if isinstance(line, LineOptionsButton):
            line.set_options(str(options["linestyle"]), float(options["linewidth"]))
        if isinstance(marker, MarkerOptionsButton):
            marker.set_options(
                str(options["marker"]),
                float(options["markersize"]),
                str(options["fillstyle"]),
            )

    def _request_plot_update(self) -> None:
        """Redraw immediately after a Figure or line-style setting changes."""
        if not self._building_line_table:
            self.plot_requested.emit()


class ScaledFigurePreview(QLabel):
    """Display a rendered figure as a proportionally scaled, non-reflowing image."""

    def __init__(self) -> None:
        super().__init__()
        self._source_pixmap = QPixmap()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background: white; border: 1px solid #b0b0b0;")

    def set_source_pixmap(self, pixmap: QPixmap) -> None:
        """Set the original rendered Figure image."""
        self._source_pixmap = pixmap
        self._update_scaled_pixmap()

    def resizeEvent(self, event) -> None:
        """Scale the same image for the available preview area."""
        super().resizeEvent(event)
        self._update_scaled_pixmap()

    def _update_scaled_pixmap(self) -> None:
        if self._source_pixmap.isNull() or self.size().isEmpty():
            return
        self.setPixmap(
            self._source_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
