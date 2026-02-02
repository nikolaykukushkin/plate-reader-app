"""
File reader with encoding detection for plate reader data files.
Handles both .txt (tab-delimited) and .xls/.xlsx files.
"""
import os
import chardet
import pandas as pd
from typing import Optional


def read_file(filepath: str) -> Optional[pd.DataFrame]:
    """
    Read a plate reader file and return as pandas DataFrame.

    Args:
        filepath: Path to the file (.txt, .xls, or .xlsx)

    Returns:
        DataFrame with file contents, or None if reading failed
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    file_ext = os.path.splitext(filepath)[1].lower()

    try:
        if file_ext in ['.xls', '.xlsx']:
            return _read_excel(filepath)
        else:
            return _read_text(filepath)
    except Exception as e:
        print(f"Error reading file: {e}")
        return None


def _read_text(filepath: str) -> pd.DataFrame:
    """Read tab-delimited text file with encoding detection."""
    # Detect encoding
    with open(filepath, 'rb') as f:
        raw_data = f.read()
        detected = chardet.detect(raw_data)
        encoding = detected['encoding']

    # Try detected encoding, fall back to common encodings
    encodings_to_try = [encoding, 'utf-16', 'utf-16-le', 'utf-8', 'latin1']

    for enc in encodings_to_try:
        if enc is None:
            continue
        try:
            with open(filepath, 'r', encoding=enc) as f:
                content = f.read()

            # Parse as tab-delimited
            lines = content.split('\n')
            data = [line.split('\t') for line in lines]

            # Remove empty trailing rows
            while data and not any(data[-1]):
                data.pop()

            return pd.DataFrame(data)
        except (UnicodeDecodeError, UnicodeError):
            continue

    raise ValueError(f"Could not decode file with any known encoding")


def _read_excel(filepath: str) -> pd.DataFrame:
    """Read Excel file (.xls or .xlsx)."""
    file_ext = os.path.splitext(filepath)[1].lower()

    try:
        if file_ext == '.xls':
            # For old Excel format, try xlrd engine
            try:
                return pd.read_excel(filepath, engine='xlrd', header=None)
            except:
                # If xlrd is not available, try openpyxl (sometimes works with .xls)
                return pd.read_excel(filepath, engine='openpyxl', header=None)
        else:
            # For .xlsx, use openpyxl
            return pd.read_excel(filepath, engine='openpyxl', header=None)
    except Exception as e:
        # Try without specifying engine as a last resort
        return pd.read_excel(filepath, header=None)


def save_to_excel(filepath: str, sheet_data: dict, metadata: Optional[dict] = None):
    """
    Save data to Excel file with multiple sheets.

    Args:
        filepath: Output file path
        sheet_data: Dictionary mapping sheet names to DataFrames
        metadata: Optional dictionary of metadata to include in processed results sheet
    """
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        for sheet_name, df in sheet_data.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)

        # Add metadata if provided (to the second sheet)
        if metadata and len(sheet_data) > 1:
            sheet_name = list(sheet_data.keys())[1]
            worksheet = writer.sheets[sheet_name]

            # Add metadata below the data
            row_offset = len(sheet_data[sheet_name]) + 3
            worksheet.cell(row=row_offset, column=1, value="Metadata:")
            row_offset += 1

            for key, value in metadata.items():
                worksheet.cell(row=row_offset, column=1, value=key)
                worksheet.cell(row=row_offset, column=2, value=str(value))
                row_offset += 1
