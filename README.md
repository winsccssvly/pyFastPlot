# pyFastPlot

**pyFastPlot** is a lightweight desktop data visualization tool designed for researchers and data analysts. It allows users to easily load data from CSV files or the clipboard (e.g., from Excel) and fine-tune plot options through an intuitive UI without the need for complex coding.

---

## Key Features

- **Drag & Drop Data Loading**: Import CSV files instantly by dragging them into the application.
- **Clipboard Support (Ctrl+V)**: Copy data from Excel or Google Sheets and paste it directly into the table widget.
- **Multiple Dataset Management**: Manage various datasets in a list and modify headers (labels) individually.
- **Advanced Plot Customization**:
  - **Global Settings**: Fixed canvas size, manual axis limits (X/Y), and LaTeX support for titles and axis labels.
  - **Line Settings**: Comprehensive table for managing line colors, styles, widths, and markers.
- **One-Click Export**: Copy the rendered plot to the system clipboard for immediate use in presentations or documents.

---

## Installation and Execution

### 1. Prerequisites
- Python 3.8 or higher.

### 2. Installation
Install the required packages using the following command:
```bash
pip install -r requirements.txt
```

### 3. Running the Application
Launch the application by executing `main.py` from the project root:
```bash
python main.py
```

---

## Compilation (Nuitka)

To distribute the application as a standalone executable for users without a Python environment, use **Nuitka**.

### Build Command
Run the following command from the project root:
```cmd
python -m nuitka --standalone ^
    --enable-plugins=pyside6,matplotlib,anti-bloat ^
    --noinclude-qt-plugins=webengine,pdf,network ^
    --include-data-dir=assets=assets ^
    --windows-console-mode=disable ^
    --windows-icon-from-ico=assets/data-analytics.ico ^
    --output-dir=build ^
    --output-filename=pyFastPlot ^
    src/pyfastplot/app.py
```

### Build Options
- `--standalone`: Includes all necessary libraries in the distribution.
- `--enable-plugins=pyside6,matplotlib,anti-bloat`: Handles specific dependencies and reduces bloat.
- `--noinclude-qt-plugins=webengine,pdf,network`: Excludes unused heavy Qt modules to reduce size.
- `--include-data-dir=assets=assets`: Includes icons and static resources in the bundle.
- `--windows-console-mode=disable`: Hides the console window when the GUI application starts.
- `--windows-icon-from-ico`: Sets the executable icon using the specified `.ico` file.

### Further Size Optimization (Optional)
To further reduce the size of the executable and DLLs, you can use [UPX](https://upx.github.io/):
1. Download UPX and extract it.
2. Add `--upx-binary="C:\path\to\upx.exe"` to the Nuitka command.

The compiled executable will be located in the `build/` directory.

---

## Usage Guide

1. **Load Data**: Click the `Generate` button to create an empty table for pasting data, or drag and drop a CSV file into the list.
2. **Edit Labels**: Double-click the header cells in the data table to rename labels. Changes are reflected instantly in the selection dropdowns.
3. **Select Axes**: Choose the X-axis (use `Index` for sequence numbers) and select multiple Y-axis variables from the list.
4. **Customize Plot**: Use the options panel to adjust font sizes, markers, and colors. Click `Update Plot` to apply changes.

---

## Architecture

This project follows the **Model-View-Presenter (MVP)** design pattern to ensure modularity and maintainability. For more details on the internal structure, refer to [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).