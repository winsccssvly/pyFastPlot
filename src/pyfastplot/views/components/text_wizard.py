import numpy as np
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QRadioButton, QButtonGroup,
    QLineEdit, QTableWidget, QTableWidgetItem, QPushButton, QLabel,
    QCheckBox, QPlainTextEdit
)
from PySide6.QtCore import Qt

class TextImportWizard(QDialog):
    def __init__(self, parent=None, initial_text=""):
        super().__init__(parent)
        self.setWindowTitle("Text Import Wizard")
        self.resize(700, 500)
        
        self.raw_text = initial_text
        self.parsed_data = []
        
        self.setup_ui()
        self.update_preview()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 1. Raw Text Display (Partial)
        layout.addWidget(QLabel("Clipboard Preview (First 5 lines):"))
        self.text_preview = QPlainTextEdit()
        self.text_preview.setReadOnly(True)
        self.text_preview.setMaximumHeight(100)
        lines = self.raw_text.split('\n')[:5]
        self.text_preview.setPlainText('\n'.join(lines))
        layout.addWidget(self.text_preview)
        
        # 2. Delimiter Selection
        delim_group_box = QHBoxLayout()
        delim_group_box.addWidget(QLabel("Delimiter:"))
        
        self.delim_group = QButtonGroup(self)
        
        delims = [("Tab", '\t'), ("Comma (,)", ','), ("Semicolon (;)", ';'), ("Space", ' '), ("Custom", "custom")]
        for text, val in delims:
            rb = QRadioButton(text)
            self.delim_group.addButton(rb)
            delim_group_box.addWidget(rb)
            if val == '\t': rb.setChecked(True)
            rb.toggled.connect(self.update_preview)
            
        self.custom_delim_input = QLineEdit()
        self.custom_delim_input.setPlaceholderText("Custom char")
        self.custom_delim_input.setMaximumWidth(80)
        self.custom_delim_input.textChanged.connect(self.update_preview)
        delim_group_box.addWidget(self.custom_delim_input)
        
        layout.addLayout(delim_group_box)
        
        # 3. Options
        self.consecutive_as_one = QCheckBox("Treat consecutive delimiters as one")
        self.consecutive_as_one.stateChanged.connect(self.update_preview)
        layout.addWidget(self.consecutive_as_one)
        
        # 4. Preview Table
        layout.addWidget(QLabel("Data Preview:"))
        self.preview_table = QTableWidget()
        self.preview_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.preview_table)
        
        # 5. Buttons
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("Apply to Table")
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.ok_btn)
        layout.addLayout(btn_layout)

    def get_selected_delimiter(self):
        btn = self.delim_group.checkedButton()
        if not btn: return '\t'
        
        text = btn.text()
        if text == "Tab": return '\t'
        if text == "Comma (,)": return ','
        if text == "Semicolon (;)": return ';'
        if text == "Space": return ' '
        if text == "Custom": return self.custom_delim_input.text()
        return '\t'

    def update_preview(self):
        delim = self.get_selected_delimiter()
        if not delim: 
            self.parsed_data = [[self.raw_text]]
        else:
            rows = self.raw_text.strip('\n').split('\n')
            self.parsed_data = []
            for r in rows:
                if self.consecutive_as_one.isChecked():
                    import re
                    # Escape delimiter for regex if it's special
                    escaped_delim = re.escape(delim)
                    parts = re.split(f"{escaped_delim}+", r)
                else:
                    parts = r.split(delim)
                
                row_vals = []
                for p in parts:
                    p = p.strip()
                    try:
                        row_vals.append(float(p))
                    except ValueError:
                        row_vals.append(p if p else np.nan)
                self.parsed_data.append(row_vals)

        # Update Table Widget
        self.preview_table.clear()
        if not self.parsed_data:
            self.preview_table.setRowCount(0)
            self.preview_table.setColumnCount(0)
            return

        row_count = len(self.parsed_data)
        col_count = max(len(r) for r in self.parsed_data)
        
        self.preview_table.setRowCount(min(row_count, 50)) # Show up to 50 for performance
        self.preview_table.setColumnCount(col_count)
        
        for r_idx in range(min(row_count, 50)):
            row = self.parsed_data[r_idx]
            for c_idx, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                self.preview_table.setItem(r_idx, c_idx, item)

    def get_data(self):
        return self.parsed_data
