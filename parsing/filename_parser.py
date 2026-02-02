"""
Parse experiment metadata from filename.
Expected format: YYYYMMDD_experiment_name_OP.ext
"""
import os
import re
from typing import Dict


def parse_filename(filepath: str) -> Dict[str, str]:
    """
    Extract experiment metadata from filename.

    Expected format: YYYYMMDD_experiment_name_OP.ext
    Example: 20260122_reverse_transplant_NK.txt

    Args:
        filepath: Full path to the file

    Returns:
        Dictionary with keys: 'date', 'name', 'operator'
        Returns empty strings if parsing fails
    """
    filename = os.path.basename(filepath)
    name_without_ext = os.path.splitext(filename)[0]

    # Default values
    result = {
        'date': '',
        'name': '',
        'operator': ''
    }

    # Try to parse the filename
    parts = name_without_ext.split('_')

    if len(parts) < 2:
        return result

    # First part should be date (8 digits)
    date_part = parts[0]
    if len(date_part) == 8 and date_part.isdigit():
        # Format as YYYY-MM-DD
        result['date'] = f"{date_part[0:4]}-{date_part[4:6]}-{date_part[6:8]}"

        # Last part should be operator initials (2-3 letters)
        operator_part = parts[-1]
        if len(operator_part) <= 3 and operator_part.isalpha():
            result['operator'] = operator_part.upper()

            # Everything in between is the experiment name
            if len(parts) > 2:
                name_parts = parts[1:-1]
                # Join with spaces and capitalize first word
                experiment_name = ' '.join(name_parts)
                result['name'] = experiment_name.capitalize()

    return result
