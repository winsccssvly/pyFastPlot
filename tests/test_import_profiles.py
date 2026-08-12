import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pyfastplot.services import import_profiles
from pyfastplot.services.import_profiles import (
    ImportProfile,
    conflicting_extensions,
    read_profile_data,
)


def test_profile_reader_uses_header_and_skips_comments(tmp_path: Path) -> None:
    source = tmp_path / "experiment.dat"
    source.write_text("# exported by instrument\nignored\nTime;Signal\n0;1.5\n1;2.5\n")
    profile = ImportProfile(
        name="Experiment",
        extensions=(".dat",),
        delimiter="semicolon",
        skip_rows=1,
        header_row=1,
        data_start_row=2,
    )

    labels, rows = read_profile_data(source, profile)

    assert labels == ["Time", "Signal"]
    assert rows == [[0.0, 1.5], [1.0, 2.5]]


def test_saved_profile_normalizes_extension(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(import_profiles, "profile_directory", lambda: tmp_path)
    profile = ImportProfile(name="My data", extensions=("result",))

    import_profiles.save_profile(profile)

    assert import_profiles.profile_for_path("measurement.result") is not None


def test_profile_reader_generates_labels_without_header(tmp_path: Path) -> None:
    source = tmp_path / "values.dat"
    source.write_text("0 1.5\n1 2.5\n")
    profile = ImportProfile(
        name="Headerless",
        extensions=(".dat",),
        delimiter="space",
        header_row=None,
        data_start_row=0,
    )

    labels, rows = read_profile_data(source, profile)

    assert labels == ["Col 1", "Col 2"]
    assert rows == [[0.0, 1.5], [1.0, 2.5]]


def test_profile_reader_supports_custom_text_delimiter(tmp_path: Path) -> None:
    source = tmp_path / "values.custom"
    source.write_text("Time::Signal\n0::1.5\n1::2.5\n", encoding="utf-8")
    profile = ImportProfile(
        name="Custom separator",
        extensions=(".custom",),
        delimiter="::",
        header_row=0,
        data_start_row=1,
    )

    labels, rows = read_profile_data(source, profile)

    assert labels == ["Time", "Signal"]
    assert rows == [[0.0, 1.5], [1.0, 2.5]]


def test_conflicting_extensions_include_builtin_and_binary_formats() -> None:
    assert conflicting_extensions(("csv", "xlsx")) == {".csv", ".xlsx"}
