from PySide6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QLineEdit, 
                             QSpinBox, QDoubleSpinBox, QCheckBox, QTableWidget, 
                             QComboBox, QTabWidget, QHeaderView, QTableWidgetItem, QMenu, QLabel)
from PySide6.QtCore import Qt, Signal
import matplotlib.font_manager as fm

class PlotOptionsWidget(QWidget):
    delete_line_signal = Signal(int)
    
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # --- Global Settings Tab ---
        global_tab = QWidget()
        global_layout = QFormLayout(global_tab)
        
        self.fig_width = QDoubleSpinBox()
        self.fig_width.setValue(6.0)
        self.fig_height = QDoubleSpinBox()
        self.fig_height.setValue(5.0)
        global_layout.addRow("Fig Width (in):", self.fig_width)
        global_layout.addRow("Fig Height (in):", self.fig_height)
        
        self.dpi_input = QSpinBox()
        self.dpi_input.setRange(10, 3000)
        self.dpi_input.setValue(100)
        global_layout.addRow("DPI:", self.dpi_input)
        
        self.font_family = QComboBox()
        curated_fonts = [
            "Auto",
            "DejaVu Sans (Default)",
            "Times New Roman",
            "Arial",
            "Korean (System Default)"
        ]
        self.font_family.addItems(curated_fonts)
        self.font_family.setCurrentText("Auto")
        global_layout.addRow("Font:", self.font_family)
        
        self.applied_font_label = QLabel("Applied Font: -")
        self.applied_font_label.setStyleSheet("color: #666; font-size: 11px; font-style: italic;")
        global_layout.addRow("", self.applied_font_label)
        
        self.title_input = QLineEdit()
        self.title_size = QSpinBox(); self.title_size.setValue(12)
        global_layout.addRow("Title:", self.title_input)
        global_layout.addRow("Title Size:", self.title_size)
        
        self.xlabel_input = QLineEdit()
        self.ylabel_input = QLineEdit()
        self.label_size = QSpinBox(); self.label_size.setValue(10)
        global_layout.addRow("X Label:", self.xlabel_input)
        global_layout.addRow("Y Label:", self.ylabel_input)
        global_layout.addRow("Label Size:", self.label_size)
        
        self.tick_size = QSpinBox(); self.tick_size.setValue(10)
        global_layout.addRow("Tick Size:", self.tick_size)
        
        self.show_legend = QCheckBox()
        self.show_legend.setChecked(False)
        self.legend_size = QSpinBox(); self.legend_size.setValue(10)
        self.legend_loc = QComboBox()
        self.legend_loc.addItems([
            "best", "upper right", "upper left", "lower left", "lower right",
            "right", "center left", "center right", "lower center", "upper center", "center"
        ])
        global_layout.addRow("Show Legend:", self.show_legend)
        global_layout.addRow("Legend Size:", self.legend_size)
        global_layout.addRow("Legend Loc:", self.legend_loc)
        
        self.xmin_input = QLineEdit()
        self.xmax_input = QLineEdit()
        self.ymin_input = QLineEdit()
        self.ymax_input = QLineEdit()
        
        global_layout.addRow("X Min/Max:", self._create_minmax_layout(self.xmin_input, self.xmax_input))
        global_layout.addRow("Y Min/Max:", self._create_minmax_layout(self.ymin_input, self.ymax_input))
        
        self.tabs.addTab(global_tab, "Global")

        # --- Line Settings Tab ---
        line_tab = QWidget()
        line_layout = QVBoxLayout(line_tab)
        
        self.line_table = QTableWidget(0, 9)
        self.line_table.setHorizontalHeaderLabels(["Plot", "Label", "Color", "Style", "Width", "Marker", "Mk Size", "Fill", "Table"])
        header = self.line_table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            
        self.line_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.line_table.customContextMenuRequested.connect(self.show_context_menu)
        
        line_layout.addWidget(self.line_table)
        
        self.tabs.addTab(line_tab, "Lines")
        
    def show_context_menu(self, pos):
        item = self.line_table.itemAt(pos)
        if item is not None:
            row = item.row()
            menu = QMenu()
            delete_action = menu.addAction("Delete Line")
            viewport = self.line_table.viewport()
            if viewport is not None:
                action = menu.exec(viewport.mapToGlobal(pos))
                if action == delete_action:
                    self.line_table.removeRow(row)
                    self.delete_line_signal.emit(row)
                
    def clear_lines(self):
        self.line_table.setRowCount(0)

    def add_cart_item(self, label, table_name):
        r = self.line_table.rowCount()
        self.line_table.insertRow(r)
        
        # Checkbox
        chk = QTableWidgetItem()
        chk.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
        chk.setCheckState(Qt.CheckState.Checked)
        self.line_table.setItem(r, 0, chk)
        
        # Label
        lbl_item = QTableWidgetItem(label)
        lbl_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsSelectable)
        self.line_table.setItem(r, 1, lbl_item)
        
        # Table
        tbl_item = QTableWidgetItem(table_name)
        tbl_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        self.line_table.setItem(r, 8, tbl_item)
        
        colors = ["auto", "blue", "orange", "green", "red", "purple", "brown", "black", "gray"]
        
        color_combo = QComboBox()
        color_combo.addItems(colors)
        color_combo.setCurrentIndex(0)
        self.line_table.setCellWidget(r, 2, color_combo)
        
        style_combo = QComboBox()
        style_combo.addItems(["-", "--", "-.", ":", "None"])
        self.line_table.setCellWidget(r, 3, style_combo)
        
        width_spin = QDoubleSpinBox()
        width_spin.setValue(1.5)
        width_spin.setSingleStep(0.5)
        self.line_table.setCellWidget(r, 4, width_spin)
        
        marker_combo = QComboBox()
        marker_combo.addItems(["None", "o", "s", "^", "v", "D", "x", "+"])
        self.line_table.setCellWidget(r, 5, marker_combo)
        
        msize_spin = QDoubleSpinBox()
        msize_spin.setValue(6.0)
        self.line_table.setCellWidget(r, 6, msize_spin)
        
        fill_combo = QComboBox()
        fill_combo.addItems(["full", "none", "bottom", "top", "left", "right"])
        self.line_table.setCellWidget(r, 7, fill_combo)
                
    def get_line_options(self, row):
        try:
            color_w = self.line_table.cellWidget(row, 2)
            style_w = self.line_table.cellWidget(row, 3)
            width_w = self.line_table.cellWidget(row, 4)
            marker_w = self.line_table.cellWidget(row, 5)
            msize_w = self.line_table.cellWidget(row, 6)
            fill_w = self.line_table.cellWidget(row, 7)

            if (isinstance(color_w, QComboBox) and isinstance(style_w, QComboBox) and
                isinstance(width_w, QDoubleSpinBox) and isinstance(marker_w, QComboBox) and
                isinstance(msize_w, QDoubleSpinBox) and isinstance(fill_w, QComboBox)):
                
                return {
                    "color": color_w.currentText() if color_w.currentText() != "auto" else "",
                    "linestyle": style_w.currentText(),
                    "linewidth": width_w.value(),
                    "marker": marker_w.currentText(),
                    "markersize": msize_w.value(),
                    "fillstyle": fill_w.currentText(),
                }
        except Exception:
            pass
        return {}
        
    def _create_minmax_layout(self, w1, w2):
        from PySide6.QtWidgets import QHBoxLayout
        w = QWidget()
        l = QHBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        l.addWidget(w1)
        l.addWidget(w2)
        return w
