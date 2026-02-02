"""
Data model for plate reader application.
Holds shared state between screens.
"""
import pandas as pd
import numpy as np
from typing import Optional, List, Tuple


class DataModel:
    """Shared data model for the application."""

    def __init__(self):
        # File information
        self.file_path: Optional[str] = None
        self.raw_dataframe: Optional[pd.DataFrame] = None

        # Experiment metadata
        self.experiment_date: str = ""
        self.experiment_name: str = ""
        self.operator_initials: str = ""
        self.num_samples: int = 24

        # Bradford configuration
        self.standard_replicates: int = 3
        self.sample_replicates: int = 3
        self.standard_concentrations: List[float] = [0.02, 0.05, 0.1, 0.2, 0.5, 1.0, 1.5, 2.0]

        # Bradford data
        self.bradford_raw_grid: Optional[np.ndarray] = None  # Original grid from file
        self.bradford_raw_bounds: Optional[Tuple[int, int, int, int]] = None  # (row_start, row_end, col_start, col_end)
        self.bradford_standards: Optional[np.ndarray] = None  # Shape: (8, n_replicates)
        self.bradford_samples: Optional[np.ndarray] = None  # Shape: (n_samples, n_replicates)

        # Luminescence data
        self.luminescence_raw_grid: Optional[np.ndarray] = None  # Original grid from file
        self.luminescence_raw_bounds: Optional[Tuple[int, int, int, int]] = None  # (row_start, row_end, col_start, col_end)
        self.luminescence_samples: Optional[np.ndarray] = None  # Shape: (n_samples,)

        # Calculated results
        self.protein_concentrations: Optional[np.ndarray] = None  # Shape: (n_samples,)
        self.specific_luminescence: Optional[np.ndarray] = None  # Shape: (n_samples,)
        self.standard_curve_params: Optional[dict] = None  # slope, intercept, r_squared, etc.

        # Sample names (editable by user)
        self.sample_names: List[str] = []

    def reset(self):
        """Reset all data to initial state."""
        self.__init__()

    def get_sample_name(self, index: int) -> str:
        """Get sample name by index. Returns 'Sample N' if not set."""
        if index < len(self.sample_names) and self.sample_names[index]:
            return self.sample_names[index]
        return f"Sample {index + 1}"

    def set_sample_names_size(self, size: int):
        """Initialize or resize sample names list."""
        if len(self.sample_names) < size:
            self.sample_names.extend([""] * (size - len(self.sample_names)))
        elif len(self.sample_names) > size:
            self.sample_names = self.sample_names[:size]
