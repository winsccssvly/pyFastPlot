"""Independent data and series state for the publication-figure tab."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class FigureDataset:
    """One tabular dataset available to the figure workspace."""

    name: str
    labels: tuple[str, ...]
    data: np.ndarray


@dataclass(frozen=True)
class FigureSeries:
    """One selected X/Y pair for a publication figure."""

    dataset_name: str
    x_label: str
    y_label: str
    x_data: np.ndarray
    y_data: np.ndarray
    label: str


class FigureModel:
    """Own datasets and plot selections independently from post-processing."""

    def __init__(self) -> None:
        self.datasets: dict[str, FigureDataset] = {}
        self.series: list[FigureSeries] = []
        self.current_dataset_name = ""

    @property
    def current_dataset(self) -> FigureDataset | None:
        """Return the dataset selected in the figure workspace."""
        return self.datasets.get(self.current_dataset_name)

    def add_dataset(self, name: str, labels: list[str], data: np.ndarray) -> str:
        """Store a numeric table and return its unique display name."""
        array = _numeric_array(data)
        if array.ndim != 2 or array.shape[1] != len(labels):
            raise ValueError(
                "Data must be a two-dimensional array matching its labels."
            )
        dataset_name = self._unique_name(name)
        self.datasets[dataset_name] = FigureDataset(
            dataset_name, tuple(labels), array.copy()
        )
        self.current_dataset_name = dataset_name
        return dataset_name

    def remove_dataset(self, name: str) -> None:
        """Remove a dataset and all figure series derived from it."""
        self.datasets.pop(name, None)
        self.series = [series for series in self.series if series.dataset_name != name]
        if self.current_dataset_name == name:
            self.current_dataset_name = next(iter(self.datasets), "")

    def set_current_dataset(self, name: str) -> None:
        """Select an existing dataset by name."""
        self.current_dataset_name = name if name in self.datasets else ""

    def add_series(self, x_label: str, y_label: str, replace: bool) -> bool:
        """Add a clean numeric series from the selected dataset."""
        dataset = self.current_dataset
        if (
            dataset is None
            or x_label not in dataset.labels
            or y_label not in dataset.labels
        ):
            return False
        x_index = dataset.labels.index(x_label)
        y_index = dataset.labels.index(y_label)
        x_data = dataset.data[:, x_index]
        y_data = dataset.data[:, y_index]
        valid = np.isfinite(x_data) & np.isfinite(y_data)
        if not valid.any():
            return False
        if replace:
            self.series.clear()
        self.series.append(
            FigureSeries(
                dataset.name,
                x_label,
                y_label,
                x_data[valid],
                y_data[valid],
                y_label,
            )
        )
        return True

    def _unique_name(self, name: str) -> str:
        base_name = name.strip() or "Figure data"
        candidate = base_name
        number = 2
        while candidate in self.datasets:
            candidate = f"{base_name} ({number})"
            number += 1
        return candidate


def _numeric_array(data: np.ndarray) -> np.ndarray:
    """Convert mixed table cells to a float matrix, preserving gaps as NaN."""
    source = np.asarray(data, dtype=object)
    array = np.full(source.shape, np.nan, dtype=float)
    for index, value in np.ndenumerate(source):
        try:
            array[index] = float(value)
        except (TypeError, ValueError):
            continue
    return array
