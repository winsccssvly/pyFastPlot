import os
import numpy as np

class DataTable:
    def __init__(self, name):
        self.name = name
        self.data = np.full((100, 20), np.nan, dtype=object) # Initial buffer
        self.labels = [f"Col {i+1}" for i in range(20)]
        self.x_sel = "Col 1"
        self.y_sels = []
        self.file_path = None

    def delete_rows(self, row_indices):
        self.data = np.delete(self.data, row_indices, axis=0)

    def delete_cols(self, col_indices):
        self.data = np.delete(self.data, col_indices, axis=1)
        for idx in sorted(col_indices, reverse=True):
            if idx < len(self.labels):
                self.labels.pop(idx)

    def clear_cells(self, cells):
        for r, c in cells:
            if r < self.data.shape[0] and c < self.data.shape[1]:
                self.data[r, c] = np.nan

    def ensure_capacity(self, num_rows, num_cols):
        curr_rows, curr_cols = self.data.shape
        if num_rows > curr_rows or num_cols > curr_cols:
            new_rows = max(num_rows, curr_rows)
            new_cols = max(num_cols, curr_cols)
            new_data = np.full((new_rows, new_cols), np.nan, dtype=object)
            new_data[:curr_rows, :curr_cols] = self.data
            self.data = new_data
            
            while len(self.labels) < new_cols:
                self.labels.append(f"Col {len(self.labels)+1}")

    def update_cell(self, row, col, value):
        self.ensure_capacity(row + 1, col + 1)
        self.data[row, col] = value

    def paste_data(self, start_row, start_col, parsed_data):
        if not parsed_data: return
        max_r = start_row + len(parsed_data)
        max_c = start_col + max((len(r) for r in parsed_data), default=0)
        self.ensure_capacity(max_r, max_c)
        
        for r_offset, row_data in enumerate(parsed_data):
            for c_offset, val in enumerate(row_data):
                self.data[start_row + r_offset, start_col + c_offset] = val

class DataModel:
    """
    DataModel manages the business logic and core data of the application.
    It stores parsed data, labels, handles CSV reading and clipboard data appending,
    while remaining completely decoupled from the UI.
    """
    def __init__(self):
        self.all_tables = {}
        self.input_table_count = 0
        
        self.current_table_name = None
        self.line_data = []

    def clear_all(self):
        self.all_tables.clear()
        self.input_table_count = 0
        self.current_table_name = None
        self.line_data = []

    def delete_table(self, table_name):
        if table_name in self.all_tables:
            del self.all_tables[table_name]
        if self.current_table_name == table_name:
            self.current_table_name = None

    def rename_table(self, old_name, new_name):
        if old_name in self.all_tables and new_name not in self.all_tables:
            table = self.all_tables.pop(old_name)
            table.name = new_name
            self.all_tables[new_name] = table
            if self.current_table_name == old_name:
                self.current_table_name = new_name
            
            for item in self.line_data:
                if item["table_name"] == old_name:
                    item["table_name"] = new_name
            return True
        return False

    def reset_current_table(self):
        if self.current_table_name:
            self.all_tables[self.current_table_name] = DataTable(self.current_table_name)

    def add_input_table(self):
        self.input_table_count += 1
        table_name = f"Input Table {self.input_table_count}"
        self.all_tables[table_name] = DataTable(table_name)
        return table_name
        
    def _parse_csv_to_table(self, table, file_path):
        try:
            import csv
            parsed_data = []
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    row_vals = []
                    for val in row:
                        val = val.strip()
                        try:
                            # Try converting to float for internal use, but keep as string if it fails
                            row_vals.append(float(val))
                        except ValueError:
                            row_vals.append(val if val else np.nan)
                    parsed_data.append(row_vals)
                
            table.paste_data(0, 0, parsed_data)
            
            # For complex CSVs, we'll just use the default labels (Col 1, Col 2...)
            # The user can rename them or we can implement a logic to find the header row later.
            num_cols = table.data.shape[1]
            table.labels = [f"Col {i+1}" for i in range(num_cols)]
                        
        except Exception as e:
            print(f"Failed to load CSV: {e}")

    def load_csv_file(self, file_path):
        file_name = os.path.basename(file_path)
        base_name, ext = os.path.splitext(file_name)
        count = 1
        new_name = file_name
        while new_name in self.all_tables:
            new_name = f"{base_name}_{count}{ext}"
            count += 1
            
        table = DataTable(new_name)
        table.file_path = file_path
        self._parse_csv_to_table(table, file_path)
            
        self.all_tables[new_name] = table
        return new_name

    def reload_table(self, table_name):
        if table_name in self.all_tables:
            table = self.all_tables[table_name]
            if table.file_path and os.path.exists(table.file_path):
                table.data = []
                table.labels = []
                self._parse_csv_to_table(table, table.file_path)
                return True
        return False

    def set_current_table(self, table_name):
        self.current_table_name = table_name

    @property
    def current_table(self):
        if self.current_table_name:
            return self.all_tables.get(self.current_table_name)
        return None

    def update_label(self, col_index, new_label):
        table = self.current_table
        if table:
            while col_index >= len(table.labels):
                table.labels.append(f"Col {len(table.labels)+1}")
                table.data.append(np.array([], dtype=object))
            table.labels[col_index] = new_label

    def update_data_cell(self, row, col, value):
        table = self.current_table
        if table:
            table.update_cell(row, col, value)

    def paste_data_to_current(self, start_row, start_col, parsed_data):
        table = self.current_table
        if not table:
            return False
        table.paste_data(start_row, start_col, parsed_data)
        return True

    def get_data(self, label_name):
        table = self.current_table
        if table:
            try:
                # Find the index of the label
                idx = table.labels.index(label_name)
                return table.data[:, idx]
            except ValueError:
                return None
        return None

    def set_x_selection(self, x_sel):
        if self.current_table:
            self.current_table.x_sel = x_sel

    def set_y_selections(self, y_sels):
        if self.current_table:
            self.current_table.y_sels = y_sels

    def get_current_selections(self):
        if self.current_table:
            return self.current_table.x_sel, self.current_table.y_sels
        return "Col 1", []

    def delete_data_rows(self, row_indices):
        if self.current_table:
            self.current_table.delete_rows(row_indices)

    def delete_data_cols(self, col_indices):
        if self.current_table:
            self.current_table.delete_cols(col_indices)

    def clear_data_cells(self, cells):
        if self.current_table:
            self.current_table.clear_cells(cells)

    def promote_row_to_labels(self, row_index):
        table = self.current_table
        if not table or row_index >= table.data.shape[0]:
            return
        
        new_labels = []
        for c in range(table.data.shape[1]):
            val = table.data[row_index, c]
            label = str(val).strip() if (isinstance(val, str) or not np.isnan(val)) else f"Col {c+1}"
            new_labels.append(label)
        
        table.labels = new_labels
        table.delete_rows([row_index])

    def add_to_cart(self, table_name, x_label, y_label, x_data, y_data):
        self.line_data.append({
            "table_name": table_name,
            "x_label": x_label,
            "y_label": y_label,
            "x_data": x_data,
            "y_data": y_data
        })
        
    def remove_from_cart(self, index):
        if 0 <= index < len(self.line_data):
            self.line_data.pop(index)
            
    def update_cart_label(self, index, new_label):
        if 0 <= index < len(self.line_data):
            self.line_data[index]["y_label"] = new_label
