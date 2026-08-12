from pathlib import Path

import numpy as np

from ..services.import_profiles import (
    ImportProfile,
    is_supported_text_path,
    profile_for_path,
    read_profile_data,
    save_profile,
)
from .analysis_models import AnalysisSeries


class UnsupportedFileFormatError(ValueError):
    """Raised when a file does not have an enabled text import format."""


def _safe_float(value: object) -> float | None:
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def _default_time_label(labels: list[str]) -> str:
    for label in labels:
        normalized = label.strip().lower()
        if normalized in {"time", "time (seconds)", "time(s)", "t"}:
            return label
    for label in labels:
        if "time" in label.strip().lower():
            return label
    return labels[0] if labels else ""


def _motion_label_parts(header: object, fallback_motion: object) -> tuple[str, str]:
    text = str(header).strip()
    parts = text.replace("_", " ").split()
    if len(parts) >= 2 and parts[0].lower() in {"position", "rotation"}:
        return parts[0], " ".join(parts[1:])
    return str(fallback_motion).strip() or "Motion", text


def _motion_series_label(name: object, motion: object, mode: object) -> str:
    name_text = str(name).strip().replace(" ", "")
    motion_text = str(motion).strip().replace(" ", "")
    mode_text = str(mode).strip().replace(" ", "")
    return f"{name_text}_{motion_text}{mode_text}"


def _row_value(row: list, index: int) -> object:
    return row[index] if index < len(row) else np.nan


def _find_motion_frame_header(parsed_data: list[list]) -> int | None:
    for row_idx, row in enumerate(parsed_data):
        first = str(_row_value(row, 0)).strip().lower()
        second = str(_row_value(row, 1)).strip().lower()
        if first == "frame" and second == "time (seconds)":
            return row_idx
    return None


def _find_named_metadata_row(rows: list[list], name: str) -> list | None:
    target = name.lower()
    for row in rows:
        if str(_row_value(row, 1)).strip().lower() == target:
            return row
    return None


def _find_motion_kind_row(rows: list[list]) -> list | None:
    candidates = {"rotation", "position"}
    for row in rows:
        values = {str(value).strip().lower() for value in row}
        if values & candidates:
            return row
    return None


