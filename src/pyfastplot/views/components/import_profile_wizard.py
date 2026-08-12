"""Dialog for testing and saving text-file import profiles."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ...services.import_profiles import (
    UNSUPPORTED_BINARY_EXTENSIONS,
    ImportProfile,
    conflicting_extensions,
    normalize_extension,
    preview_profile_data,
)


class ImportProfileWizard(QDialog):
    """Create a reusable import profile while inspecting a sample file."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("New Text Import Format")
        self.resize(760, 520)
        self.setAcceptDrops(True)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.sample_path = QLineEdit()
        browse = QPushButton("Browse...")
        browse.clicked.connect(self._select_sample)
        sample_layout = QHBoxLayout()
        sample_layout.addWidget(self.sample_path)
        sample_layout.addWidget(browse)
        form.addRow("Sample file", sample_layout)
        self.name_input = QLineEdit()
        form.addRow("Format name", self.name_input)
        self.extensions_input = QLineEdit()
        self.extensions_input.setPlaceholderText(".dat, .exp")
        form.addRow("Extensions", self.extensions_input)
        self.delimiter = QComboBox()
        self.delimiter.addItems(["comma", "tab", "semicolon", "space"])
        form.addRow("Delimiter", self.delimiter)
        self.custom_delimiter = QLineEdit()
        self.custom_delimiter.setPlaceholderText("Optional, e.g. | or ::")
        form.addRow("Custom delimiter", self.custom_delimiter)
        self.encoding = QComboBox()
        self.encoding.addItems(["utf-8", "cp949", "latin-1"])
        form.addRow("Encoding", self.encoding)
        self.header_row = QSpinBox()
        self.header_row.setMinimum(0)
        form.addRow("Header row (first = 0)", self.header_row)
        self.no_header = QCheckBox("No header (use Col 1, Col 2, ...)")
        self.no_header.toggled.connect(self.header_row.setDisabled)
        form.addRow("Column names", self.no_header)
        self.data_start_row = QSpinBox()
        self.data_start_row.setMinimum(0)
        self.data_start_row.setValue(1)
        form.addRow("Data start row", self.data_start_row)
        layout.addLayout(form)
        self.preview = QTableWidget()
        self.preview.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.preview)
        buttons = QHBoxLayout()
        test = QPushButton("Test / refresh preview")
        test.clicked.connect(self.refresh_preview)
        save = QPushButton("Save format")
        save.clicked.connect(self._validate_and_accept)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        buttons.addWidget(test)
        buttons.addStretch()
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        layout.addLayout(buttons)

    def _select_sample(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select a sample text file", "")
        if path:
            self._set_sample_file(path)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Accept a local file dragged onto the wizard."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        """Use the first dropped local file as the format sample."""
        paths = [url.toLocalFile() for url in event.mimeData().urls()]
        if sample_path := next((path for path in paths if path), ""):
            self._set_sample_file(sample_path)
            event.acceptProposedAction()
        else:
            event.ignore()

    def _set_sample_file(self, path: str) -> None:
        self.sample_path.setText(path)
        if not self.name_input.text():
            suffix = Path(path).suffix.lstrip(".").upper()
            self.name_input.setText(f"{suffix} format")
        if not self.extensions_input.text().strip():
            self.extensions_input.setText(Path(path).suffix)
        self.refresh_preview()

    def profile(self) -> ImportProfile:
        extensions = tuple(
            extension.strip()
            for extension in self.extensions_input.text().split(",")
            if extension.strip()
        )
        return ImportProfile(
            name=self.name_input.text().strip(),
            extensions=extensions,
            delimiter=(
                self.custom_delimiter.text()
                if self.custom_delimiter.text()
                else self.delimiter.currentText()
            ),
            encoding=self.encoding.currentText(),
            header_row=None if self.no_header.isChecked() else self.header_row.value(),
            data_start_row=self.data_start_row.value(),
        )

    def refresh_preview(self) -> None:
        path = self.sample_path.text().strip()
        if not path:
            return
        try:
            labels, rows = preview_profile_data(path, self.profile())
        except (OSError, UnicodeError, ValueError) as error:
            QMessageBox.warning(self, "Cannot read sample", str(error))
            return
        self.preview.setColumnCount(len(labels))
        self.preview.setHorizontalHeaderLabels(labels)
        self.preview.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                self.preview.setItem(row_index, column_index, item)

    def _validate_and_accept(self) -> None:
        profile = self.profile()
        if not profile.name or not profile.extensions:
            QMessageBox.warning(
                self,
                "Missing settings",
                "Enter a format name and extension.",
            )
            return
        extensions = tuple(normalize_extension(value) for value in profile.extensions)
        if any(extension in UNSUPPORTED_BINARY_EXTENSIONS for extension in extensions):
            QMessageBox.warning(
                self,
                "Unsupported extension",
                "Excel and other binary spreadsheet formats cannot be added "
                "as text formats.",
            )
            return
        duplicates = conflicting_extensions(extensions)
        if duplicates:
            QMessageBox.warning(
                self,
                "Extension already in use",
                "These extensions are already supported: "
                f"{', '.join(sorted(duplicates))}",
            )
            return
        self.accept()
