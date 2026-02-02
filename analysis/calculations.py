"""
Analysis calculations for Bradford protein assay.
Includes linear regression and protein concentration calculation.
"""
import numpy as np
from scipy import stats
from typing import Tuple, Dict


def calculate_protein_concentrations(
    bradford_samples: np.ndarray,
    bradford_standards: np.ndarray,
    standard_concentrations: np.ndarray,
    luminescence_samples: np.ndarray
) -> Tuple[np.ndarray, np.ndarray, Dict]:
    """
    Calculate protein concentrations from Bradford assay data.

    Args:
        bradford_samples: Array of sample absorbances, shape (n_samples, n_replicates)
        bradford_standards: Array of standard absorbances, shape (8, n_replicates)
        standard_concentrations: Array of standard concentrations (mg/ml), shape (8,)
        luminescence_samples: Array of luminescence values, shape (n_samples,)

    Returns:
        Tuple of:
        - protein_concentrations: Array of protein concentrations (mg/ml), shape (n_samples,)
        - specific_luminescence: Array of specific luminescence (RLU per mg/ml), shape (n_samples,)
        - curve_params: Dictionary with regression parameters
    """
    # Average the replicates for standards and samples
    std_abs_mean = np.mean(bradford_standards, axis=1)
    std_abs_sem = stats.sem(bradford_standards, axis=1)
    sample_abs_mean = np.mean(bradford_samples, axis=1)

    # Perform linear regression: absorbance = slope * concentration + intercept
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        standard_concentrations,
        std_abs_mean
    )

    r_squared = r_value ** 2

    # Calculate protein concentrations from sample absorbances
    # concentration = (absorbance - intercept) / slope
    protein_concentrations = (sample_abs_mean - intercept) / slope

    # Handle negative concentrations (can happen if absorbance is below intercept)
    protein_concentrations = np.maximum(protein_concentrations, 0.0)

    # Calculate specific luminescence (RLU per mg/ml)
    # Avoid division by zero
    specific_luminescence = np.zeros_like(luminescence_samples, dtype=float)
    mask = protein_concentrations > 0
    specific_luminescence[mask] = luminescence_samples[mask] / protein_concentrations[mask]

    # Prepare curve parameters
    curve_params = {
        'slope': slope,
        'intercept': intercept,
        'r_squared': r_squared,
        'p_value': p_value,
        'std_err': std_err,
        'std_concentrations': standard_concentrations,
        'std_absorbances_mean': std_abs_mean,
        'std_absorbances_sem': std_abs_sem
    }

    return protein_concentrations, specific_luminescence, curve_params


def format_equation(slope: float, intercept: float) -> str:
    """
    Format the linear equation as a string.

    Args:
        slope: Slope of the line
        intercept: Y-intercept

    Returns:
        String like "y = 0.423x + 0.085"
    """
    if intercept >= 0:
        return f"y = {slope:.3f}x + {intercept:.3f}"
    else:
        return f"y = {slope:.3f}x - {abs(intercept):.3f}"
