"""
Bradford assay grid detection and parsing.
"""
import numpy as np
import pandas as pd
from typing import Optional, Tuple


def detect_bradford_grid(df: pd.DataFrame) -> Optional[Tuple[np.ndarray, Tuple[int, int, int, int]]]:
    """
    Auto-detect Bradford grid in the dataframe.
    Looks for the largest contiguous numeric grid.

    Args:
        df: DataFrame containing the file data

    Returns:
        Tuple of (grid_array, bounds) where bounds = (row_start, row_end, col_start, col_end)
        Returns None if no suitable grid found
    """
    # Convert dataframe to numpy array
    data = df.values

    # Find all numeric regions
    best_grid = None
    best_bounds = None
    best_size = 0

    # Scan for numeric grids
    for start_row in range(len(data)):
        for start_col in range(len(data[0]) if len(data) > 0 else 0):
            # Try to find a contiguous numeric block starting here
            grid, bounds = _extract_numeric_block(data, start_row, start_col)
            if grid is not None:
                # Check if first row looks like a header (sequential integers)
                if _is_header_row(grid[0]):
                    # Skip the first row
                    if grid.shape[0] > 1:
                        grid = grid[1:]
                        bounds = (bounds[0] + 1, bounds[1], bounds[2], bounds[3])
                    else:
                        continue

                size = grid.shape[0] * grid.shape[1]
                if size > best_size:
                    best_size = size
                    best_grid = grid
                    best_bounds = bounds

    # Bradford grid should be at least 8x12 = 96 values
    if best_grid is not None and best_size >= 80:  # Allow some tolerance
        return best_grid, best_bounds

    return None


def _extract_numeric_block(data: np.ndarray, start_row: int, start_col: int) -> Tuple[Optional[np.ndarray], Optional[Tuple]]:
    """
    Extract a contiguous block of numeric values starting from (start_row, start_col).
    """
    if start_row >= len(data) or start_col >= len(data[start_row]):
        return None, None

    # Check if starting cell is numeric
    if not _is_numeric(data[start_row][start_col]):
        return None, None

    # Find extent of numeric block
    num_rows = 0
    num_cols = 0

    # First, find how many columns are numeric in the first row
    for col in range(start_col, len(data[start_row])):
        if _is_numeric(data[start_row][col]):
            num_cols += 1
        else:
            break

    if num_cols == 0:
        return None, None

    # Now find how many rows have this many numeric columns
    for row in range(start_row, len(data)):
        if row >= len(data):
            break

        # Check if this row has num_cols numeric values starting at start_col
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

    # Extract the block and convert to floats
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


def _is_header_row(row: np.ndarray) -> bool:
    """Check if a row looks like a header (sequential integers like 1, 2, 3, 4...)."""
    if len(row) < 4:
        return False

    try:
        # Check if all values are integers (or very close to integers)
        for val in row[:min(12, len(row))]:
            if abs(val - round(val)) > 0.1:
                return False

        # Check if values are sequential (difference of 1 between consecutive values)
        for i in range(1, min(8, len(row))):
            if abs((row[i] - row[i-1]) - 1.0) > 0.1:
                return False

        # Check if values are in reasonable range for column numbers (1-20)
        if row[0] < 1 or row[0] > 20:
            return False

        return True
    except:
        return False


def parse_bradford_grid(
    grid: np.ndarray,
    num_samples: int,
    std_replicates: int = 3,
    sample_replicates: int = 3
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Parse Bradford grid into standards and samples.

    Grid layout (for 3 replicates):
    - Standards: first std_replicates columns, 8 rows
    - Samples: remaining columns, arranged in blocks of sample_replicates

    Args:
        grid: 2D numpy array of absorbance values
        num_samples: Number of samples expected
        std_replicates: Number of replicates for standards
        sample_replicates: Number of replicates for samples

    Returns:
        Tuple of (standards_array, samples_array)
        - standards_array: shape (8, std_replicates)
        - samples_array: shape (num_samples, sample_replicates)
    """
    num_rows, num_cols = grid.shape

    # Extract standards (first std_replicates columns, 8 rows)
    standards = grid[:8, :std_replicates]

    # Extract samples
    # Samples are in columns starting after standards
    sample_start_col = std_replicates
    samples = []

    # Calculate how many samples per column block
    samples_per_block = 8  # Typically 8 rows

    # Number of column blocks needed
    num_blocks = (num_samples + samples_per_block - 1) // samples_per_block

    sample_idx = 0
    for block in range(num_blocks):
        col_start = sample_start_col + block * sample_replicates
        col_end = col_start + sample_replicates

        if col_end > num_cols:
            break

        # Extract samples from this block (rows 0-7 or until we have enough samples)
        for row in range(min(samples_per_block, num_rows)):
            if sample_idx >= num_samples:
                break

            sample_data = grid[row, col_start:col_end]
            samples.append(sample_data)
            sample_idx += 1

        if sample_idx >= num_samples:
            break

    samples_array = np.array(samples)
    return standards, samples_array


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
