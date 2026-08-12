from PySide6.QtCore import QEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .components.table import TableWidget


class TableWindow(QMainWindow):
    """
    A separate window to display and edit a DataTable.
    """

    def __init__(self, table_name, data_table, presenter, parent=None):
        super().__init__(parent)
        self.table_name = table_name
        self.presenter = presenter
        self.setWindowTitle(f"Table: {table_name}")
        self.resize(800, 600)

        central = QWidget()
        layout = QVBoxLayout(central)
        self.table_widget = TableWidget()
        self.table_widget.set_data_table(data_table)
        layout.addWidget(self.table_widget)

        button_layout = QHBoxLayout()
        copy_all_btn = QPushButton("Copy All")
        export_btn = QPushButton("Export to CSV")
        button_layout.addStretch()
        button_layout.addWidget(copy_all_btn)
        button_layout.addWidget(export_btn)
        layout.addLayout(button_layout)
        self.setCentralWidget(central)

        copy_all_btn.clicked.connect(self.table_widget.copy_all_data)
        export_btn.clicked.connect(
            lambda: self.table_widget.export_all_data_csv(f"{table_name}.csv")
        )

        # Connect table interactions to presenter slots
        self.table_widget.data_pasted_signal.connect(self.presenter.on_data_pasted)
        self.table_widget.delete_rows_signal.connect(self.presenter.on_delete_rows)
        self.table_widget.delete_cols_signal.connect(self.presenter.on_delete_cols)
        self.table_widget.clear_cells_signal.connect(self.presenter.on_clear_cells)
        self.table_widget.set_as_labels_signal.connect(self.presenter.on_set_as_labels)
        self.table_widget.rename_col_signal.connect(self.presenter.on_rename_column)
        self.table_widget.undo_signal.connect(self.presenter.on_undo)
        self.table_widget.redo_signal.connect(self.presenter.on_redo)

    def changeEvent(self, event):
        if event.type() == QEvent.Type.ActivationChange and self.isActiveWindow():
            self.presenter.set_active_table_from_window(self.table_name)
        super().changeEvent(event)

    def closeEvent(self, event):
        self.presenter.on_window_closed(self.table_name)
        super().closeEvent(event)
