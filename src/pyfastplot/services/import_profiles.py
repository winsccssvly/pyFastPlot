"""User-configurable readers for delimited text data files."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

BUILT_IN_TEXT_EXTENSIONS = frozenset({".csv", ".wdt"})
UNSUPPORTED_BINARY_EXTENSIONS = frozenset({".xls", ".xlsx", ".xlsm", ".xlsb", ".ods"})


@dataclass(frozen=True)
class ImportProfile:
    """Rules used to turn one family of text files into a data table.

    Parameters
    ----------
    name
        Human-readable profile name.
    extensions
        File suffixes associated with this profile.
    delimiter
        A delimiter character or text string, or ``"tab"`` or ``"space"``.
    skip_rows, header_row, data_start_row
        Zero-based line positions in the source file.
    """

    name: str
    extensions: tuple[str, ...]
    delimiter: str = "comma"
    encoding: str = "utf-8"
    skip_rows: int = 0
    header_row: int | None = 0
    data_start_row: int = 1
    comment_prefixes: tuple[str, ...] = ("#",)
    x_column: str = ""
    data_type: str = "generic"


def profile_directory() -> Path:
    """Return the per-user directory used for import profiles."""
    return Path.home() / ".pyfastplot" / "import-profiles"


def normalize_extension(value: str) -> str:
    """Normalize one user-entered filename suffix."""
    text = value.strip().lower()
    if not text:
        return ""
    return text if text.startswith(".") else f".{text}"


def delimiter_value(value: str) -> str:
    """Translate a stored delimiter label into a delimiter character."""
    return {"tab": "\t", "space": " ", "comma": ",", "semicolon": ";"}.get(value, value)


def load_profiles() -> list[ImportProfile]:
    """Load valid user profiles, ignoring incomplete configuration files."""
    return [profile for _path, profile in load_profile_records()]


def load_profile_records() -> list[tuple[Path, ImportProfile]]:
    """Load saved profiles together with the files that define them."""
    records: list[tuple[Path, ImportProfile]] = []
    for path in profile_directory().glob("*.json"):
        try:
            content = json.loads(path.read_text(encoding="utf-8"))
            records.append((path, _profile_from_dict(content)))
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            continue
    return records


def save_profile(profile: ImportProfile) -> Path:
    """Persist a profile in the user configuration directory."""
    directory = profile_directory()
    directory.mkdir(parents=True, exist_ok=True)
    file_name = "-".join(profile.name.lower().split()) or "import-profile"
    path = directory / f"{file_name}.json"
    content = asdict(profile)
    content["extensions"] = [
        extension
        for value in profile.extensions
        if (extension := normalize_extension(value))
    ]
    path.write_text(json.dumps(content, indent=2), encoding="utf-8")
    return path


def delete_profile(profile_path: Path) -> None:
    """Delete one saved import profile from the application's profile directory."""
    directory = profile_directory().resolve()
    target = profile_path.resolve()
    if target.parent != directory or target.suffix.lower() != ".json":
        raise ValueError("The selected file is not an import profile.")
    target.unlink()


def profile_for_path(file_path: str | Path) -> ImportProfile | None:
    """Return the first configured profile matching a file suffix."""
    suffix = Path(file_path).suffix.lower()
    if suffix in UNSUPPORTED_BINARY_EXTENSIONS:
        return None
    return next((p for p in load_profiles() if suffix in p.extensions), None)


def supported_extensions() -> set[str]:
    """Return all currently supported text-file suffixes."""
    profile_extensions = {
        extension
        for profile in load_profiles()
        for extension in profile.extensions
        if extension not in UNSUPPORTED_BINARY_EXTENSIONS
    }
    return set(BUILT_IN_TEXT_EXTENSIONS) | profile_extensions


def is_supported_text_path(file_path: str | Path) -> bool:
    """Return whether a path has an explicitly supported text-file suffix."""
    return Path(file_path).suffix.lower() in supported_extensions()


