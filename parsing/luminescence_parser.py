"""
Luminescence assay grid detection and parsing.
"""
import numpy as np
import pandas as pd
from typing import Optional, Tuple


def detect_luminescence_grid(
    df: pd.DataFrame,
    num_samples: int,
    bradford_bounds: Optional[Tuple[int, int, int, int]] = None
) -> Optional[Tuple[np.ndarray, Tuple[int, int, int, int]]]:
    """
    Auto-detect luminescence grid in the dataframe.
    Looks for a smaller numeric grid below the Bradford grid.

    Args:
        df: DataFrame containing the file data
        num_samples: Expected number of samples (e.g., 24)
        bradford_bounds: Optional bounds of Bradford grid to search below

    Returns:
        Tuple of (grid_array, bounds) where bounds = (row_start, row_end, col_start, col_end)
        Returns None if no suitable grid found
    """
    data = df.values

    # Determine where to start searching
    start_search_row = 0
    if bradford_bounds is not None:
        start_search_row = bradford_bounds[1] + 1  # Start after Bradford grid

    # Find all numeric regions below Bradford
    best_grid = None
    best_bounds = None
    best_score = 0

    for start_row in range(start_search_row, len(data)):
        for start_col in range(len(data[0]) if len(data) > 0 else 0):
            # Try to find a contiguous numeric block
            grid, bounds = _extract_numeric_block(data, start_row, start_col)
            if grid is not None:
                size = grid.shape[0] * grid.shape[1]
                # Score based on how close the size is to num_samples
                score = 1000 - abs(size - num_samples)
                if score > best_score and size >= num_samples * 0.8:  # Allow 20% tolerance
                    best_score = score
                    best_grid = grid
                    best_bounds = bounds

    return (best_grid, best_bounds) if best_grid is not None else None


def _extract_numeric_block(data: np.ndarray, start_row: int, start_col: int) -> Tuple[Optional[np.ndarray], Optional[Tuple]]:
    """
    Extract a contiguous block of numeric values.
    """
    if start_row >= len(data) or start_col >= len(data[start_row]):
        return None, None

    if not _is_numeric(data[start_row][start_col]):
        return None, None

    # Find extent of numeric block
    num_cols = 0
    for col in range(start_col, len(data[start_row])):
        if _is_numeric(data[start_row][col]):
            num_cols += 1
        else:
            break

    if num_cols == 0:
        return None, None

    num_rows = 0
    for row in range(start_row, len(data)):
        if row >= len(data):
            break

        valid = True
        if start_col + num_cols > len(data[row]):
            break

        for col in range(start_col, start_col + num_cols):
            if not _is_numeric(data[row][col]):
                valid = False
                break

        if valid:
            num_rows += 1
        else:
            break

    if num_rows == 0:
        return None, None

    # Extract and convert to floats
    grid = []
    for row in range(start_row, start_row + num_rows):
        row_data = []
        for col in range(start_col, start_col + num_cols):
            try:
                val = float(data[row][col])
                row_data.append(val)
            except (ValueError, TypeError):
                row_data.append(np.nan)
        grid.append(row_data)

    bounds = (start_row, start_row + num_rows, start_col, start_col + num_cols)
    return np.array(grid), bounds


def _is_numeric(value) -> bool:
    """Check if a value can be converted to float."""
    if value is None or value == '':
        return False
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False


def parse_luminescence_grid(grid: np.ndarray, num_samples: int) -> np.ndarray:
    """
    Parse luminescence grid into sample array.
    Reads left-to-right, top-to-bottom (like reading a book).

    Args:
        grid: 2D numpy array of luminescence values
        num_samples: Expected number of samples

    Returns:
        1D array of luminescence values for each sample
    """
    # Flatten the grid in row-major order (left-to-right, top-to-bottom)
    flattened = grid.flatten()

    # Take only the number of samples we need
    samples = flattened[:num_samples]

    return samples


def extract_grid_from_bounds(
    df: pd.DataFrame,
    row_start: int,
    row_end: int,
    col_start: int,
    col_end: int
) -> np.ndarray:
    """
    Extract a grid from specific bounds in the dataframe.
    Used for manual grid selection.
    """
    data = df.values[row_start:row_end, col_start:col_end]

    # Convert to float array
    grid = []
    for row in data:
        row_data = []
        for val in row:
            try:
                row_data.append(float(val))
            except (ValueError, TypeError):
                row_data.append(np.nan)
        grid.append(row_data)

    return np.array(grid)
