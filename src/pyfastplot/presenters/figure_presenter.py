"""Presenter for the independent publication-figure workspace."""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
from matplotlib.axes import Axes
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QInputDialog,
    QMessageBox,
    QTreeWidgetItem,
)

from ..models.data_model import DataModel, DataTable, UnsupportedFileFormatError
from ..models.figure_model import FigureModel
from ..services.import_profiles import supported_extensions
from ..views.components.figure_tab import FigureTab
from ..views.components.import_profile_manager import ImportProfileManager
from ..views.components.import_profile_wizard import ImportProfileWizard
from ..views.table_window import TableWindow


class FigurePresenter:
    """Connect figure data, Matplotlib rendering, and style controls."""

    def __init__(
        self,
        view: FigureTab,
        model: FigureModel,
        data_model: DataModel,
    ) -> None:
        self.view = view
        self.model = model
        self.data_model = data_model
        self.table_windows: dict[str, TableWindow] = {}
        self._connect_signals()

    def _connect_signals(self) -> None:
        self.view.plot_requested.connect(self.refresh_plot)
        self.view.copy_requested.connect(self.copy_plot)
        self.view.save_requested.connect(self.save_plot)
        self.view.reset_requested.connect(self.on_reset_settings)
        self.view.file_dropped.connect(self.load_file)
        self.view.load_file_button.clicked.connect(self.on_load_file_clicked)
        self.view.dataset_tree.itemSelectionChanged.connect(self._on_tree_selection)
        self.view.dataset_tree.axis_selection_changed.connect(
            self._rebuild_from_checked_columns
        )
        self.view.dataset_tree.delete_table_signal.connect(self.on_remove_dataset)
        self.view.dataset_tree.delete_tables_signal.connect(self._remove_datasets)
        self.view.dataset_tree.reload_table_signal.connect(self.reload_file)
        self.view.dataset_tree.rename_table_signal.connect(self.on_rename_table)
        self.view.dataset_tree.delete_all_signal.connect(self.on_remove_all_datasets)
        self.view.dataset_tree.new_table_signal.connect(self.on_add_input_table)
        self.view.dataset_tree.itemDoubleClicked.connect(
            lambda item, _column: self.on_table_double_clicked(item)
        )

    def add_dataset(self, name: str, labels: list[str], data: np.ndarray) -> str:
        """Add post-processed data to this independent workspace.

        This is the public bridge for the future ``View Data`` transfer action.
        """
        dataset_name = self.model.add_dataset(name, labels, data)
        self._ensure_editable_table(dataset_name, labels, data)
        self._update_datasets()
        self.on_dataset_selected(dataset_name)
        return dataset_name

    def _ensure_editable_table(
        self, name: str, labels: list[str], data: np.ndarray
    ) -> None:
        """Create a Figure-local editable table for transferred plot data."""
        if name in self.data_model.all_tables:
            return
        table = DataTable(name, max(1, len(labels)))
        table.data = np.asarray(data, dtype=object).copy()
        table.labels = list(labels)
        table.x_sel = labels[0] if labels else ""
        table.y_sels = []
        self.data_model.all_tables[name] = table

    def load_file(self, file_path: str) -> None:
        """Import a dropped text data file into the Figure-only data space."""
        try:
            path = Path(file_path)
            if not path.is_file():
                raise FileNotFoundError(path)
            table_name = self.data_model.load_csv_file(str(path))
            table = self.data_model.all_tables[table_name]
            self.data_model.set_current_table(table_name)
            self.add_dataset(table_name, table.labels, self._table_data(table))
        except UnsupportedFileFormatError:
            extensions = ", ".join(sorted(supported_extensions()))
            QMessageBox.warning(
                self.view,
                "Unsupported file format",
                f"'{Path(file_path).name}' cannot be imported.\n\n"
                f"Supported text formats: {extensions}",
            )
        except (OSError, UnicodeError, ValueError, KeyError) as error:
            QMessageBox.warning(
                self.view,
                "Cannot import file",
                f"Could not import '{Path(file_path).name}'.\n\nReason: {error}",
            )

    def on_load_file_clicked(self) -> None:
        """Open files into the Figure-only data workspace."""
        from ..services.import_profiles import file_dialog_filter

        file_paths, _ = QFileDialog.getOpenFileNames(
            self.view,
            "Open Text Data File",
            "",
            file_dialog_filter(),
        )
        for file_path in file_paths:
            self.load_file(file_path)

    def on_new_import_format_clicked(self) -> None:
        """Create one shared text import format from a tested sample file."""
        dialog = ImportProfileWizard(self.view.window())
        if dialog.exec() == ImportProfileWizard.DialogCode.Accepted:
            self.data_model.save_import_profile(dialog.profile())

    def on_manage_import_formats_clicked(self) -> None:
        """Show the shared text import format manager."""
        ImportProfileManager(self.view.window()).exec()

    def reload_file(self, table_name: str) -> None:
        """Reload a Figure source using the shared Post-processing parser."""
        if not self.data_model.reload_table(table_name):
            QMessageBox.warning(
                self.view,
                "Cannot reload file",
                "Original file not found.",
            )
            return
        table = self.data_model.all_tables[table_name]
        self.model.remove_dataset(table_name)
        self.add_dataset(table_name, table.labels, self._table_data(table))
        self._rebuild_from_checked_columns(table_name)

    def on_dataset_selected(self, name: str) -> None:
        """Update X/Y selections for an independent dataset."""
        self.model.set_current_dataset(name)
        if name in self.data_model.all_tables:
            self.data_model.set_current_table(name)

    def on_remove_dataset(self, name: str) -> None:
        """Remove data only from the independent figure workspace."""
        self.model.remove_dataset(name)
        self.data_model.delete_table(name)
        self._close_table_window(name)
        self._update_datasets()
        self._update_series_table()
        self.refresh_plot()

    def _remove_datasets(self, names: list[str]) -> None:
        for name in names:
            self.model.remove_dataset(name)
            self.data_model.delete_table(name)
            self._close_table_window(name)
        self._update_datasets()
        self._update_series_table()
        self.refresh_plot()

    def refresh_plot(self) -> None:
        """Render the selected figure series using its current style controls."""
        axes = self.view.axes
        axes.clear()
        if self.view.display_mode_name() == "Canvas (actual size)":
            self._set_output_figure_size()
        self._draw_series(axes)
        self._apply_axes_settings(axes)
        self.view.prepare_canvas_hover()
        self.view.update_canvas_display()
        self.view.canvas.draw()
        if self.view.display_mode_name() == "Preview (scaled)":
            self._render_preview()

    def copy_plot(self) -> None:
        """Copy the current rendered figure to the system clipboard."""
        image = QImage.fromData(self._render_figure_bytes())
        clipboard = QApplication.clipboard()
        if clipboard is not None:
            clipboard.setPixmap(QPixmap.fromImage(image))

    def on_reset_settings(self) -> None:
        """Reset Figure Settings and immediately redraw the active Figure."""
        self.view.reset_global_settings()
        self.refresh_plot()

    def save_plot(self) -> None:
        """Save the current figure in PNG or SVG format."""
        path, _ = QFileDialog.getSaveFileName(
            self.view, "Save figure", "figure.png", "PNG (*.png);;SVG (*.svg)"
        )
        if path:
            self._save_figure(Path(path), Path(path).suffix.lstrip(".") or "png")

    def _update_datasets(self) -> None:
        datasets = {
            name: dataset.labels for name, dataset in self.model.datasets.items()
        }
        selections = {
            name: self._selection_for_dataset(name, labels)
            for name, labels in datasets.items()
        }
        self.view.update_datasets(datasets, selections)

    def _selection_for_dataset(
        self, name: str, labels: tuple[str, ...]
    ) -> tuple[str, list[str]]:
        """Return a valid persisted X/Y layout for one Figure dataset."""
        table = self.data_model.all_tables.get(name)
        if table is None:
            return (labels[0], []) if labels else ("", [])
        x_label = table.x_sel if table.x_sel in labels else labels[0]
        y_labels = [label for label in table.y_sels if label in labels]
        return x_label, y_labels

    def _table_data(self, table: DataTable) -> np.ndarray:
        """Return only columns represented by the shared table labels."""
        return table.data[:, : len(table.labels)]

    def _on_tree_selection(self) -> None:
        items = self.view.dataset_tree.selectedItems()
        if not items:
            return
        name = self.view.dataset_tree.table_name_for_item(items[0])
        if name:
            self.on_dataset_selected(name)

    def on_table_double_clicked(self, item: QTreeWidgetItem) -> None:
        """Open the editable source table when its top-level row is opened."""
        if item.parent() is not None:
            return
        table_name = self.view.dataset_tree.table_name_for_item(item)
        if table_name:
            self.open_table_window(table_name)

    def _rebuild_from_checked_columns(self, _table_name: str) -> None:
        """Build Figure lines from the Post-processing-style tree selection."""
        for table_name in self.model.datasets:
            table = self.data_model.all_tables.get(table_name)
            if table is None:
                continue
            table.x_sel = self.view.dataset_tree.x_label_for_table(table_name)
            table.y_sels = self.view.dataset_tree.y_labels_for_table(table_name)
        self.model.series.clear()
        sources = self.view.dataset_tree.selected_plot_sources()
        for table_name, x_label, y_label in sources:
            self.model.set_current_dataset(table_name)
            self.model.add_series(x_label, y_label, replace=False)
        self._update_series_table()
        self.refresh_plot()

    def on_add_input_table(self) -> None:
        """Create a manually editable Figure source table."""
        column_count, accepted = QInputDialog.getInt(
            self.view, "New Table", "Column count:", 2, 1, 500, 1
        )
        if not accepted:
            return
        table_name = self.data_model.add_input_table(column_count)
        table = self.data_model.all_tables[table_name]
        self.data_model.set_current_table(table_name)
        self.add_dataset(table_name, table.labels, self._table_data(table))
        self.open_table_window(table_name)

    def open_table_window(self, table_name: str) -> None:
        """Show the editable table window for a Figure source."""
        if table_name in self.table_windows:
            window = self.table_windows[table_name]
            window.raise_()
            window.activateWindow()
            return
        table = self.data_model.all_tables.get(table_name)
        if table is None:
            return
        window = TableWindow(table_name, table, self, self.view)
        self.table_windows[table_name] = window
        window.show()

    def set_active_table_from_window(self, table_name: str) -> None:
        """Keep Figure data selection in sync with an activated table window."""
        self.data_model.set_current_table(table_name)
        items = self.view.dataset_tree.findItems(table_name, Qt.MatchFlag.MatchExactly)
        if items:
            self.view.dataset_tree.blockSignals(True)
            self.view.dataset_tree.setCurrentItem(items[0])
            self.view.dataset_tree.blockSignals(False)
        self.on_dataset_selected(table_name)

    def on_window_closed(self, table_name: str) -> None:
        """Forget a closed Figure table window."""
        self.table_windows.pop(table_name, None)

    def on_rename_table(self, old_name: str, new_name: str) -> None:
        """Rename the Figure data and its editable table together."""
        if not self.data_model.rename_table(old_name, new_name):
            return
        dataset = self.model.datasets.get(old_name)
        if dataset is not None:
            self.model.remove_dataset(old_name)
            self.model.add_dataset(new_name, list(dataset.labels), dataset.data)
        if old_name in self.table_windows:
            window = self.table_windows.pop(old_name)
            window.table_name = new_name
            window.setWindowTitle(f"Table: {new_name}")
            self.table_windows[new_name] = window
        self._update_datasets()
        self._rebuild_from_checked_columns(new_name)

    def on_remove_all_datasets(self) -> None:
        """Clear every Figure-only source without a confirmation dialog."""
        for name in list(self.table_windows):
            self._close_table_window(name)
        self.data_model.clear_all()
        self.model.datasets.clear()
        self.model.series.clear()
        self._update_datasets()
        self._update_series_table()
        self.refresh_plot()

    def _close_table_window(self, table_name: str) -> None:
        """Close an editable table window without retaining its reference."""
        window = self.table_windows.pop(table_name, None)
        if window is not None:
            window.close()

    def _sync_current_table(self) -> None:
        """Push editable-table changes back into Figure data and plot lines."""
        table = self.data_model.current_table
        if table is None:
            return
        self.model.remove_dataset(table.name)
        self.model.add_dataset(table.name, table.labels, self._table_data(table))
        self._update_datasets()
        self._rebuild_from_checked_columns(table.name)
        window = self.table_windows.get(table.name)
        if window is not None:
            window.table_widget.set_data_table(table)

    def on_data_pasted(
        self, start_row: int, start_col: int, parsed_data: list[list[object]]
    ) -> None:
        """Apply a pasted edit to the active Figure source."""
        if self.data_model.paste_data_to_current(start_row, start_col, parsed_data):
            self._sync_current_table()

    def on_delete_rows(self, row_indices: list[int]) -> None:
        """Delete active-table rows and update its Figure dataset."""
        self.data_model.delete_data_rows(row_indices)
        self._sync_current_table()

    def on_delete_cols(self, col_indices: list[int]) -> None:
        """Delete active-table columns and update its Figure dataset."""
        self.data_model.delete_data_cols(col_indices)
        self._sync_current_table()

    def on_clear_cells(self, cells: list[tuple[int, int]]) -> None:
        """Clear active-table cells and update its Figure dataset."""
        self.data_model.clear_data_cells(cells)
        self._sync_current_table()

    def on_set_as_labels(self, row_index: int) -> None:
        """Promote a data row to Figure source labels."""
        self.data_model.promote_row_to_labels(row_index)
        self._sync_current_table()

    def on_rename_column(self, col_index: int, new_name: str) -> None:
        """Rename an active Figure source column."""
        self.data_model.update_label(col_index, new_name)
        self._sync_current_table()

    def on_undo(self) -> None:
        """Undo an editable Figure-table operation."""
        if self.data_model.undo_current_table():
            self._sync_current_table()

    def on_redo(self) -> None:
        """Redo an editable Figure-table operation."""
        if self.data_model.redo_current_table():
            self._sync_current_table()

    def _update_series_table(self) -> None:
        rows = [(series.label, series.dataset_name) for series in self.model.series]
        self.view.update_series_table(rows)

    def _save_figure(self, target: io.BytesIO | Path, image_format: str) -> None:
        """Save the actual figure at its configured physical size."""
        figure = self._create_export_figure()
        figure.savefig(
            target,
            format=image_format,
            dpi=self.view.dpi_input.value(),
        )

    def _render_preview(self) -> None:
        """Render once at export size and hand the fixed image to the preview."""
        image = QImage.fromData(self._render_figure_bytes())
        self.view.set_preview_image(QPixmap.fromImage(image))

    def _render_figure_bytes(self) -> bytes:
        """Return the current Figure rendered at its configured output dimensions."""
        buffer = io.BytesIO()
        figure = self._create_export_figure()
        figure.savefig(buffer, format="png", dpi=self.view.dpi_input.value())
        return buffer.getvalue()

    def _create_export_figure(self) -> Figure:
        """Build an off-screen Figure so exports cannot resize the Canvas."""
        figure = Figure(
            figsize=(self.view.width_input.value(), self.view.height_input.value()),
            constrained_layout=True,
        )
        FigureCanvasAgg(figure)
        axes = figure.add_subplot(111)
        self._draw_series(axes)
        self._apply_axes_settings(axes)
        return figure

    def _draw_series(self, axes: Axes) -> None:
        """Draw the selected Figure series onto one Matplotlib axes."""
        for index, series in enumerate(self.model.series):
            options = self.view.line_options(index)
            color_value = str(options["color"])
            marker_value = str(options["marker"])
            color = None if color_value == "auto" else color_value
            marker = None if marker_value == "None" else marker_value
            axes.plot(
                series.x_data,
                series.y_data,
                label=str(options["label"] or series.label),
                color=color,
                linestyle=str(options["linestyle"]),
                linewidth=float(str(options["linewidth"])),
                marker=marker,
                markersize=float(str(options["markersize"])),
                fillstyle=str(options["fillstyle"]),
            )

    def _set_output_figure_size(self) -> None:
        """Set the physical Figure size used by preview and export rendering."""
        self.view.figure.set_size_inches(
            self.view.width_input.value(),
            self.view.height_input.value(),
            forward=False,
        )

    def _apply_axes_settings(self, axes: Axes) -> None:
        font_size = self.view.font_size_input.value()
        axes.set_title(self.view.title_input.text(), fontsize=font_size + 2)
        axes.set_xlabel(self.view.xlabel_input.text(), fontsize=font_size)
        axes.set_ylabel(self.view.ylabel_input.text(), fontsize=font_size)
        axes.tick_params(labelsize=self.view.font_size_input.value())
        axes.set_xscale("log" if self.view.x_log_check.isChecked() else "linear")
        axes.set_yscale("log" if self.view.y_log_check.isChecked() else "linear")
        self._apply_axis_limits(axes)
        axes.grid(True, alpha=0.3)
        if self.view.legend_check.isChecked() and axes.lines:
            axes.legend(loc=self.view.legend_location.currentText())

    def _apply_axis_limits(self, axes: Axes) -> None:
        x_limits = self._limits(self.view.x_min.text(), self.view.x_max.text())
        y_limits = self._limits(self.view.y_min.text(), self.view.y_max.text())
        if x_limits is not None:
            axes.set_xlim(left=x_limits[0], right=x_limits[1])
        if y_limits is not None:
            axes.set_ylim(bottom=y_limits[0], top=y_limits[1])

    def _limits(
        self, lower: str, upper: str
    ) -> tuple[float | None, float | None] | None:
        """Return valid optional bounds while preserving an automatic opposite side."""
        try:
            low_value = float(lower) if lower.strip() else None
            high_value = float(upper) if upper.strip() else None
        except ValueError:
            return None
        if low_value is None and high_value is None:
            return None
        if (
            low_value is not None
            and high_value is not None
            and low_value >= high_value
        ):
            return None
        return low_value, high_value
