"""
Data model for plate reader application.
Holds shared state between screens.
"""
import pandas as pd
import numpy as np
from typing import Optional, List, Tuple, Dict
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Legacy DataModel (used by tkinter app -- do not modify)
# ---------------------------------------------------------------------------

class DataModel:
    """Shared data model for the tkinter application."""

    def __init__(self):
        self.file_path: Optional[str] = None
        self.raw_dataframe: Optional[pd.DataFrame] = None

        self.experiment_date: str = ""
        self.experiment_name: str = ""
        self.operator_initials: str = ""
        self.num_samples: int = 24

        self.standard_replicates: int = 3
        self.sample_replicates: int = 3
        self.standard_concentrations: List[float] = [0.02, 0.05, 0.1, 0.2, 0.5, 1.0, 1.5, 2.0]

        self.bradford_raw_grid: Optional[np.ndarray] = None
        self.bradford_raw_bounds: Optional[Tuple[int, int, int, int]] = None
        self.bradford_standards: Optional[np.ndarray] = None
        self.bradford_samples: Optional[np.ndarray] = None

        self.luminescence_raw_grid: Optional[np.ndarray] = None
        self.luminescence_raw_bounds: Optional[Tuple[int, int, int, int]] = None
        self.luminescence_samples: Optional[np.ndarray] = None

        self.protein_concentrations: Optional[np.ndarray] = None
        self.specific_luminescence: Optional[np.ndarray] = None
        self.standard_curve_params: Optional[dict] = None

        self.sample_names: List[str] = []

    def reset(self):
        self.__init__()

    def get_sample_name(self, index: int) -> str:
        if index < len(self.sample_names) and self.sample_names[index]:
            return self.sample_names[index]
        return f"Sample {index + 1}"

    def set_sample_names_size(self, size: int):
        if len(self.sample_names) < size:
            self.sample_names.extend([""] * (size - len(self.sample_names)))
        elif len(self.sample_names) > size:
            self.sample_names = self.sample_names[:size]


# ---------------------------------------------------------------------------
# New v2 data model (used by Streamlit app)
# ---------------------------------------------------------------------------

@dataclass
class CellSelection:
    """A rectangular selection of cells in the spreadsheet."""
    row_start: int   # inclusive
    row_end: int     # exclusive
    col_start: int   # inclusive
    col_end: int     # exclusive

    @property
    def num_cells(self) -> int:
        return (self.row_end - self.row_start) * (self.col_end - self.col_start)

    @property
    def num_rows(self) -> int:
        return self.row_end - self.row_start

    @property
    def num_cols(self) -> int:
        return self.col_end - self.col_start

    def extract_values(self, df: pd.DataFrame) -> np.ndarray:
        """Extract numeric values from this selection, returned as 2-D array."""
        block = df.iloc[self.row_start:self.row_end, self.col_start:self.col_end]
        result = np.full((self.num_rows, self.num_cols), np.nan)
        for r_idx, (_, row) in enumerate(block.iterrows()):
            for c_idx, val in enumerate(row):
                try:
                    result[r_idx, c_idx] = float(val)
                except (ValueError, TypeError):
                    pass
        return result

    def label(self) -> str:
        """Human-readable label like 'rows 3-10, cols A-F'."""
        col_s = _col_letter(self.col_start)
        col_e = _col_letter(self.col_end - 1)
        return f"rows {self.row_start + 1}-{self.row_end}, cols {col_s}-{col_e}"


def _col_letter(idx: int) -> str:
    """Convert 0-based column index to spreadsheet-style letter(s)."""
    result = ""
    while True:
        result = chr(ord('A') + idx % 26) + result
        idx = idx // 26 - 1
        if idx < 0:
            break
    return result


