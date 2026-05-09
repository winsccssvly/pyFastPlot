import numpy as np
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QTableWidget, QApplication, QMessageBox, QMenu
from PySide6.QtGui import QAction

class TableWidget(QTableWidget):
    data_pasted_signal = Signal(int, int, list)
    delete_rows_signal = Signal(list)
    delete_cols_signal = Signal(list)
    clear_cells_signal = Signal(list)

    def __init__(self):
        super().__init__()
        self.setRowCount(0)
        self.setColumnCount(0)
        
        h_header = self.horizontalHeader()
        if h_header is not None:
            h_header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            h_header.customContextMenuRequested.connect(self.show_col_context_menu)
        
        v_header = self.verticalHeader()
        if v_header is not None:
            v_header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            v_header.customContextMenuRequested.connect(self.show_row_context_menu)
    
    def keyPressEvent(self, e):
        if e.modifiers() & Qt.KeyboardModifier.ControlModifier and e.key() == Qt.Key.Key_V:
            self.paste_data()
        elif e.key() == Qt.Key.Key_Delete or e.key() == Qt.Key.Key_Backspace:
            self.clear_selected_cells()
        else:
            super().keyPressEvent(e)

    def clear_selected_cells(self):
        cells = []
        for item in self.selectedItems():
            row = item.row()
            col = item.column()
            if row > 0: # Header is row 0, data starts at 1
                cells.append((row - 1, col))
        if cells:
            self.clear_cells_signal.emit(cells)

    def show_col_context_menu(self, pos):
        h_header = self.horizontalHeader()
        if h_header is None:
            return
            
        col = h_header.logicalIndexAt(pos)
        if col >= 0:
            menu = QMenu()
            del_action = QAction("Delete entire column", self)
            
            selected_cols = set()
            for item in self.selectedItems():
                selected_cols.add(item.column())
                
            if col in selected_cols and len(selected_cols) > 1:
                del_action.setText(f"Delete {len(selected_cols)} selected columns")
                del_action.triggered.connect(lambda: self.delete_cols_signal.emit(list(selected_cols)))
            else:
                del_action.triggered.connect(lambda: self.delete_cols_signal.emit([col]))
                
            menu.addAction(del_action)
            menu.exec(h_header.mapToGlobal(pos))

    def show_row_context_menu(self, pos):
        v_header = self.verticalHeader()
        if v_header is None:
            return
            
        row = v_header.logicalIndexAt(pos)
        if row > 0:
            menu = QMenu()
            del_action = QAction("Delete entire row", self)
            
            selected_rows = set()
            for item in self.selectedItems():
                if item.row() > 0:
                    selected_rows.add(item.row() - 1)
            
            if (row - 1) in selected_rows and len(selected_rows) > 1:
                del_action.setText(f"Delete {len(selected_rows)} selected rows")
                del_action.triggered.connect(lambda: self.delete_rows_signal.emit(list(selected_rows)))
            else:
                del_action.triggered.connect(lambda: self.delete_rows_signal.emit([row - 1]))
                
            menu.addAction(del_action)
            menu.exec(v_header.mapToGlobal(pos))
    
    def paste_data(self):
        clipboard = QApplication.clipboard()
        if clipboard is None:
            return
        clipboard_text = clipboard.text()
        if not clipboard_text:
            return
        
        start_col = self.currentColumn()
        start_row = self.currentRow()
        if start_col < 0: start_col = 0
        if start_row < 0: start_row = 1 # Default to pasting into data, not header
        
        # If the user clicked on row 0 (headers), we still let them paste, but we subtract 1 so data row index starts at -1? 
        # Actually, in the model, row index 0 is data row 0.
        # UI row 0 is header. UI row 1 is data row 0.
        # If user pastes at UI row 1, data row is 0.
        # Let's adjust start_row to data coordinates.
        if start_row == 0:
            start_row = 1
            
        data_start_row = start_row - 1
        
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
        
        self.data_pasted_signal.emit(data_start_row, start_col, parsed_data)