def conflicting_extensions(extensions: tuple[str, ...]) -> set[str]:
    """Return enabled or reserved extensions that cannot be registered again."""
    normalized = {normalize_extension(extension) for extension in extensions}
    normalized.discard("")
    return normalized & (supported_extensions() | UNSUPPORTED_BINARY_EXTENSIONS)


def file_dialog_filter() -> str:
    """Build the native file-dialog filter from installed user profiles."""
    extensions = sorted(supported_extensions() - BUILT_IN_TEXT_EXTENSIONS)
    patterns = " ".join(f"*{extension}" for extension in extensions)
    supported = (
        f"Supported text files ({patterns} *.csv *.wdt)"
        if patterns
        else "Supported text files (*.csv *.wdt)"
    )
    return f"{supported};;All Files (*)"


def read_profile_data(
    file_path: str | Path, profile: ImportProfile
) -> tuple[list[str], list[list[object]]]:
    """Read a profile-configured delimited file into labels and scalar rows."""
    lines = (
        Path(file_path)
        .read_text(encoding=profile.encoding, errors="replace")
        .splitlines()
    )
    lines = [line for line in lines if not _is_comment(line, profile.comment_prefixes)]
    lines = lines[profile.skip_rows :]
    delimiter = delimiter_value(profile.delimiter)
    rows = _read_delimited_rows(lines, delimiter)
    header_index = (
        profile.header_row - profile.skip_rows
        if profile.header_row is not None
        else None
    )
    data_index = max(0, profile.data_start_row - profile.skip_rows)
    labels = _labels_from_rows(rows, header_index)
    return labels, [_convert_row(row) for row in rows[data_index:] if row]


def preview_profile_data(
    file_path: str | Path, profile: ImportProfile, limit: int = 20
) -> tuple[list[str], list[list[object]]]:
    """Read a bounded preview for the import-profile wizard."""
    labels, rows = read_profile_data(file_path, profile)
    return labels, rows[:limit]


def _profile_from_dict(content: dict[str, Any]) -> ImportProfile:
    extensions = tuple(
        extension
        for value in content.get("extensions", [])
        if (extension := normalize_extension(str(value)))
    )
    if not content.get("name") or not extensions:
        raise ValueError("A profile needs a name and at least one extension.")
    header = content.get("header_row", 0)
    return ImportProfile(
        name=str(content["name"]),
        extensions=extensions,
        delimiter=str(content.get("delimiter", "comma")),
        encoding=str(content.get("encoding", "utf-8")),
        skip_rows=int(content.get("skip_rows", 0)),
        header_row=None if header is None else int(header),
        data_start_row=int(content.get("data_start_row", 1)),
        comment_prefixes=tuple(content.get("comment_prefixes", ["#"])),
        x_column=str(content.get("x_column", "")),
        data_type=str(content.get("data_type", "generic")),
    )


def _is_comment(line: str, prefixes: tuple[str, ...]) -> bool:
    return any(line.lstrip().startswith(prefix) for prefix in prefixes if prefix)


def _read_delimited_rows(lines: list[str], delimiter: str) -> list[list[str]]:
    """Read CSV-compatible single delimiters or custom text delimiters."""
    if not delimiter:
        raise ValueError("Enter a delimiter.")
    if len(delimiter) == 1:
        return list(csv.reader(lines, delimiter=delimiter))
    return [line.split(delimiter) for line in lines]


def _labels_from_rows(rows: list[list[str]], index: int | None) -> list[str]:
    if index is None or index < 0 or index >= len(rows):
        width = max((len(row) for row in rows), default=0)
        return [f"Col {number}" for number in range(1, width + 1)]
    return [
        value.strip() or f"Col {number}" for number, value in enumerate(rows[index], 1)
    ]


def _convert_row(row: list[str]) -> list[object]:
    values: list[object] = []
    for value in row:
        text = value.strip()
        try:
            values.append(float(text))
        except ValueError:
            values.append(text if text else np.nan)
    return values
