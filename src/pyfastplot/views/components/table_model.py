import numpy as np
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor, QFont

DEFAULT_PARENT_INDEX = QModelIndex()


class DataTableModel(QAbstractTableModel):
    """
    A high-performance virtualized table model for displaying large datasets.
    It directly references the data stored in the DataTable object.
    """

    def __init__(self, data_table=None):
        super().__init__()
        self.data_table = data_table
        self.header_font = QFont()
        self.header_font.setBold(True)

    def set_table(self, data_table):
        self.beginResetModel()
        self.data_table = data_table
        self.endResetModel()

    def rowCount(self, parent=DEFAULT_PARENT_INDEX):
        if not self.data_table:
            return 0
        return self.data_table.data.shape[0]

    def columnCount(self, parent=DEFAULT_PARENT_INDEX):
        if not self.data_table:
            return 0
        return self.data_table.data.shape[1]

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not self.data_table:
            return None

        row = index.row()
        col = index.column()

        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            try:
                val = self.data_table.data[row, col]
                if isinstance(val, float) and np.isnan(val):
                    return ""
                return str(val)
            except IndexError:
                return ""

        return None

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if (
            not self.data_table
            or not index.isValid()
            or role != Qt.ItemDataRole.EditRole
        ):
            return False

        row = index.row()
        col = index.column()

        try:
            # Try to convert to float if possible, otherwise keep as string
            try:
                val = float(value)
            except ValueError:
                val = value

            self.data_table.update_cell(row, col, val)
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])
            return True
        except Exception:
            return False

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if not self.data_table:
            return None

        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                if section < len(self.data_table.labels):
                    return self.data_table.labels[section]
                return f"Col {section + 1}"
            else:
                return str(section + 1)

        if (
            role == Qt.ItemDataRole.FontRole
            and orientation == Qt.Orientation.Horizontal
        ):
            return self.header_font

        if (
            role == Qt.ItemDataRole.BackgroundRole
            and orientation == Qt.Orientation.Horizontal
        ):
            return QColor(240, 240, 240)

        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.ItemIsEnabled
        return (
            super().flags(index)
            | Qt.ItemFlag.ItemIsEditable
            | Qt.ItemFlag.ItemIsSelectable
        )
