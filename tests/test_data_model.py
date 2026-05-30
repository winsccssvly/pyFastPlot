import numpy as np

from pyfastplot.models.data_model import DataModel, DataTable


def test_add_input_table_creates_default_table():
    model = DataModel()

    table_name = model.add_input_table()

    assert table_name == "Input Table 1"
    assert table_name in model.all_tables
    assert model.all_tables[table_name].data.shape == (100, 20)


def test_load_csv_file_parses_numeric_and_text_cells(tmp_path):
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text("time,value,label\n0,1.5,a\n1,2.5,\n", encoding="utf-8")
    model = DataModel()

    table_name = model.load_csv_file(csv_path)
    table = model.all_tables[table_name]

    assert table_name == "sample.csv"
    assert table.data[1, 0] == 0.0
    assert table.data[1, 1] == 1.5
    assert table.data[1, 2] == "a"
    assert np.isnan(table.data[2, 2])


def test_load_csv_file_uses_unique_names(tmp_path):
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text("1,2\n", encoding="utf-8")
    model = DataModel()

    first = model.load_csv_file(csv_path)
    second = model.load_csv_file(csv_path)

    assert first == "sample.csv"
    assert second == "sample_1.csv"


def test_paste_data_expands_table_and_supports_undo():
    table = DataTable("T")

    table.paste_data(99, 19, [[1, 2], [3, 4]])

    assert table.data.shape == (101, 21)
    assert table.data[100, 20] == 4
    assert table.undo()
    assert table.data.shape == (100, 20)


def test_promote_row_to_labels_removes_row():
    model = DataModel()
    table_name = model.add_input_table()
    model.set_current_table(table_name)
    table = model.current_table
    assert table is not None
    table.data[0, 0] = "time"
    table.data[0, 1] = "value"

    model.promote_row_to_labels(0)

    assert table.labels[:2] == ["time", "value"]
    assert table.data.shape[0] == 99
