# pyFastPlot User Manual

pyFastPlot is a desktop plotting tool for quickly turning CSV files or pasted
spreadsheet data into clean Matplotlib figures.

## 1. Basic Workflow

1. Load a CSV file or click `Generate` to create an empty table.
2. Paste or edit data in the spreadsheet table.
3. Choose an X column and a Y column.
4. Click `Plot New` to replace the current plot, or `Overlay Plot` to add a
   line to the current plot.
5. Adjust plot options.
6. Click `Update Plot`.
7. Copy the plot to the clipboard or save it as an image file.

## 2. Data Tables

The lower-left `Data Table` panel lists loaded CSV files and generated tables.

Controls:

- `Generate`: create a blank editable table.
- `Clear`: reset the selected table.
- `Remove All`: remove all loaded/generated tables.

You can also drag a `.csv` file into the application window.

## 3. Spreadsheet Editing

The central spreadsheet supports common editing actions:

- paste tabular data with `Ctrl+V`,
- open the Text Import Wizard with `Ctrl+Shift+V`,
- delete selected cells with Delete or Backspace,
- undo with `Ctrl+Z`,
- redo with `Ctrl+Y`,
- right-click row headers to delete rows or set a row as column labels,
- right-click column headers to rename or delete columns.

Rows containing text headers can be promoted to column labels with `Set as
Column Labels`.

## 4. Data Selection

The right side of the lower panel contains:

- `X`: X-axis data source. Use `Index` when there is no X column.
- `Y`: Y-axis data source.
- `Label`: optional custom line label.
- `Plot New`: clear current plotted lines and add the selected series.
- `Overlay Plot`: add the selected series to the existing plot.

Only numeric values are plotted. Non-numeric rows and missing values are skipped.

## 5. Plot Options

The options panel is on the right side of the graph.

### Global Tab

The `Global` tab controls figure-level settings:

- figure width and height in inches,
- DPI,
- font selection,
- title and title size,
- X/Y labels,
- label and tick size,
- legend visibility, size, and location,
- manual X/Y axis limits,
- X/Y log scale.

`Auto` font mode uses a Korean-capable system font when Korean text is detected.

### Lines Tab

The `Lines` tab lists plotted lines. Each row can control:

- whether the line is visible,
- label,
- color,
- line style,
- line width,
- marker,
- marker size,
- marker fill style,
- source table.

Right-click a line row and choose `Delete Line` to remove it from the plot list.

## 6. Plot Export

Use the buttons below the plot options:

- `Update Plot`: redraw the plot using current settings.
- `Copy to Clipboard`: copy the current rendered plot image.
- `Save Plot`: save as PNG or SVG.

## 7. Logs

If the app fails to start or a runtime error occurs, check:

```text
%USERPROFILE%\.pyfastplot\pyfastplot.log
```

## 8. Packaging

Build instructions are maintained in the project README and
`packaging/README.md`. The NSIS installer does not auto-run the application
after installation, which avoids drag-and-drop issues caused by elevated
installer-launched processes.