@dataclass
class Experiment:
    """One experiment's data and configuration."""

    # Identity
    name: str = ""
    date: str = ""
    operator: str = ""

    # Selections (lists to support non-contiguous regions)
    luminescence_selections: List[CellSelection] = field(default_factory=list)
    bradford_standard_selections: List[CellSelection] = field(default_factory=list)
    bradford_sample_selections: List[CellSelection] = field(default_factory=list)

    # Configuration
    standard_concentrations: List[float] = field(
        default_factory=lambda: [0.02, 0.05, 0.1, 0.2, 0.5, 1.0, 1.5, 2.0]
    )
    sample_names: List[str] = field(default_factory=list)
    bradford_enabled: List[bool] = field(default_factory=list)

    # Cached results (populated during calculation)
    luminescence_values: Optional[np.ndarray] = field(default=None, repr=False)
    bradford_standards_data: Optional[np.ndarray] = field(default=None, repr=False)
    bradford_samples_data: Optional[np.ndarray] = field(default=None, repr=False)
    protein_concentrations: Optional[np.ndarray] = field(default=None, repr=False)
    specific_luminescence: Optional[np.ndarray] = field(default=None, repr=False)
    standard_curve_params: Optional[Dict] = field(default=None, repr=False)

    # --- derived properties ---

    @property
    def num_lumi_cells(self) -> int:
        return sum(s.num_cells for s in self.luminescence_selections)

    @property
    def num_samples(self) -> int:
        return self.num_lumi_cells

    @property
    def has_bradford(self) -> bool:
        return bool(self.bradford_standard_selections and self.bradford_sample_selections)

    @property
    def bradford_std_replicates(self) -> int:
        if not self.bradford_standard_selections:
            return 0
        return sum(s.num_cols for s in self.bradford_standard_selections)

    @property
    def bradford_sample_replicates(self) -> int:
        if not self.bradford_sample_selections or self.num_samples == 0:
            return 0
        total = sum(s.num_cells for s in self.bradford_sample_selections)
        return total // self.num_samples

    @property
    def bradford_sample_replicates_valid(self) -> bool:
        if not self.has_bradford or self.num_samples == 0:
            return True
        total = sum(s.num_cells for s in self.bradford_sample_selections)
        return total % self.num_samples == 0

    def ensure_lists_sized(self):
        """Resize sample_names and bradford_enabled to match num_samples."""
        n = self.num_samples
        while len(self.sample_names) < n:
            self.sample_names.append("")
        self.sample_names = self.sample_names[:n]
        while len(self.bradford_enabled) < n:
            self.bradford_enabled.append(True)
        self.bradford_enabled = self.bradford_enabled[:n]

    def clear_results(self):
        """Invalidate cached calculation results."""
        self.luminescence_values = None
        self.bradford_standards_data = None
        self.bradford_samples_data = None
        self.protein_concentrations = None
        self.specific_luminescence = None
        self.standard_curve_params = None


@dataclass
class AppState:
    """Top-level application state for the Streamlit app."""

    # File data
    file_path: Optional[str] = None
    raw_dataframe: Optional[pd.DataFrame] = field(default=None, repr=False)
    original_filename: str = ""

    # Auto-parsed experiment suggestions from filename
    filename_experiments: List[Dict] = field(default_factory=list)

    # User-defined experiments
    experiments: List[Experiment] = field(default_factory=list)

    # Builder state
    active_experiment_idx: int = 0

    # Navigation
    current_screen: str = "upload"

    def add_experiment(self, name: str = "", date: str = "", operator: str = "") -> int:
        """Add a new experiment, return its index."""
        exp = Experiment(name=name, date=date, operator=operator)
        self.experiments.append(exp)
        return len(self.experiments) - 1

    def remove_experiment(self, idx: int):
        if 0 <= idx < len(self.experiments):
            self.experiments.pop(idx)
            if self.active_experiment_idx >= len(self.experiments):
                self.active_experiment_idx = max(0, len(self.experiments) - 1)

    def reset(self):
        self.file_path = None
        self.raw_dataframe = None
        self.original_filename = ""
        self.filename_experiments = []
        self.experiments = []
        self.active_experiment_idx = 0
        self.current_screen = "upload"
