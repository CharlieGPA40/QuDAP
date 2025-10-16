"""
VSM Magnetic Contributions Module
==================================

Extracts and removes paramagnetic (PM) and diamagnetic (DM) contributions
from VSM hysteresis data.

Author: VSM Analysis Tools
Version: 2.0 (Updated with separate upper/lower branch fitting)
Date: 2024

Usage:
    from vsm_magnetic_contributions import (
        extract_pm_dm_slope,
        remove_pm_dm_contribution,
        visualize_pm_dm_extraction
    )
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats


def identify_saturation_regions(H, M, saturation_threshold=0.8, min_points=20):
    """
    Identify high-field regions where ferromagnetic component is saturated

    Parameters:
    -----------
    H : array-like
        Magnetic field (Oe)
    M : array-like
        Magnetic moment (emu)
    saturation_threshold : float
        Fraction of max field to consider as "high field" (default 0.8 = 80%)
    min_points : int
        Minimum number of points required in saturation region

    Returns:
    --------
    dict : Indices and characteristics of saturation regions
    """
    # Sort by field
    sort_idx = np.argsort(H)
    H_sorted = H[sort_idx]
    M_sorted = M[sort_idx]

    H_max = np.max(np.abs(H_sorted))
    threshold_field = saturation_threshold * H_max

    # Find points in saturation regions
    # Negative high field (most negative)
    neg_sat_mask = H_sorted < -threshold_field
    neg_sat_indices = sort_idx[neg_sat_mask]

    # Positive high field (most positive)
    pos_sat_mask = H_sorted > threshold_field
    pos_sat_indices = sort_idx[pos_sat_mask]

    # Check if we have enough points
    if len(neg_sat_indices) < min_points or len(pos_sat_indices) < min_points:
        # Reduce threshold
        threshold_field = 0.7 * H_max
        neg_sat_mask = H_sorted < -threshold_field
        neg_sat_indices = sort_idx[neg_sat_mask]
        pos_sat_mask = H_sorted > threshold_field
        pos_sat_indices = sort_idx[pos_sat_mask]

    return {
        'neg_indices': neg_sat_indices,
        'pos_indices': pos_sat_indices,
        'threshold_field': threshold_field,
        'neg_H': H[neg_sat_indices],
        'neg_M': M[neg_sat_indices],
        'pos_H': H[pos_sat_indices],
        'pos_M': M[pos_sat_indices]
    }


def find_linear_regions(x, y, n_points=50, linearity_threshold=0.995):
    """
    Automatically find linear regions at high fields (beginning and end of data)

    Parameters:
    -----------
    x : array-like
        Magnetic field (Oe)
    y : array-like
        Magnetic moment (emu)
    n_points : int
        Number of points to test from each end
    linearity_threshold : float
        R² threshold for linearity (default 0.995)

    Returns:
    --------
    dict : Indices of linear regions and their R² values
    """
    # Sort data by field if not already sorted
    sort_idx = np.argsort(x)
    x_sorted = x[sort_idx]
    y_sorted = y[sort_idx]

    # Test beginning points (most negative field)
    best_start_idx = 0
    best_start_r2 = 0

    for i in range(20, min(n_points + 1, len(x) // 4)):
        x_start = x_sorted[:i]
        y_start = y_sorted[:i]

        # Calculate R² for linear fit
        slope, intercept, r_value, _, _ = stats.linregress(x_start, y_start)
        r2 = r_value ** 2

        if r2 >= linearity_threshold and r2 > best_start_r2:
            best_start_r2 = r2
            best_start_idx = i

    # Test ending points (most positive field)
    best_end_idx = len(x_sorted)
    best_end_r2 = 0

    for i in range(20, min(n_points + 1, len(x) // 4)):
        x_end = x_sorted[-i:]
        y_end = y_sorted[-i:]

        # Calculate R² for linear fit
        slope, intercept, r_value, _, _ = stats.linregress(x_end, y_end)
        r2 = r_value ** 2

        if r2 >= linearity_threshold and r2 > best_end_r2:
            best_end_r2 = r2
            best_end_idx = i

    # If no good linear region found, use default
    if best_start_idx == 0:
        best_start_idx = min(30, len(x) // 5)
    if best_end_idx == len(x_sorted):
        best_end_idx = min(30, len(x) // 5)

    # Get the actual indices in original (unsorted) array
    start_indices = sort_idx[:best_start_idx]
    end_indices = sort_idx[-best_end_idx:]

    return {
        'start_indices': start_indices,
        'end_indices': end_indices,
        'start_r2': best_start_r2,
        'end_r2': best_end_r2,
        'start_n': best_start_idx,
        'end_n': best_end_idx
    }


def extract_pm_dm_slope(H, M, method='linear_saturation', **kwargs):
    """
    Extract paramagnetic + diamagnetic slope from high-field data

    Parameters:
    -----------
    H : array-like
        Magnetic field (Oe)
    M : array-like
        Magnetic moment (emu)
    method : str
        Method to use:
        - 'linear_saturation': Linear fit to high-field saturation regions (RECOMMENDED)
        - 'high_field_only': Use only highest field points
        - 'symmetric': Enforce symmetry between +H and -H regions
    **kwargs : additional parameters
        saturation_threshold: field threshold (default 0.8)
        n_points: number of points to use (for 'high_field_only')

    Returns:
    --------
    dict : Slope components and diagnostics
    """
    # Convert to numpy arrays
    H = np.asarray(H)
    M = np.asarray(M)

    # Validate input
    if len(H) != len(M):
        raise ValueError(f"H and M must have same length (H: {len(H)}, M: {len(M)})")

    if len(H) < 50:
        raise ValueError(f"Need at least 50 data points, got {len(H)}")

    # Check for NaN/Inf
    n_invalid = np.sum(~np.isfinite(H) | ~np.isfinite(M))
    if n_invalid > len(H) * 0.5:
        raise ValueError(f"Too many invalid (NaN/Inf) values: {n_invalid}/{len(H)}")

    # Try the requested method
    try:
        if method == 'linear_saturation':
            result = _extract_slope_linear_saturation(H, M, **kwargs)
        elif method == 'high_field_only':
            result = _extract_slope_high_field_only(H, M, **kwargs)
        elif method == 'symmetric':
            result = _extract_slope_symmetric(H, M, **kwargs)
        else:
            raise ValueError(f"Unknown method: {method}. Use 'linear_saturation', 'high_field_only', or 'symmetric'")

        # Validate result
        if not np.isfinite(result['chi_total']):
            raise ValueError(f"Method '{method}' returned invalid chi_total: {result['chi_total']}")

        return result

    except Exception as e:
        # If the primary method fails, try a fallback
        print(f"Warning: Method '{method}' failed ({e}). Trying fallback method...")

        if method != 'high_field_only':
            try:
                print("  Trying 'high_field_only' method as fallback...")
                result = _extract_slope_high_field_only(H, M, n_points=kwargs.get('n_points', 30))
                if np.isfinite(result['chi_total']):
                    print(f"  Fallback succeeded! chi = {result['chi_total']:.6e}")
                    return result
            except:
                pass

        # If all methods fail, return zero slope
        print(f"  All methods failed. Returning zero slope.")
        return {
            'chi_total': 0.0,
            'chi_upper': 0.0,
            'chi_lower': 0.0,
            'chi_total_origin': 0.0,
            'M_offset': 0.0,
            'r_squared': 0.0,
            'std_err': 0.0,
            'n_points': 0,
            'sat_threshold': kwargs.get('saturation_threshold', 0.8),
            'sat_regions': None,
            'method': 'failed',
            'error': str(e)
        }


def _fit_slope_linear_saturation(H_sat, M_sat):
    """Helper function to fit slope to a single branch"""
    # Linear fit: M = M_offset + slope * H
    slope, intercept, r_value, p_value, std_err = stats.linregress(H_sat, M_sat)

    # Check if result is valid
    if not np.isfinite(slope):
        raise ValueError("Linear regression returned NaN or Inf for slope")

    # Alternative: force through origin for pure χ
    H_sat_squared_sum = np.sum(H_sat ** 2)
    if H_sat_squared_sum > 0:
        slope_origin = np.sum(H_sat * M_sat) / H_sat_squared_sum
    else:
        slope_origin = 0

    return slope, intercept, r_value, p_value, std_err, slope_origin


def _extract_slope_linear_saturation(H, M, saturation_threshold=0.8, min_points=20):
    """
    Extract slope by linear fitting to high-field saturation regions
    Fits upper and lower branches separately, then averages
    Assumes: M = M_sat + χ*H at high fields
    """
    # Get saturation regions
    sat_regions = identify_saturation_regions(H, M, saturation_threshold, min_points)

    # Separate upper and lower branches
    H_sat_upper = sat_regions['pos_H']
    M_sat_upper = sat_regions['pos_M']
    H_sat_lower = sat_regions['neg_H']
    M_sat_lower = sat_regions['neg_M']

    # Check for valid data
    if len(H_sat_upper) < 10 or len(H_sat_lower) < 10:
        raise ValueError(f"Not enough points in saturation regions")

    # Remove any NaN or Inf values - upper
    valid_mask = np.isfinite(H_sat_upper) & np.isfinite(M_sat_upper)
    H_sat_upper = H_sat_upper[valid_mask]
    M_sat_upper = M_sat_upper[valid_mask]

    if len(H_sat_upper) < 10:
        raise ValueError(f"Not enough valid points in upper branch after removing NaN/Inf (only {len(H_sat_upper)})")

    # Remove any NaN or Inf values - lower
    valid_mask = np.isfinite(H_sat_lower) & np.isfinite(M_sat_lower)
    H_sat_lower = H_sat_lower[valid_mask]
    M_sat_lower = M_sat_lower[valid_mask]

    if len(H_sat_lower) < 10:
        raise ValueError(f"Not enough valid points in lower branch after removing NaN/Inf (only {len(H_sat_lower)})")

    try:
        # Fit upper branch (positive field)
        slope_upper, intercept_upper, r_value_upper, p_value_upper, std_err_upper, slope_origin_upper = _fit_slope_linear_saturation(
            H_sat_upper, M_sat_upper)

        # Fit lower branch (negative field)
        slope_lower, intercept_lower, r_value_lower, p_value_lower, std_err_lower, slope_origin_lower = _fit_slope_linear_saturation(
            H_sat_lower, M_sat_lower)

        # Average the slopes
        slope = (slope_upper + slope_lower) / 2
        slope_origin = (slope_origin_upper + slope_origin_lower) / 2
        intercept = (intercept_upper + intercept_lower) / 2
        r_value = np.sqrt((r_value_upper**2 + r_value_lower**2) / 2)
        std_err = (std_err_upper + std_err_lower) / 2

    except Exception as e:
        raise ValueError(f"Linear fit failed: {e}")

    return {
        'chi_total': slope,  # χ_para + χ_dia (averaged)
        'chi_upper': slope_upper,  # χ from upper branch
        'chi_lower': slope_lower,  # χ from lower branch
        'chi_total_origin': slope_origin,
        'chi_upper_origin': slope_origin_upper,
        'chi_lower_origin': slope_origin_lower,
        'M_offset': intercept,
        'M_offset_upper': intercept_upper,
        'M_offset_lower': intercept_lower,
        'r_squared': r_value**2,
        'r_squared_upper': r_value_upper**2,
        'r_squared_lower': r_value_lower**2,
        'std_err': std_err,
        'n_points': len(H_sat_upper) + len(H_sat_lower),
        'n_points_upper': len(H_sat_upper),
        'n_points_lower': len(H_sat_lower),
        'sat_threshold': saturation_threshold,
        'sat_regions': sat_regions,
        'method': 'linear_saturation'
    }


def _extract_slope_high_field_only(H, M, n_points=30):
    """
    Use only the N highest field points from each end
    Fits upper and lower branches separately, then averages
    """
    # Remove NaN values first
    valid_mask = np.isfinite(H) & np.isfinite(M)
    H_clean = H[valid_mask]
    M_clean = M[valid_mask]

    if len(H_clean) < 2 * n_points:
        n_points = len(H_clean) // 4
        if n_points < 10:
            raise ValueError(f"Not enough valid data points (only {len(H_clean)})")

    # Sort by field
    sort_idx = np.argsort(H_clean)
    H_sorted = H_clean[sort_idx]
    M_sorted = M_clean[sort_idx]

    # Take n_points from each end
    H_lower = H_sorted[:n_points]  # Negative field (lower branch)
    M_lower = M_sorted[:n_points]
    H_upper = H_sorted[-n_points:]  # Positive field (upper branch)
    M_upper = M_sorted[-n_points:]

    # Linear fit for each branch
    try:
        # Fit lower branch (negative field)
        slope_lower, intercept_lower, r_value_lower, _, std_err_lower = stats.linregress(H_lower, M_lower)

        # Fit upper branch (positive field)
        slope_upper, intercept_upper, r_value_upper, _, std_err_upper = stats.linregress(H_upper, M_upper)

        if not (np.isfinite(slope_lower) and np.isfinite(slope_upper)):
            raise ValueError("Linear fit returned NaN")

        # Average the slopes
        slope = (slope_lower + slope_upper) / 2
        intercept = (intercept_lower + intercept_upper) / 2
        r_value = np.sqrt((r_value_lower**2 + r_value_upper**2) / 2)
        std_err = (std_err_lower + std_err_upper) / 2

        # Alternative through origin for each branch
        H_lower_squared_sum = np.sum(H_lower ** 2)
        H_upper_squared_sum = np.sum(H_upper ** 2)

        if H_lower_squared_sum > 0:
            slope_origin_lower = np.sum(H_lower * M_lower) / H_lower_squared_sum
        else:
            slope_origin_lower = 0

        if H_upper_squared_sum > 0:
            slope_origin_upper = np.sum(H_upper * M_upper) / H_upper_squared_sum
        else:
            slope_origin_upper = 0

        slope_origin = (slope_origin_lower + slope_origin_upper) / 2

    except Exception as e:
        raise ValueError(f"Linear fit failed: {e}")

    # Create sat_regions for compatibility
    sat_regions = {
        'neg_indices': np.where(np.isin(H, H_lower))[0],
        'pos_indices': np.where(np.isin(H, H_upper))[0],
        'neg_H': H_lower,
        'neg_M': M_lower,
        'pos_H': H_upper,
        'pos_M': M_upper,
        'threshold_field': np.percentile(np.abs(H_clean), 80)
    }

    return {
        'chi_total': slope,  # Averaged slope
        'chi_upper': slope_upper,
        'chi_lower': slope_lower,
        'chi_total_origin': slope_origin,
        'chi_upper_origin': slope_origin_upper,
        'chi_lower_origin': slope_origin_lower,
        'M_offset': intercept,
        'M_offset_upper': intercept_upper,
        'M_offset_lower': intercept_lower,
        'r_squared': r_value**2,
        'r_squared_upper': r_value_upper**2,
        'r_squared_lower': r_value_lower**2,
        'std_err': std_err,
        'n_points': 2 * n_points,
        'n_points_upper': n_points,
        'n_points_lower': n_points,
        'sat_regions': sat_regions,
        'method': 'high_field_only'
    }


def _extract_slope_symmetric(H, M, saturation_threshold=0.8, min_points=20):
    """
    Enforce symmetry: χ(+H) should equal χ(-H)
    Fit slopes from positive and negative field regions separately
    """
    sat_regions = identify_saturation_regions(H, M, saturation_threshold, min_points)

    # Remove NaN values
    neg_valid = np.isfinite(sat_regions['neg_H']) & np.isfinite(sat_regions['neg_M'])
    pos_valid = np.isfinite(sat_regions['pos_H']) & np.isfinite(sat_regions['pos_M'])

    neg_H = sat_regions['neg_H'][neg_valid]
    neg_M = sat_regions['neg_M'][neg_valid]
    pos_H = sat_regions['pos_H'][pos_valid]
    pos_M = sat_regions['pos_M'][pos_valid]

    if len(neg_H) < 10 or len(pos_H) < 10:
        raise ValueError(f"Not enough valid points in saturation regions")

    try:
        # Fit negative region (lower branch)
        slope_lower, intercept_lower, r_lower, _, std_err_lower = stats.linregress(neg_H, neg_M)

        # Fit positive region (upper branch)
        slope_upper, intercept_upper, r_upper, _, std_err_upper = stats.linregress(pos_H, pos_M)

        # Check validity
        if not (np.isfinite(slope_lower) and np.isfinite(slope_upper)):
            raise ValueError("Linear fit returned NaN")

        # Average (should be similar if truly symmetric)
        chi_avg = (slope_lower + slope_upper) / 2

        # Through origin versions
        neg_H_squared_sum = np.sum(neg_H ** 2)
        pos_H_squared_sum = np.sum(pos_H ** 2)

        if neg_H_squared_sum > 0:
            slope_origin_lower = np.sum(neg_H * neg_M) / neg_H_squared_sum
        else:
            slope_origin_lower = 0

        if pos_H_squared_sum > 0:
            slope_origin_upper = np.sum(pos_H * pos_M) / pos_H_squared_sum
        else:
            slope_origin_upper = 0

        slope_origin = (slope_origin_lower + slope_origin_upper) / 2

    except Exception as e:
        raise ValueError(f"Symmetric fit failed: {e}")

    return {
        'chi_total': chi_avg,  # Averaged slope
        'chi_lower': slope_lower,  # χ from negative field
        'chi_upper': slope_upper,  # χ from positive field
        'chi_total_origin': slope_origin,
        'chi_lower_origin': slope_origin_lower,
        'chi_upper_origin': slope_origin_upper,
        'asymmetry': abs(slope_upper - slope_lower),
        'M_offset': (intercept_lower + intercept_upper) / 2,
        'M_offset_lower': intercept_lower,
        'M_offset_upper': intercept_upper,
        'r_squared_lower': r_lower**2,
        'r_squared_upper': r_upper**2,
        'r_squared': (r_lower**2 + r_upper**2) / 2,  # Average R²
        'std_err': (std_err_lower + std_err_upper) / 2,
        'n_points': len(neg_H) + len(pos_H),
        'n_points_lower': len(neg_H),
        'n_points_upper': len(pos_H),
        'sat_regions': sat_regions,
        'method': 'symmetric'
    }


def remove_pm_dm_contribution(H, M, chi_total, remove_offset=True, M_offset=0):
    """
    Remove paramagnetic and diamagnetic linear background

    Parameters:
    -----------
    H : array-like
        Magnetic field
    M : array-like
        Measured moment
    chi_total : float
        Total susceptibility (χ_para + χ_dia)
    remove_offset : bool
        Whether to also remove vertical offset
    M_offset : float
        Vertical offset to remove

    Returns:
    --------
    array : Corrected moment (ferromagnetic contribution only)
    """
    M_corrected = M - chi_total * H

    if remove_offset:
        M_corrected = M_corrected - M_offset

    return M_corrected


def separate_pm_dm_contributions(chi_total, temperature=None, estimate_method='assume_dominant'):
    """
    Try to separate paramagnetic and diamagnetic contributions

    Parameters:
    -----------
    chi_total : float
        Total measured susceptibility
    temperature : float, optional
        Temperature in Kelvin
    estimate_method : str
        Method to estimate separation:
        - 'assume_dominant': Assume purely PM or DM based on sign

    Returns:
    --------
    dict : Estimated contributions
    """
    if chi_total > 1e-10:
        # Positive total: paramagnetic dominates
        return {
            'chi_para': chi_total,  # Lower bound
            'chi_dia': 0,  # Unknown without more data
            'dominant': 'paramagnetic',
            'confidence': 'medium',
            'note': 'Cannot separate without additional measurements'
        }

    elif chi_total < -1e-10:
        # Negative total: diamagnetic dominates
        return {
            'chi_para': 0,  # Unknown without more data
            'chi_dia': chi_total,  # Lower bound
            'dominant': 'diamagnetic',
            'confidence': 'medium',
            'note': 'Cannot separate without additional measurements'
        }

    else:
        # Negligible
        return {
            'chi_para': 0,
            'chi_dia': 0,
            'dominant': 'negligible',
            'confidence': 'high',
            'note': 'No significant PM/DM contribution'
        }


def get_linear_region_diagnostics(x, y, slope, n_points=50):
    """
    Get diagnostic information about the linear regions

    Parameters:
    -----------
    x, y : array-like
        Data
    slope : float
        Calculated slope
    n_points : int
        Number of points used

    Returns:
    --------
    dict : Diagnostic information
    """
    linear_regions = find_linear_regions(x, y, n_points=n_points)

    start_idx = linear_regions['start_indices']
    end_idx = linear_regions['end_indices']

    x_start = x[start_idx]
    y_start = y[start_idx]
    x_end = x[end_idx]
    y_end = y[end_idx]

    # Calculate residuals
    y_start_pred = slope * x_start
    y_end_pred = slope * x_end

    residuals_start = y_start - y_start_pred
    residuals_end = y_end - y_end_pred

    rmse_start = np.sqrt(np.mean(residuals_start ** 2))
    rmse_end = np.sqrt(np.mean(residuals_end ** 2))

    return {
        'slope': slope,
        'n_start': len(start_idx),
        'n_end': len(end_idx),
        'start_field_range': (np.min(x_start), np.max(x_start)),
        'end_field_range': (np.min(x_end), np.max(x_end)),
        'start_r2': linear_regions['start_r2'],
        'end_r2': linear_regions['end_r2'],
        'rmse_start': rmse_start,
        'rmse_end': rmse_end,
        'start_indices': start_idx,
        'end_indices': end_idx
    }


def visualize_pm_dm_extraction(H, M, slope_result, save_path=None):
    """
    Visualize how PM/DM slope is extracted

    Parameters:
    -----------
    H, M : array-like
        Data
    slope_result : dict
        Result from extract_pm_dm_slope()
    save_path : str, optional
        Path to save figure

    Returns:
    --------
    matplotlib figure
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Plot 1: Full data with saturation regions highlighted
    ax1 = axes[0, 0]
    ax1.scatter(H, M, s=2, alpha=0.5, color='gray', label='All data')

    if 'sat_regions' in slope_result and slope_result['sat_regions'] is not None:
        sat = slope_result['sat_regions']
        ax1.scatter(sat['neg_H'], sat['neg_M'], s=20, color='blue',
                   label=f'Lower saturation (n={len(sat["neg_H"])})', zorder=3)
        ax1.scatter(sat['pos_H'], sat['pos_M'], s=20, color='red',
                   label=f'Upper saturation (n={len(sat["pos_H"])})', zorder=3)

    # Plot linear background
    H_line = np.array([np.min(H), np.max(H)])
    M_line = slope_result['chi_total'] * H_line
    ax1.plot(H_line, M_line, 'k--', linewidth=2,
            label=f'χ_total = {slope_result["chi_total"]:.6e}')

    ax1.set_xlabel('Magnetic Field (Oe)', fontsize=12)
    ax1.set_ylabel('Moment (emu)', fontsize=12)
    ax1.set_title('Saturation Regions for Slope Extraction', fontsize=13)
    ax1.legend(fontsize=9, loc='best')
    ax1.grid(True, alpha=0.3)

    # Plot 2: After PM/DM removal
    ax2 = axes[0, 1]
    M_corrected = remove_pm_dm_contribution(H, M, slope_result['chi_total'],
                                           remove_offset=False)
    ax2.scatter(H, M_corrected, s=2, alpha=0.6, color='black')
    ax2.axhline(y=0, color='r', linestyle='--', linewidth=1)
    ax2.set_xlabel('Magnetic Field (Oe)', fontsize=12)
    ax2.set_ylabel('Moment (emu)', fontsize=12)
    ax2.set_title('After PM/DM Removal', fontsize=13)
    ax2.grid(True, alpha=0.3)

    # Plot 3: High-field regions detail with THREE separate slopes
    ax3 = axes[1, 0]
    if 'sat_regions' in slope_result and slope_result['sat_regions'] is not None:
        sat = slope_result['sat_regions']

        # Get the slope values
        chi_lower = slope_result.get('chi_lower', slope_result['chi_total'])
        chi_upper = slope_result.get('chi_upper', slope_result['chi_total'])
        chi_final = slope_result['chi_total']

        # Get offsets
        offset_lower = slope_result.get('M_offset_lower', 0)
        offset_upper = slope_result.get('M_offset_upper', 0)

        # LOWER branch (negative field) - BLUE
        ax3.scatter(sat['neg_H'], sat['neg_M'], s=30, color='blue',
                   label=f'Lower data (n={len(sat["neg_H"])})', alpha=0.7, edgecolors='darkblue', linewidths=0.5)

        # Blue line: fit with offset
        H_lower_line = np.array([np.min(sat['neg_H']), np.max(sat['neg_H'])])
        M_lower_line = chi_lower * H_lower_line + offset_lower
        ax3.plot(H_lower_line, M_lower_line, 'b-', linewidth=2.5,
                label=f'Lower fit: χ = {chi_lower:.4e}', alpha=0.8)

        # UPPER branch (positive field) - RED
        ax3.scatter(sat['pos_H'], sat['pos_M'], s=30, color='red',
                   label=f'Upper data (n={len(sat["pos_H"])})', alpha=0.7, edgecolors='darkred', linewidths=0.5)

        # Red line: fit with offset
        H_upper_line = np.array([np.min(sat['pos_H']), np.max(sat['pos_H'])])
        M_upper_line = chi_upper * H_upper_line + offset_upper
        ax3.plot(H_upper_line, M_upper_line, 'r-', linewidth=2.5,
                label=f'Upper fit: χ = {chi_upper:.4e}', alpha=0.8)

        # FINAL averaged slope - BLACK DASHED (with averaged offset, spanning full range)
        offset_final = slope_result.get('M_offset', 0)
        H_final_line = np.array([np.min(sat['neg_H']), np.max(sat['pos_H'])])
        M_final_line = chi_final * H_final_line
        ax3.plot(H_final_line, M_final_line, 'k--', linewidth=2,
                label=f'FINAL (avg): χ = {chi_final:.4e}', alpha=0.9)

        ax3.axhline(y=0, color='gray', linestyle=':', linewidth=1, alpha=0.5)
        ax3.axvline(x=0, color='gray', linestyle=':', linewidth=1, alpha=0.5)

        ax3.set_xlabel('Magnetic Field (Oe)', fontsize=12)
        ax3.set_ylabel('Moment (emu)', fontsize=12)
        ax3.set_title('Three Separate Linear Fits (With Offsets)', fontsize=13, fontweight='bold')
        ax3.legend(fontsize=9, loc='best', framealpha=0.9)
        ax3.grid(True, alpha=0.3)

    # Plot 4: Diagnostics text
    ax4 = axes[1, 1]
    ax4.axis('off')

    # Determine if PM or DM dominant
    chi = slope_result['chi_total']
    if chi > 1e-10:
        contribution_type = "Paramagnetic (PM) dominated"
        interpretation = "Positive slope → unpaired electrons"
    elif chi < -1e-10:
        contribution_type = "Diamagnetic (DM) dominated"
        interpretation = "Negative slope → paired electrons"
    else:
        contribution_type = "No linear background"
        interpretation = "Pure ferromagnetic"

    diagnostics_text = f"""
    PM/DM EXTRACTION RESULTS
    {'='*50}
    
    SUSCEPTIBILITY (through origin):
    • χ_FINAL (avg) = {slope_result['chi_total']:.6e} emu/Oe
    • χ_upper (pos) = {slope_result.get('chi_upper', 0):.6e} emu/Oe
    • χ_lower (neg) = {slope_result.get('chi_lower', 0):.6e} emu/Oe
    • Difference    = {abs(slope_result.get('chi_upper', 0) - slope_result.get('chi_lower', 0)):.6e}
    
    INTERPRETATION:
    • Type: {contribution_type}
    • {interpretation}
    
    FIT QUALITY:
    • R² (upper) = {slope_result.get('r_squared_upper', 0):.6f}
    • R² (lower) = {slope_result.get('r_squared_lower', 0):.6f}
    • R² (avg)   = {slope_result.get('r_squared', 0):.6f}
    • Points (upper) = {slope_result.get('n_points_upper', 0)}
    • Points (lower) = {slope_result.get('n_points_lower', 0)}
    • Total points   = {slope_result.get('n_points', 0)}
    • Method = {slope_result.get('method', 'unknown')}
    """

    if 'asymmetry' in slope_result:
        diagnostics_text += f"""
    SYMMETRY CHECK:
    • Asymmetry = {slope_result.get('asymmetry', 0):.6e}
    """

    if 'M_offset' in slope_result:
        diagnostics_text += f"""
    OFFSET (with intercept):
    • M_offset (avg) = {slope_result['M_offset']:.6e} emu
    • M_offset_upper = {slope_result.get('M_offset_upper', 0):.6e} emu
    • M_offset_lower = {slope_result.get('M_offset_lower', 0):.6e} emu
    """

    ax4.text(0.05, 0.95, diagnostics_text, transform=ax4.transAxes,
            fontsize=9, verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')

    return fig


def process_vsm_with_pm_dm_removal(H, M, method='linear_saturation', **kwargs):
    """
    Complete workflow: extract and remove PM/DM contributions

    Parameters:
    -----------
    H, M : array-like
        VSM data
    method : str
        Extraction method
    **kwargs : additional parameters

    Returns:
    --------
    dict : Results including corrected data
    """
    # Extract PM/DM slope
    slope_result = extract_pm_dm_slope(H, M, method=method, **kwargs)

    # Remove PM/DM contribution
    M_corrected = remove_pm_dm_contribution(
        H, M,
        slope_result['chi_total'],
        remove_offset='M_offset' in slope_result,
        M_offset=slope_result.get('M_offset', 0)
    )

    # Try to separate PM and DM
    separation = separate_pm_dm_contributions(slope_result['chi_total'])

    return {
        'H': H,
        'M_raw': M,
        'M_corrected': M_corrected,
        'chi_total': slope_result['chi_total'],
        'slope_result': slope_result,
        'separation': separation
    }


# Version info
__version__ = '2.0.0'
__author__ = 'VSM Analysis Tools'
__all__ = [
    'extract_pm_dm_slope',
    'remove_pm_dm_contribution',
    'visualize_pm_dm_extraction',
    'process_vsm_with_pm_dm_removal',
    'identify_saturation_regions',
    'separate_pm_dm_contributions',
    'get_linear_region_diagnostics'
]


if __name__ == "__main__":
    # Self-test
    print(f"VSM Magnetic Contributions Module v{__version__}")
    print("Module loaded successfully!")
    print("\nAvailable functions:")
    for func in __all__:
        print(f"  - {func}")