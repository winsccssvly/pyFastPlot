import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QHeaderView, QMenu, QTableView

from .table_model import DataTableModel
from .text_wizard import TextImportWizard


class TableWidget(QTableView):
    data_pasted_signal = Signal(int, int, list)
    delete_rows_signal = Signal(list)
    delete_cols_signal = Signal(list)
    clear_cells_signal = Signal(list)
    set_as_labels_signal = Signal(int)
    rename_col_signal = Signal(int, str)
    undo_signal = Signal()
    redo_signal = Signal()

    def __init__(self):
        super().__init__()
        self.model_obj = DataTableModel()
        self.setModel(self.model_obj)

        # UI Tweaks
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.setSelectionMode(QTableView.SelectionMode.ExtendedSelection)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_main_context_menu)

        h_header = self.horizontalHeader()
        h_header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        h_header.customContextMenuRequested.connect(self.show_col_context_menu)
        h_header.sectionDoubleClicked.connect(self.on_header_double_clicked)

        v_header = self.verticalHeader()
        v_header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        v_header.customContextMenuRequested.connect(self.show_row_context_menu)

    def set_data_table(self, data_table):
        self.model_obj.set_table(data_table)

    def keyPressEvent(self, e):
        if e.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if e.key() == Qt.Key.Key_V:
                if e.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    self.open_wizard()
                else:
                    self.paste_data()
            elif e.key() == Qt.Key.Key_Z:
                self.undo_signal.emit()
            elif e.key() == Qt.Key.Key_Y:
                self.redo_signal.emit()
            else:
                super().keyPressEvent(e)
        elif e.key() == Qt.Key.Key_Delete or e.key() == Qt.Key.Key_Backspace:
            self.clear_selected_cells()
        else:
            super().keyPressEvent(e)

    def clear_selected_cells(self):
        indexes = self.selectionModel().selectedIndexes()
        cells = [(idx.row(), idx.column()) for idx in indexes]
        if cells:
            self.clear_cells_signal.emit(cells)

    def show_col_context_menu(self, pos):
        h_header = self.horizontalHeader()
        col = h_header.logicalIndexAt(pos)
        if col >= 0:
            menu = QMenu()
            del_action = QAction("Delete entire column", self)

            selected_indexes = self.selectionModel().selectedIndexes()
            selected_cols = set(idx.column() for idx in selected_indexes)

            if col in selected_cols and len(selected_cols) > 1:
                del_action.setText(f"Delete {len(selected_cols)} selected columns")
                del_action.triggered.connect(
                    lambda: self.delete_cols_signal.emit(list(selected_cols))
                )
            else:
                del_action.triggered.connect(
                    lambda: self.delete_cols_signal.emit([col])
                )

            rename_action = QAction("Rename column", self)
            rename_action.triggered.connect(lambda: self.on_header_double_clicked(col))

            menu.addAction(rename_action)
            menu.addSeparator()
            menu.addAction(del_action)
            menu.exec(h_header.mapToGlobal(pos))

    def on_header_double_clicked(self, logicalIndex):
        from PySide6.QtWidgets import QInputDialog

        old_name = self.model_obj.headerData(
            logicalIndex, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole
        )
        new_name, ok = QInputDialog.getText(
            self, "Rename Column", "Enter new column name:", text=old_name
        )
        if ok and new_name.strip():
            self.rename_col_signal.emit(logicalIndex, new_name.strip())

    def show_row_context_menu(self, pos):
        v_header = self.verticalHeader()
        row = v_header.logicalIndexAt(pos)
        if row >= 0:
            menu = QMenu()
            del_action = QAction("Delete entire row", self)

            selected_indexes = self.selectionModel().selectedIndexes()
            selected_rows = set(idx.row() for idx in selected_indexes)

            if row in selected_rows and len(selected_rows) > 1:
                del_action.setText(f"Delete {len(selected_rows)} selected rows")
                del_action.triggered.connect(
                    lambda: self.delete_rows_signal.emit(list(selected_rows))
                )
            else:
                del_action.triggered.connect(
                    lambda: self.delete_rows_signal.emit([row])
                )

            promote_action = QAction("Set as Column Labels", self)
            promote_action.triggered.connect(
                lambda: self.set_as_labels_signal.emit(row)
            )
            menu.addAction(promote_action)
            menu.addSeparator()

            menu.addAction(del_action)
            menu.exec(v_header.mapToGlobal(pos))

    def show_main_context_menu(self, pos):
        menu = QMenu()
        wizard_action = QAction("Text Import Wizard (Paste Special)...", self)
        wizard_action.setShortcut("Ctrl+Shift+V")
        wizard_action.triggered.connect(self.open_wizard)
        menu.addAction(wizard_action)

        paste_action = QAction("Paste (Default)", self)
        paste_action.setShortcut("Ctrl+V")
        paste_action.triggered.connect(self.paste_data)
        menu.addAction(paste_action)

        menu.exec(self.viewport().mapToGlobal(pos))

    def open_wizard(self):
        clipboard = QApplication.clipboard()
        if not clipboard:
            return
        text = clipboard.text()
        if not text:
            return

        dialog = TextImportWizard(self, text)
        if dialog.exec() == TextImportWizard.DialogCode.Accepted:
            parsed_data = dialog.get_data()
            if parsed_data:
                index = self.currentIndex()
                start_row = index.row() if index.isValid() else 0
                start_col = index.column() if index.isValid() else 0
                self.data_pasted_signal.emit(start_row, start_col, parsed_data)

    def paste_data(self):
        clipboard = QApplication.clipboard()
        if not clipboard:
            return
        clipboard_text = clipboard.text()
        if not clipboard_text:
            return

        index = self.currentIndex()
        start_row = index.row() if index.isValid() else 0
        start_col = index.column() if index.isValid() else 0

        rows = clipboard_text.strip("\n").split("\n")
        parsed_data = []
        for r in rows:
            row_vals = []
            for val_str in r.split("\t"):
                val_str = val_str.strip()
                try:
                    row_vals.append(float(val_str))
                except ValueError:
                    row_vals.append(val_str if val_str else np.nan)
            parsed_data.append(row_vals)

        self.data_pasted_signal.emit(start_row, start_col, parsed_data)