class DataTable:
    def __init__(self, name: str, column_count: int = 20) -> None:
        self.name: str = name
        column_count = max(1, int(column_count))
        self.data = np.full((100, column_count), np.nan, dtype=object)
        self.labels = [f"Col {i + 1}" for i in range(column_count)]
        self.x_sel = "Col 1"
        self.y_sels = []
        self.file_path: str | None = None
        self.data_type = "generic"
        self._undo_stack = []
        self._redo_stack = []

    def save_state(self):
        state = (self.data.copy(), list(self.labels))
        self._undo_stack.append(state)
        if len(self._undo_stack) > 20:  # Keep last 20 states
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def undo(self):
        if self._undo_stack:
            current_state = (self.data.copy(), list(self.labels))
            self._redo_stack.append(current_state)
            self.data, self.labels = self._undo_stack.pop()
            return True
        return False

    def redo(self):
        if self._redo_stack:
            current_state = (self.data.copy(), list(self.labels))
            self._undo_stack.append(current_state)
            self.data, self.labels = self._redo_stack.pop()
            return True
        return False

    def delete_rows(self, row_indices):
        self.save_state()
        self.data = np.delete(self.data, row_indices, axis=0)

    def delete_cols(self, col_indices):
        self.save_state()
        self.data = np.delete(self.data, col_indices, axis=1)
        for idx in sorted(col_indices, reverse=True):
            if idx < len(self.labels):
                self.labels.pop(idx)

    def clear_cells(self, cells):
        self.save_state()
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
                self.labels.append(f"Col {len(self.labels) + 1}")

    def update_cell(self, row, col, value):
        self.save_state()
        self.ensure_capacity(row + 1, col + 1)
        self.data[row, col] = value

    def paste_data(self, start_row, start_col, parsed_data):
        if not parsed_data:
            return
        self.save_state()
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

            for series_index, item in enumerate(self.line_data):
                if item.source_table == old_name:
                    renamed = AnalysisSeries(
                        id=item.id.replace(old_name, new_name, 1),
                        source_table=new_name,
                        x_label=item.x_label,
                        y_label=item.y_label,
                        x_data=item.x_data,
                        y_data=item.y_data,
                        data_type=item.data_type,
                        x_unit=item.x_unit,
                        y_unit=item.y_unit,
                        color=item.color,
                        visible=item.visible,
                    )
                    self.line_data[series_index] = renamed
            return True
        return False

    def reset_current_table(self):
        if self.current_table_name:
            self.all_tables[self.current_table_name] = DataTable(
                self.current_table_name
            )

    def add_input_table(self, column_count=20):
        self.input_table_count += 1
        table_name = f"Input Table {self.input_table_count}"
        self.all_tables[table_name] = DataTable(table_name, column_count)
        return table_name

    def _parse_csv_to_table(self, table, file_path):
        import csv

        parsed_data = []
        with open(file_path, encoding="utf-8") as file:
            reader = csv.reader(file)
            for row in reader:
                row_vals = []
                for val in row:
                    val = val.strip()
                    try:
                        row_vals.append(float(val))
                    except ValueError:
                        row_vals.append(val if val else np.nan)
                parsed_data.append(row_vals)
        if not parsed_data:
            raise ValueError("The file does not contain any readable rows.")
        if self._try_parse_motion_csv(table, parsed_data):
            return
        max_r = len(parsed_data)
        max_c = max((len(row) for row in parsed_data), default=0)
        if max_c == 0:
            raise ValueError("The file does not contain any readable columns.")
        table.ensure_capacity(max_r, max_c)
        for r_offset, row_data in enumerate(parsed_data):
            for c_offset, val in enumerate(row_data):
                table.data[r_offset, c_offset] = val
        table.labels = [f"Col {i + 1}" for i in range(max_c)]
        table._undo_stack.clear()
        table._redo_stack.clear()

    def _try_parse_motion_csv(self, table: DataTable, parsed_data: list[list]) -> bool:
        if not parsed_data:
            return False

        if self._try_parse_multiline_motion_csv(table, parsed_data):
            return True

        headers = [str(value).strip() for value in parsed_data[0]]
        header_map = {header.lower(): idx for idx, header in enumerate(headers)}
        required = ["frame", "time (seconds)", "type", "name", "id"]
        if not all(header in header_map for header in required):
            return False

        time_idx = header_map["time (seconds)"]
        type_idx = header_map["type"]
        name_idx = header_map["name"]
        metadata_indices = {header_map[header] for header in required}
        component_indices = [
            idx
            for idx, header in enumerate(headers)
            if idx not in metadata_indices and str(header).strip()
        ]
        if not component_indices:
            return False

        times = []
        rows_by_time = {}
        labels = ["Time (Seconds)"]
        label_set = set(labels)
        for row in parsed_data[1:]:
            if len(row) <= max(time_idx, type_idx, name_idx):
                continue
            time_value = _safe_float(row[time_idx])
            if time_value is None:
                continue
            if time_value not in rows_by_time:
                rows_by_time[time_value] = {"Time (Seconds)": time_value}
                times.append(time_value)

            name = str(row[name_idx]).strip()
            motion_type = str(row[type_idx]).strip()
            for col_idx in component_indices:
                if col_idx >= len(row):
                    continue
                value = _safe_float(row[col_idx])
                if value is None:
                    continue
                motion, mode = _motion_label_parts(headers[col_idx], motion_type)
                label = _motion_series_label(name, motion, mode)
                rows_by_time[time_value][label] = value
                if label not in label_set:
                    label_set.add(label)
                    labels.append(label)

        if len(labels) == 1 or not times:
            return False

        table.data = np.full((len(times), len(labels)), np.nan, dtype=object)
        table.labels = labels
        for row_idx, time_value in enumerate(times):
            row_data = rows_by_time[time_value]
            for col_idx, label in enumerate(labels):
                table.data[row_idx, col_idx] = row_data.get(label, np.nan)
        table.x_sel = "Time (Seconds)"
        table.y_sels = []
        table.data_type = "motion"
        table._undo_stack.clear()
        table._redo_stack.clear()
        return True

    def _try_parse_multiline_motion_csv(
        self, table: DataTable, parsed_data: list[list]
    ) -> bool:
        header_idx = _find_motion_frame_header(parsed_data)
        if header_idx is None:
            return False

        headers = [str(value).strip() for value in parsed_data[header_idx]]
        name_row = _find_named_metadata_row(parsed_data[:header_idx], "Name")
        type_row = _find_named_metadata_row(parsed_data[:header_idx], "Type")
        motion_row = _find_motion_kind_row(parsed_data[:header_idx])
        if name_row is None or type_row is None or motion_row is None:
            return False

        component_indices = [
            idx for idx, header in enumerate(headers) if idx >= 2 and header
        ]
        if not component_indices:
            return False

        labels = ["Time (Seconds)"]
        label_set = set(labels)
        rows = []
        for row in parsed_data[header_idx + 1 :]:
            if len(row) < 2:
                continue
            time_value = _safe_float(row[1])
            if time_value is None:
                continue
            row_data = {"Time (Seconds)": time_value}
            for col_idx in component_indices:
                value = _safe_float(_row_value(row, col_idx))
                if value is None:
                    continue
                name = str(_row_value(name_row, col_idx)).strip()
                motion = str(_row_value(motion_row, col_idx)).strip()
                mode = headers[col_idx]
                label = _motion_series_label(name, motion, mode)
                row_data[label] = value
                if label not in label_set:
                    label_set.add(label)
                    labels.append(label)
            rows.append(row_data)

        if len(labels) == 1 or not rows:
            return False

        table.data = np.full((len(rows), len(labels)), np.nan, dtype=object)
        table.labels = labels
        for row_idx, row_data in enumerate(rows):
            for col_idx, label in enumerate(labels):
                table.data[row_idx, col_idx] = row_data.get(label, np.nan)
        table.x_sel = "Time (Seconds)"
        table.y_sels = []
        table.data_type = "motion"
        table._undo_stack.clear()
        table._redo_stack.clear()
        return True

    def _parse_wdt_to_table(self, table, file_path):
        try:
            parsed_data = []
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            if len(lines) <= 69:
                raise ValueError("The WDT file is missing its expected header row.")

            # Header line: index 69 (70th row)
            header_line = lines[69].strip()
            if header_line.endswith(":"):
                header_line = header_line[:-1]

            # Remove [msec] and other unit patterns
            header_line = header_line.replace("[msec]", "")

            headers = [h.strip() for h in header_line.split("\t")]

            # Read values from index 70 (71st row) onwards
            for line in lines[70:]:
                line = line.strip()
                if not line:
                    continue
                parts = line.split("\t")
                row_vals = []
                for val in parts:
                    val = val.strip()
                    try:
                        row_vals.append(float(val))
                    except ValueError:
                        row_vals.append(val if val else np.nan)
                if row_vals:
                    parsed_data.append(row_vals)

            max_r = len(parsed_data)
            max_c = max((len(r) for r in parsed_data), default=0)
            if max_r == 0 or max_c == 0:
                raise ValueError("The WDT file does not contain any readable data.")
            table.ensure_capacity(max_r, max_c)
            for r_offset, row_data in enumerate(parsed_data):
                for c_offset, val in enumerate(row_data):
                    table.data[r_offset, c_offset] = val

            table.labels = [f"Col {i + 1}" for i in range(max_c)]
            for i, h in enumerate(headers):
                if i < len(table.labels):
                    table.labels[i] = h

            table.x_sel = _default_time_label(table.labels)
            table.y_sels = []
            table._undo_stack.clear()
            table._redo_stack.clear()
            table.data_type = "wave_elevation"
        except (OSError, UnicodeError, ValueError) as error:
            raise ValueError(f"Could not parse WDT data: {error}") from error

    def _parse_profile_to_table(
        self, table: DataTable, file_path: str, profile: ImportProfile
    ) -> None:
        """Load a user-configured delimited text file into a table."""
        labels, parsed_data = read_profile_data(file_path, profile)
        max_rows = len(parsed_data)
        max_columns = max((len(row) for row in parsed_data), default=len(labels))
        if max_rows == 0 or max_columns == 0:
            raise ValueError(
                f"The file has no readable data for the '{profile.name}' format."
            )
        table.ensure_capacity(max_rows, max_columns)
        for row_index, row in enumerate(parsed_data):
            for column_index, value in enumerate(row):
                table.data[row_index, column_index] = value
        table.labels = labels + [
            f"Col {index}" for index in range(len(labels) + 1, max_columns + 1)
        ]
        if profile.x_column in table.labels:
            table.x_sel = profile.x_column
        else:
            table.x_sel = _default_time_label(table.labels)
        table.y_sels = []
        table.data_type = profile.data_type
        table._undo_stack.clear()
        table._redo_stack.clear()

    def save_import_profile(self, profile: ImportProfile) -> Path:
        """Save a reusable user-defined text file reader."""
        return save_profile(profile)

    def load_csv_file(self, file_path):
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(path)
        if not is_supported_text_path(path):
            raise UnsupportedFileFormatError(
                f"'{path.suffix or '(no extension)'}' is not an enabled text format."
            )
        file_name = path.name
        base_name, ext = path.stem, path.suffix
        count = 1
        new_name = file_name
        while new_name in self.all_tables:
            new_name = f"{base_name}_{count}{ext}"
            count += 1

        table = DataTable(new_name)
        table.file_path = str(path)
        if ext.lower() == ".wdt":
            self._parse_wdt_to_table(table, file_path)
        elif profile := profile_for_path(path):
            self._parse_profile_to_table(table, str(path), profile)
        else:
            self._parse_csv_to_table(table, file_path)

        self.all_tables[new_name] = table
        return new_name

    def reload_table(self, table_name):
        if table_name in self.all_tables:
            table = self.all_tables[table_name]
            if table.file_path and Path(table.file_path).exists():
                table.data = np.full((100, 20), np.nan, dtype=object)
                table.labels = []
                table.data_type = "generic"
                ext = Path(table.file_path).suffix
                if ext.lower() == ".wdt":
                    self._parse_wdt_to_table(table, table.file_path)
                elif profile := profile_for_path(table.file_path):
                    self._parse_profile_to_table(table, table.file_path, profile)
                else:
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
            table.ensure_capacity(table.data.shape[0], col_index + 1)
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

    def undo_current_table(self):
        if self.current_table:
            return self.current_table.undo()
        return False

    def redo_current_table(self):
        if self.current_table:
            return self.current_table.redo()
        return False

    def promote_row_to_labels(self, row_index):
        table = self.current_table
        if not table or row_index >= table.data.shape[0]:
            return

        table.save_state()
        new_labels = []
        for c in range(table.data.shape[1]):
            val = table.data[row_index, c]
            label = (
                str(val).strip()
                if (isinstance(val, str) or not np.isnan(val))
                else f"Col {c + 1}"
            )
            new_labels.append(label)

        table.labels = new_labels
        table.data = np.delete(table.data, [row_index], axis=0)

    def add_to_cart(self, table_name, x_label, y_label, x_data, y_data):
        series_id = f"{table_name}:{x_label}:{y_label}:{len(self.line_data) + 1}"
        data_type = "generic"
        y_unit = ""
        table = self.all_tables.get(table_name)
        if table and table.file_path and str(table.file_path).lower().endswith(".wdt"):
            data_type = "wave_elevation"
            y_unit = "cm"
        elif table and table.data_type == "motion":
            data_type = "motion"
            y_unit = "cm"
        self.line_data.append(
            AnalysisSeries(
                id=series_id,
                source_table=table_name,
                x_label=x_label,
                y_label=y_label,
                x_data=x_data,
                y_data=y_data,
                data_type=data_type,
                y_unit=y_unit,
            )
        )

    def remove_from_cart(self, index):
        if 0 <= index < len(self.line_data):
            self.line_data.pop(index)

    def update_cart_label(self, index, new_label):
        if 0 <= index < len(self.line_data):
            item = self.line_data[index]
            self.line_data[index] = AnalysisSeries(
                id=item.id,
                source_table=item.source_table,
                x_label=item.x_label,
                y_label=new_label,
                x_data=item.x_data,
                y_data=item.y_data,
                data_type=item.data_type,
                x_unit=item.x_unit,
                y_unit=item.y_unit,
                color=item.color,
                visible=item.visible,
            )
