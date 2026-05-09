import numpy as np
from PySide6.QtCore import Signal, Qt, QModelIndex
from PySide6.QtWidgets import QTableView, QApplication, QMenu, QHeaderView
from PySide6.QtGui import QAction
from .table_model import DataTableModel

class TableWidget(QTableView):
    data_pasted_signal = Signal(int, int, list)
    delete_rows_signal = Signal(list)
    delete_cols_signal = Signal(list)
    clear_cells_signal = Signal(list)
    set_as_labels_signal = Signal(int)

    def __init__(self):
        super().__init__()
        self.model_obj = DataTableModel()
        self.setModel(self.model_obj)
        
        # UI Tweaks
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.setSelectionMode(QTableView.SelectionMode.ExtendedSelection)
        
        h_header = self.horizontalHeader()
        h_header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        h_header.customContextMenuRequested.connect(self.show_col_context_menu)
        
        v_header = self.verticalHeader()
        v_header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        v_header.customContextMenuRequested.connect(self.show_row_context_menu)

    def set_data_table(self, data_table):
        self.model_obj.set_table(data_table)

    def keyPressEvent(self, e):
        if e.modifiers() & Qt.KeyboardModifier.ControlModifier and e.key() == Qt.Key.Key_V:
            self.paste_data()
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
                del_action.triggered.connect(lambda: self.delete_cols_signal.emit(list(selected_cols)))
            else:
                del_action.triggered.connect(lambda: self.delete_cols_signal.emit([col]))
                
            menu.addAction(del_action)
            menu.exec(h_header.mapToGlobal(pos))

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
                del_action.triggered.connect(lambda: self.delete_rows_signal.emit(list(selected_rows)))
            else:
                del_action.triggered.connect(lambda: self.delete_rows_signal.emit([row]))
                
            promote_action = QAction("Set as Column Labels", self)
            promote_action.triggered.connect(lambda: self.set_as_labels_signal.emit(row))
            menu.addAction(promote_action)
            menu.addSeparator()

            menu.addAction(del_action)
            menu.exec(v_header.mapToGlobal(pos))
    
    def paste_data(self):
        clipboard = QApplication.clipboard()
        if not clipboard: return
        clipboard_text = clipboard.text()
        if not clipboard_text: return
        
        index = self.currentIndex()
        start_row = index.row() if index.isValid() else 0
        start_col = index.column() if index.isValid() else 0
        
        rows = clipboard_text.strip('\n').split('\n')
        parsed_data = []
        for r in rows:
            row_vals = []
            for val_str in r.split('\t'):
                val_str = val_str.strip()
                try:
                    row_vals.append(float(val_str))
                except ValueError:
                    row_vals.append(val_str if val_str else np.nan)
            parsed_data.append(row_vals)
        
        self.data_pasted_signal.emit(start_row, start_col, parsed_data)

