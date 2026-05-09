import numpy as np
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QPushButton, QHBoxLayout, QVBoxLayout,
    QComboBox, QListWidget, QListWidgetItem, QAbstractItemView, QLabel,
    QTableWidgetItem, QScrollArea, QLineEdit
)
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont

from .components.file_list import FileListWidget
from .components.table import TableWidget
from .components.plot_canvas import MplCanvas
from .components.plot_options import PlotOptionsWidget

class MainWindow(QMainWindow):
    """
    MainWindow orchestrates the main UI layout and acts as the View in the MVP pattern.
    It assembles individual UI components (TableWidget, FileListWidget, MplCanvas, PlotOptionsWidget)
    and exposes them or their signals for the Presenter to bind to.
    """
    def __init__(self):
        super().__init__()
        self.setupUI()
    
    def setupUI(self):
        self.setWindowTitle("Data Visualizer 1.0")
        self.resize(1200, 800)
        
        main_layout = QVBoxLayout()
        
        top_layout = self._create_top_layout()
        main_layout.addLayout(top_layout)
        
        bottom_layout = self._create_bottom_layout()
        main_layout.addLayout(bottom_layout)
        
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)
    
    def _create_top_layout(self):
        top_layout = QHBoxLayout()
        
        graph_layout = QVBoxLayout()
        
        self.sc = MplCanvas(self, width=5, height=4, dpi=100)
        self.toolbar = NavigationToolbar2QT(self.sc, self)
        
        graph_layout.addWidget(self.toolbar)
        graph_layout.addWidget(self.sc)
        
        graph_option_layout = QVBoxLayout()
        
        self.plot_options = PlotOptionsWidget()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.plot_options)
        scroll.setMinimumWidth(410)
        
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
        
        graph_option_layout.addWidget(scroll)
        graph_option_layout.addLayout(button_layout)
        
        # Adjust layout ratios: Graph(0) : Options(1) -> Graph gets natural size, Options fills rest
        top_layout.addLayout(graph_layout, 0)
        top_layout.addLayout(graph_option_layout, 1)
        
        return top_layout

    def _create_bottom_layout(self):
        bottom_layout = QHBoxLayout()
        
        file_selection_layout = QVBoxLayout()
        
        title_label = QLabel("Data Table")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        file_selection_layout.addWidget(title_label)
        
        button_row_layout = QHBoxLayout()
        self.add_input_btn = QPushButton("Generate")
        self.clear_table_btn = QPushButton("Clear")
        self.remove_all_btn = QPushButton("Remove All")
        
        button_row_layout.addWidget(self.add_input_btn)
        button_row_layout.addWidget(self.clear_table_btn)
        button_row_layout.addWidget(self.remove_all_btn)
        
        file_selection_layout.addLayout(button_row_layout)
        
        self.table_list_widget = FileListWidget()
        self.table_list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        file_selection_layout.addWidget(self.table_list_widget)
        
        table_layout = QVBoxLayout()
        self.tableWidget = TableWidget()
        table_layout.addWidget(self.tableWidget)
        
        data_selection_layout = QVBoxLayout()
        
        sel_title = QLabel("Data Selection")
        sel_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        data_selection_layout.addWidget(sel_title)
        
        x_layout = QHBoxLayout()
        x_layout.addWidget(QLabel("X:"))
        self.combo_x = QComboBox()
        x_layout.addWidget(self.combo_x)
        data_selection_layout.addLayout(x_layout)
        
        y_layout = QHBoxLayout()
        y_layout.addWidget(QLabel("Y:"))
        self.combo_y = QComboBox()
        y_layout.addWidget(self.combo_y)
        data_selection_layout.addLayout(y_layout)
        
        label_layout = QHBoxLayout()
        label_layout.addWidget(QLabel("Label:"))
        self.line_label_input = QLineEdit()
        self.line_label_input.setPlaceholderText("Custom line label (Optional)")
        label_layout.addWidget(self.line_label_input)
        data_selection_layout.addLayout(label_layout)
        
        self.new_plot_btn = QPushButton("Plot New")
        self.new_plot_btn.setMinimumHeight(30)
        data_selection_layout.addWidget(self.new_plot_btn)
        
        self.overlay_plot_btn = QPushButton("Overlay Plot")
        self.overlay_plot_btn.setMinimumHeight(30)
        data_selection_layout.addWidget(self.overlay_plot_btn)
        
        self.warning_label = QLabel("")
        self.warning_label.setStyleSheet("color: red; font-size: 12px; margin-top: 5px;")
        self.warning_label.setWordWrap(True)
        data_selection_layout.addWidget(self.warning_label)
        
        data_selection_layout.addStretch()
        
        bottom_layout.addLayout(file_selection_layout, 1)
        bottom_layout.addLayout(table_layout, 5)
        bottom_layout.addLayout(data_selection_layout, 2)
        
        return bottom_layout

    def update_table_view(self, data_store, labels):
        self.tableWidget.blockSignals(True)
        num_cols = max(len(data_store), len(labels))
        max_rows = max((len(arr) for arr in data_store), default=0)
        
        # Add buffer for manual input
        buffer_cols = 20
        buffer_rows = 100
        
        display_cols = max(num_cols + buffer_cols, 20)
        display_rows = max(max_rows + buffer_rows, 100)
        
        if num_cols == 0 and not self.table_list_widget.selectedItems():
            self.tableWidget.setRowCount(0)
            self.tableWidget.setColumnCount(0)
            self.tableWidget.blockSignals(False)
            return

        self.tableWidget.setColumnCount(display_cols)
        self.tableWidget.setRowCount(display_rows + 1)
        
        for c_idx in range(display_cols):
            label = labels[c_idx] if c_idx < len(labels) else f"Col {c_idx+1}"
            item = QTableWidgetItem(label)
            item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsEnabled)
            item.setBackground(QColor(230, 230, 230))
            font = QFont()
            font.setBold(True)
            item.setFont(font)
            self.tableWidget.setItem(0, c_idx, item)
            
        for c_idx in range(display_cols):
            col_data = data_store[c_idx] if c_idx < len(data_store) else []
            for r_idx in range(display_rows):
                if r_idx < len(col_data):
                    val = col_data[r_idx]
                    if isinstance(val, float) and np.isnan(val):
                        display_text = ""
                    else:
                        display_text = str(val)
                else:
                    display_text = ""
                    
                item = QTableWidgetItem(display_text)
                item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsEnabled)
                self.tableWidget.setItem(r_idx + 1, c_idx, item)
                
        self.tableWidget.blockSignals(False)

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
        
    def update_plot(self):
        self.sc.axes.grid(True)
        self.sc.draw()
