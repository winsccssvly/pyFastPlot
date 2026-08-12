"""Dialog for inspecting and removing saved text import formats."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ...services.import_profiles import (
    delete_profile,
    load_profile_records,
)

PROFILE_PATH_ROLE = Qt.ItemDataRole.UserRole


class ImportProfileManager(QDialog):
    """List saved import formats and allow unwanted formats to be removed."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Manage Text Import Formats")
        self.resize(620, 320)
        self._build_ui()
        self.refresh_profiles()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        self.profile_table = QTableWidget(0, 3)
        self.profile_table.setHorizontalHeaderLabels(
            ["Format", "Extensions", "Delimiter"]
        )
        self.profile_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.profile_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.profile_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.profile_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.profile_table)
        buttons = QHBoxLayout()
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_profiles)
        delete_button = QPushButton("Delete selected")
        delete_button.clicked.connect(self.delete_selected_profile)
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        buttons.addWidget(refresh_button)
        buttons.addWidget(delete_button)
        buttons.addStretch()
        buttons.addWidget(close_button)
        layout.addLayout(buttons)

    def refresh_profiles(self) -> None:
        """Reload the profile list from the user configuration directory."""
        records = load_profile_records()
        self.profile_table.setRowCount(len(records))
        for row, (path, profile) in enumerate(records):
            name = QTableWidgetItem(profile.name)
            name.setData(PROFILE_PATH_ROLE, str(path))
            self.profile_table.setItem(row, 0, name)
            extensions = QTableWidgetItem(", ".join(profile.extensions))
            self.profile_table.setItem(row, 1, extensions)
            self.profile_table.setItem(row, 2, QTableWidgetItem(profile.delimiter))

    def delete_selected_profile(self) -> None:
        """Delete the selected saved profile after explicit confirmation."""
        row = self.profile_table.currentRow()
        item = self.profile_table.item(row, 0)
        if item is None:
            QMessageBox.information(self, "Select a format", "Select a format first.")
            return
        answer = QMessageBox.question(
            self,
            "Delete text import format",
            f"Delete '{item.text()}'?",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        path_value = item.data(PROFILE_PATH_ROLE)
        if not isinstance(path_value, str):
            return
        try:
            delete_profile(Path(path_value))
        except (OSError, ValueError) as error:
            QMessageBox.warning(self, "Cannot delete format", str(error))
            return
        self.refresh_profiles()
