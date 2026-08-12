from dataclasses import dataclass
from typing import Literal

import numpy as np


@dataclass(frozen=True)
class AnalysisRegion:
    """Shared time range applied to plots and statistics.

    Parameters
    ----------
    mode
        Whether to use the full input range or a selected range.
    start
        Selected range start, or ``None`` for full range.
    end
        Selected range end, or ``None`` for full range.
    label
        Display label for the range.
    """

    mode: Literal["full", "selected"] = "full"
    start: float | None = None
    end: float | None = None
    label: str = "Analysis Region"


@dataclass(frozen=True)
class AnalysisSeries:
    """One series selected for plotting, comparison, and statistics."""

    id: str
    source_table: str
    x_label: str
    y_label: str
    x_data: np.ndarray
    y_data: np.ndarray
    data_type: Literal["wave_elevation", "motion", "generic"] = "generic"
    x_unit: str = ""
    y_unit: str = ""
    color: object | None = None
    visible: bool = True


@dataclass(frozen=True)
class IndividualWave:
    """One wave segment bounded by adjacent zero up-crossings."""

    start_time: float
    end_time: float
    period: float
    height: float
    crest: float
    trough: float


@dataclass(frozen=True)
class DespikeThreshold:
    """Non-destructive global threshold for manual despike review."""

    center: float
    std: float
    significant_wave_height: float
    multiplier: float
    lower: float
    upper: float
    sample_count: int
