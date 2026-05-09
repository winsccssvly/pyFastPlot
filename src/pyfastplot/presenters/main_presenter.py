from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QMessageBox
import numpy as np

class MainPresenter:
    """
    MainPresenter acts as the mediator between the DataModel and the MainWindow (View).
    It listens to UI signals, updates the Model accordingly, and subsequently triggers UI refreshes.
    """
    def __init__(self, view, model):
        self.view = view
        self.model = model
        self._connect_signals()
        
        # Initial sync of UI settings to the plot canvas
        self.on_plot_data()

    def _connect_signals(self):
        self.view.add_input_btn.clicked.connect(self.on_add_input_table)
        self.view.remove_all_btn.clicked.connect(self.on_remove_all_tables)
        self.view.clear_table_btn.clicked.connect(self.on_clear_table)
        self.view.plot_button.clicked.connect(self.on_plot_data)
        self.view.copy_button.clicked.connect(self.on_copy_to_clipboard)
        self.view.save_button.clicked.connect(self.on_save_plot)
        
        self.view.table_list_widget.file_dropped_signal.connect(self.on_load_csv)
        self.view.table_list_widget.delete_table_signal.connect(self.on_delete_table)
        self.view.table_list_widget.rename_table_signal.connect(self.on_rename_table)
        self.view.table_list_widget.itemSelectionChanged.connect(self.on_table_selected)
        self.view.table_list_widget.reload_table_signal.connect(self.on_reload_table)
        
        self.view.tableWidget.data_pasted_signal.connect(self.on_data_pasted)
        self.view.tableWidget.delete_rows_signal.connect(self.on_delete_rows)
        self.view.tableWidget.delete_cols_signal.connect(self.on_delete_cols)
        self.view.tableWidget.clear_cells_signal.connect(self.on_clear_cells)
        self.view.tableWidget.set_as_labels_signal.connect(self.on_set_as_labels)
        self.view.tableWidget.undo_signal.connect(self.on_undo)
        self.view.tableWidget.redo_signal.connect(self.on_redo)
        
        self.view.tableWidget.model_obj.dataChanged.connect(self.on_model_data_changed)
        
        self.view.combo_x.currentTextChanged.connect(self.on_x_selection_changed)
        self.view.combo_y.currentTextChanged.connect(self.on_y_selection_changed)
        
        self.view.new_plot_btn.clicked.connect(self.on_new_plot)
        self.view.overlay_plot_btn.clicked.connect(self.on_overlay_plot)
        
        self.view.plot_options.delete_line_signal.connect(self.on_delete_cart_item)
        self.view.plot_options.line_table.cellChanged.connect(self.on_cart_label_changed)

    def _update_view_for_current_table(self):
        if self.model.current_table:
            self.view.update_selection_ui(self.model.current_table.labels)
            self.view.tableWidget.set_data_table(self.model.current_table)
        else:
            self.view.update_selection_ui([])
            self.view.tableWidget.set_data_table(None)

    def on_copy_to_clipboard(self):
        import io
        from PySide6.QtGui import QImage, QPixmap
        
        dpi = self.view.plot_options.dpi_input.value()
        buf = io.BytesIO()
        
        try:
            self.view.sc.figure.savefig(buf, format='png', dpi=dpi, bbox_inches='tight')
            buf.seek(0)
            
            image = QImage.fromData(buf.getvalue())
            pixmap = QPixmap.fromImage(image)
            
            clipboard = QApplication.clipboard()
            if clipboard is not None:
                clipboard.setPixmap(pixmap)
        except Exception as e:
            QMessageBox.warning(self.view, "Error", f"An error occurred while copying to clipboard:\n{e}")
            
    def on_save_plot(self):
        from PySide6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self.view, 
            "Save Plot", 
            "", 
            "PNG Image (*.png);;SVG Image (*.svg)"
        )
        
        if file_path:
            dpi = self.view.plot_options.dpi_input.value()
            try:
                self.view.sc.figure.savefig(file_path, dpi=dpi, bbox_inches='tight')
            except Exception as e:
                QMessageBox.critical(self.view, "Error", f"An error occurred while saving the file:\n{e}")
        
    def on_x_selection_changed(self, text):
        if text:
            self.model.set_x_selection(text)

    def on_y_selection_changed(self, text):
        if text:
            self.model.set_y_selections([text])
        
    def on_delete_cart_item(self, row):
        self.model.remove_from_cart(row)
        
    def on_cart_label_changed(self, row, col):
        if col == 1:
            item = self.view.plot_options.line_table.item(row, col)
            if item:
                self.model.update_cart_label(row, item.text())

    def on_model_data_changed(self, topLeft, bottomRight, roles):
        # If headers/labels were part of the data and they changed, update UI
        if self.model.current_table:
            # For now, labels are separate from data, but if we ever sync them, 
            # we'd call self.view.update_selection_ui(self.model.current_table.labels)
            pass

    def on_add_input_table(self):
        new_name = self.model.add_input_table()
        self.view.table_list_widget.add_table_item(new_name, is_file_based=False)
        items = self.view.table_list_widget.findItems(new_name, Qt.MatchFlag.MatchExactly)
        if items:
            self.view.table_list_widget.setCurrentItem(items[0])
        
    def on_load_csv(self, file_path):
        new_name = self.model.load_csv_file(file_path)
        self.view.table_list_widget.add_table_item(new_name, is_file_based=True)
        
        items = self.view.table_list_widget.findItems(new_name, Qt.MatchFlag.MatchExactly)
        if items:
            self.view.table_list_widget.setCurrentItem(items[0])

    def on_table_selected(self):
        selected = self.view.table_list_widget.selectedItems()
        if not selected:
            return
        table_name = selected[0].text()
        self.model.set_current_table(table_name)
        
        self._update_view_for_current_table()
        
        x_sel, y_sels = self.model.get_current_selections()
        self.view.restore_selections(x_sel, y_sels)

    def on_rename_table(self, old_name, new_name):
        self.model.rename_table(old_name, new_name)

    def on_delete_table(self, table_name):
        self.model.delete_table(table_name)
        
        items = self.view.table_list_widget.findItems(table_name, Qt.MatchFlag.MatchExactly)
        if items:
            self.view.table_list_widget.takeItem(self.view.table_list_widget.row(items[0]))
            
        if self.view.table_list_widget.count() == 0:
            self._update_view_for_current_table()

    def on_reload_table(self, table_name):
        success = self.model.reload_table(table_name)
        if success:
            if self.model.current_table_name == table_name:
                self._update_view_for_current_table()
        else:
            QMessageBox.warning(self.view, "Warning", "The original file path could not be found or the file does not exist.")

    def on_remove_all_tables(self):
        self.model.clear_all()
        self.view.table_list_widget.clear()
        self._update_view_for_current_table()

    def on_clear_table(self):
        selected = self.view.table_list_widget.selectedItems()
        if not selected:
            return
        self.model.reset_current_table()
        self._update_view_for_current_table()

    def on_data_pasted(self, start_row, start_col, parsed_data):
        success = self.model.paste_data_to_current(start_row, start_col, parsed_data)
        if not success:
            QMessageBox.warning(self.view, "Warning", "No table is selected. Please add or select a table from the left panel.")
            return
        self._update_view_for_current_table()

    def on_delete_rows(self, row_indices):
        self.model.delete_data_rows(row_indices)
        self._update_view_for_current_table()

    def on_delete_cols(self, col_indices):
        self.model.delete_data_cols(col_indices)
        self._update_view_for_current_table()

    def on_clear_cells(self, cells):
        self.model.clear_data_cells(cells)
        self._update_view_for_current_table()

    def on_set_as_labels(self, row_index):
        self.model.promote_row_to_labels(row_index)
        self._update_view_for_current_table()

    def on_undo(self):
        if self.model.undo_current_table():
            self._update_view_for_current_table()

    def on_redo(self):
        if self.model.redo_current_table():
            self._update_view_for_current_table()

    def on_new_plot(self):
        if self._add_to_cart(clear_first=True):
            self.on_plot_data()
        
    def on_overlay_plot(self):
        if self._add_to_cart(clear_first=False):
            self.on_plot_data()

    def _add_to_cart(self, clear_first):
        self.view.warning_label.setText("")
        y_col_name = self.view.combo_y.currentText()
        if not y_col_name:
            QMessageBox.warning(self.view, "Warning", "Please select the Y data to add to the cart.")
            return False
            
        custom_label = self.view.line_label_input.text().strip()
        y_label = custom_label if custom_label else y_col_name
            
        x_label = self.view.combo_x.currentText()
        x_raw = None
        if x_label != "Index":
            x_raw = self.model.get_data(x_label)
            
        table_name = self.model.current_table_name
            
        y_raw = self.model.get_data(y_col_name)
        if y_raw is None: return False
        
        if x_raw is None:
            x_raw = np.arange(len(y_raw), dtype=object)
            
        min_len = min(len(x_raw), len(y_raw))
        
        clean_x = []
        clean_y = []
        
        for i in range(min_len):
            xv = x_raw[i]
            yv = y_raw[i]
            
            if (isinstance(xv, float) and np.isnan(xv)) or (isinstance(yv, float) and np.isnan(yv)):
                continue
                
            try:
                clean_x.append(float(xv))
                clean_y.append(float(yv))
            except (ValueError, TypeError):
                # Skip metadata or non-numeric header rows
                continue
        
        if clear_first:
            self.model.line_data.clear()
            self.view.plot_options.clear_lines()
            self.view.plot_options.xlabel_input.setText(x_label)
            self.view.plot_options.ylabel_input.setText(y_label)
        
        self.model.add_to_cart(table_name, x_label, y_label, np.array(clean_x), np.array(clean_y))
        self.view.plot_options.add_cart_item(y_label, table_name)
        return True

    def on_plot_data(self):
        import matplotlib as mpl
        import warnings
        import re
        from PySide6.QtCore import Qt
        
        # Suppress fallback font warnings since they clutter the console even when fallback works
        warnings.filterwarnings("ignore", message=".*Glyph.*missing from font.*")

        # Gather text for rendering (excluding raw data) to detect language
        title_text = self.view.plot_options.title_input.text()
        final_xlabel = self.view.plot_options.xlabel_input.text()
        final_ylabel = self.view.plot_options.ylabel_input.text()
        
        displayed_texts = [title_text, final_xlabel, final_ylabel]
        for row_idx, cart_item in enumerate(self.model.line_data):
            chk_item = self.view.plot_options.line_table.item(row_idx, 0)
            if chk_item and chk_item.checkState() == Qt.CheckState.Checked:
                displayed_texts.append(cart_item["y_label"])
                
        # Check for Korean characters in text
        has_korean = any(bool(re.search(r'[가-힣ㄱ-ㅎㅏ-ㅣ]', str(t))) for t in displayed_texts if t)

        import platform
        is_mac = platform.system() == "Darwin"
        # Set OS-specific default fonts for Korean
        kor_font = 'AppleGothic' if is_mac else 'Malgun Gothic'

        font_selection = self.view.plot_options.font_family.currentText()
        actual_font = ""

        if font_selection == "Auto":
            if has_korean:
                mpl.rcParams['font.family'] = kor_font
                actual_font = f"{kor_font} (Auto-detected Korean)"
            else:
                mpl.rcParams['font.family'] = 'sans-serif'
                actual_font = "DejaVu Sans (Default)"
        elif font_selection == "DejaVu Sans (Default)":
            mpl.rcParams['font.family'] = 'sans-serif'
            actual_font = "DejaVu Sans (Default)"
        elif font_selection == "Korean (System Default)":
            mpl.rcParams['font.family'] = kor_font
            actual_font = kor_font
        else:
            mpl.rcParams['font.family'] = font_selection
            actual_font = font_selection
            
        # Display the actual font name applied to the UI
        self.view.plot_options.applied_font_label.setText(f"Applied Font: {actual_font}")
        
        mpl.rcParams['axes.unicode_minus'] = False

        # 1. Retrieve Global Settings
        fig_width = self.view.plot_options.fig_width.value()
        fig_height = self.view.plot_options.fig_height.value()
        self.view.sc.set_fig_size(fig_width, fig_height)
        
        # 2. Prepare for plotting
        self.view.clear_plot()
        
        y_labels = []
        
        # 3. Plot cart data
        for row_idx, cart_item in enumerate(self.model.line_data):
            # Verify checkbox state
            chk_item = self.view.plot_options.line_table.item(row_idx, 0)
            if chk_item and chk_item.checkState() != Qt.CheckState.Checked:
                continue
                
            y_label = cart_item["y_label"]
            y_labels.append(y_label)
            
            x_data = cart_item["x_data"]
            y_data = cart_item["y_data"]
            
            if x_data is None:
                x_data_current = np.arange(len(y_data))
            else:
                x_data_current = x_data
                
            min_len = min(len(x_data_current), len(y_data))
            x_plot = x_data_current[:min_len]
            y_plot = y_data[:min_len]
            
            line_kwargs = self.view.plot_options.get_line_options(row_idx)
            line_kwargs = {k: v for k, v in line_kwargs.items() if v != ""}
            
            self.view.draw_plot(x_plot, y_plot, y_label, **line_kwargs)
            
        # Apply Global Text Settings
        title_text = self.view.plot_options.title_input.text()
        title_size = self.view.plot_options.title_size.value()
        if title_text:
            self.view.sc.axes.set_title(title_text, fontsize=title_size)

        custom_xlabel = self.view.plot_options.xlabel_input.text()
        custom_ylabel = self.view.plot_options.ylabel_input.text()
        label_size = self.view.plot_options.label_size.value()
        
        self.view.sc.axes.set_xlabel(custom_xlabel, fontsize=label_size)
        self.view.sc.axes.set_ylabel(custom_ylabel, fontsize=label_size)
        
        tick_size = self.view.plot_options.tick_size.value()
        self.view.sc.axes.tick_params(axis='both', which='major', labelsize=tick_size)
        
        xmin = self.view.plot_options.xmin_input.text()
        xmax = self.view.plot_options.xmax_input.text()
        ymin = self.view.plot_options.ymin_input.text()
        ymax = self.view.plot_options.ymax_input.text()
        
        if xmin or xmax:
            left = float(xmin) if xmin else None
            right = float(xmax) if xmax else None
            self.view.sc.axes.set_xlim(left=left, right=right)
            
        if ymin or ymax:
            bottom = float(ymin) if ymin else None
            top = float(ymax) if ymax else None
            self.view.sc.axes.set_ylim(bottom=bottom, top=top)
        
        if self.view.plot_options.show_legend.isChecked():
            legend_size = self.view.plot_options.legend_size.value()
            legend_loc = self.view.plot_options.legend_loc.currentText()
            self.view.sc.axes.legend(fontsize=legend_size, loc=legend_loc, 
                                     framealpha=1.0, fancybox=False, frameon=True, edgecolor='black')
        else:
            leg = self.view.sc.axes.get_legend()
            if leg:
                leg.remove()
            
        self.view.sc.figure.tight_layout()
        self.view.update_plot()
