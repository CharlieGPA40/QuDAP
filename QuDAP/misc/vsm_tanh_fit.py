"""
VSM Tanh Fitting and Magnetic Parameter Extraction
===================================================

Fits data with YOUR tanh model and extracts:
- Coercivity (Hc) - two methods
- Exchange bias (Heb)
- Saturation magnetization (Ms)
- Vertical offset correction

Your Model: M = m * tanh(s*(H - c)) + a*H + b
where: m=Ms, s=slope parameter, c=Heb, a=residual slope, b=offset

Author: VSM Analysis Tools
Version: 2.0
Date: 2024
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.interpolate import interp1d


def tanh_model(H, m, s, c, a=0, b=0):
    """
    YOUR tanh model for hysteresis loop

    M = m * tanh(s*(H - c)) + a*H + b

    Parameters:
    -----------
    H : array
        Magnetic field
    m : float
        Saturation magnetization (Ms)
    s : float
        Slope parameter (steepness of tanh)
    c : float
        Coercivity (Hc) - NOT exchange bias!
    a : float
        Linear slope (residual PM/DM if not fully removed, default 0)
    b : float
        Vertical offset (default 0)

    Returns:
    --------
    M : array
        Magnetization

    Note:
    -----
    This is YOUR model matching OriginLab fitting
    - c is Hc (coercivity), not Heb
    - Heb (exchange bias) is calculated from upper and lower branch c values:
      Heb = (c_lower + c_upper) / 2  (if they differ)
    """
    return m * np.tanh(s * (H - c)) + a * H + b


def find_coercivity_from_data(H, M, method='interpolation'):
    """
    Find coercivity from data where M = 0

    Parameters:
    -----------
    H, M : arrays
        Field and magnetization
    method : str
        'interpolation' or 'nearest'

    Returns:
    --------
    float or None : Coercivity value (returns None if not found)
    """
    # Look for zero crossings
    sign_changes = np.where(np.diff(np.sign(M)))[0]

    if len(sign_changes) == 0:
        return None

    Hc_values = []

    for idx in sign_changes:
        if method == 'interpolation':
            # Linear interpolation between the two points
            H1, H2 = H[idx], H[idx + 1]
            M1, M2 = M[idx], M[idx + 1]

            if M2 != M1:  # Avoid division by zero
                Hc = H1 - M1 * (H2 - H1) / (M2 - M1)
                Hc_values.append(Hc)
        else:  # nearest
            # Take the point closer to zero
            if abs(M[idx]) < abs(M[idx + 1]):
                Hc_values.append(H[idx])
            else:
                Hc_values.append(H[idx + 1])

    if len(Hc_values) == 0:
        return None

    # Return average if multiple crossings
    return np.mean(Hc_values)


def extract_coercivity_method1_fit(H, M, initial_guess=None, include_slope=False):
    """
    Method 1: Extract coercivity from YOUR tanh model fitting

    Parameters:
    -----------
    H, M : arrays
        Field and magnetization data (single branch)
    initial_guess : dict, optional
        Initial parameters {'m': ..., 's': ..., 'c': ..., 'a': ..., 'b': ...}
    include_slope : bool
        Whether to include linear slope term (a*H) and offset (b) in fit
        False: M = m*tanh(s*(H-c))           [3 parameters]
        True:  M = m*tanh(s*(H-c)) + a*H + b [5 parameters - YOUR FULL MODEL]

    Returns:
    --------
    dict : Fitting results and coercivity
    """
    # Prepare initial guess
    if initial_guess is None:
        m_guess = (np.max(M) - np.min(M)) / 2
        H_range = np.max(H) - np.min(H)
        s_guess = 4.0 / H_range  # s ≈ 1/Hc, assume Hc ≈ H_range/4
        c_guess = np.mean(H)  # Start at center
        a_guess = 0
        b_guess = 0
    else:
        m_guess = initial_guess.get('m', (np.max(M) - np.min(M)) / 2)
        s_guess = initial_guess.get('s', 0.005)
        c_guess = initial_guess.get('c', 0)
        a_guess = initial_guess.get('a', 0)
        b_guess = initial_guess.get('b', 0)

    try:
        if include_slope:
            # YOUR FULL MODEL - all 5 parameters
            popt, pcov = curve_fit(
                lambda H, m, s, c, a, b: tanh_model(H, m, s, c, a, b),
                H, M,
                p0=[m_guess, s_guess, c_guess, a_guess, b_guess],
                maxfev=10000,
                bounds=([0, 0.0001, -np.max(np.abs(H)), -np.inf, -np.inf],
                        [np.inf, 10, np.max(np.abs(H)), np.inf, np.inf])
            )

            m_fit, s_fit, c_fit, a_fit, b_fit = popt
            perr = np.sqrt(np.diag(pcov))

        else:
            # SIMPLIFIED MODEL - 3 parameters (after PM/DM removal)
            popt, pcov = curve_fit(
                lambda H, m, s, c: tanh_model(H, m, s, c, 0, 0),
                H, M,
                p0=[m_guess, s_guess, c_guess],
                maxfev=10000,
                bounds=([0, 0.0001, -np.max(np.abs(H))],
                        [np.inf, 10, np.max(np.abs(H))])
            )

            m_fit, s_fit, c_fit = popt
            a_fit, b_fit = 0, 0
            perr = np.sqrt(np.diag(pcov))
            # Pad perr to 5 elements
            perr = np.concatenate([perr, [0, 0]])

        # Calculate fit
        M_fit = tanh_model(H, m_fit, s_fit, c_fit, a_fit, b_fit)

        # Calculate R²
        ss_res = np.sum((M - M_fit) ** 2)
        ss_tot = np.sum((M - np.mean(M)) ** 2)
        r_squared = 1 - (ss_res / ss_tot)

        return {
            'success': True,
            'm': m_fit,              # Ms (saturation magnetization)
            's': s_fit,              # Slope parameter (steepness)
            'c': c_fit,              # Hc (coercivity) - NOT Heb!
            'a': a_fit,              # Linear slope
            'b': b_fit,              # Offset
            'Hc': abs(c_fit),        # Coercivity (same as c)
            'Ms': m_fit,             # Saturation (same as m)
            'm_err': perr[0],
            's_err': perr[1],
            'c_err': perr[2],
            'a_err': perr[3],
            'b_err': perr[4],
            'r_squared': r_squared,
            'M_fit': M_fit,
            'include_slope': include_slope,
            'method': 'tanh_fit'
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'include_slope': include_slope,
            'method': 'tanh_fit'
        }


def extract_coercivity_method2_data(H_upper, M_upper, H_lower, M_lower):
    """
    Method 2: Extract coercivity from data (M=0 crossings)
    Works on already-split upper and lower branches

    Parameters:
    -----------
    H_upper, M_upper : arrays
        Upper branch data
    H_lower, M_lower : arrays
        Lower branch data

    Returns:
    --------
    dict : Coercivity results
    """
    # Find Hc for upper branch (left coercivity)
    Hc_left = find_coercivity_from_data(H_upper, M_upper)

    # Find Hc for lower branch (right coercivity)
    Hc_right = find_coercivity_from_data(H_lower, M_lower)

    # Calculate coercivity and exchange bias
    if Hc_left is not None and Hc_right is not None:
        # Hc = (|Hc_left| + |Hc_right|) / 2
        Hc = abs(Hc_left) + abs(Hc_right)

        # Heb = (Hc_right + Hc_left) / 2
        Heb = (Hc_right + Hc_left) / 2

        return {
            'success': True,
            'Hc': Hc,
            'Hc_left': Hc_left,
            'Hc_right': Hc_right,
            'Heb': Heb,
            'method': 'data_crossing'
        }
    else:
        return {
            'success': False,
            'Hc_left': Hc_left,
            'Hc_right': Hc_right,
            'error': 'Could not find M=0 crossings',
            'method': 'data_crossing'
        }


def extract_saturation_magnetization(H, M, high_field_fraction=0.8, n_points=5):
    """
    Extract saturation magnetization from high-field regions
    Uses multiple points to exclude outliers (YOUR SUGGESTION)

    Parameters:
    -----------
    H, M : arrays
        Field and magnetization
    high_field_fraction : float
        Fraction of max field to consider as "high field" (default 0.8)
    n_points : int
        Number of highest points to average (default 5)
        Takes 2nd through (n_points+1)th to exclude potential outlier

    Returns:
    --------
    dict : Ms values for upper and lower saturation
    """
    H_max = np.max(np.abs(H))
    threshold = high_field_fraction * H_max

    # Upper saturation (positive field)
    upper_mask = H > threshold
    if np.sum(upper_mask) >= n_points:
        # Get top n_points values (excluding potential outliers)
        M_upper_candidates = M[upper_mask]
        M_upper_sorted = np.sort(M_upper_candidates)[::-1]  # Descending order

        # Take 2nd to (n_points+1)th highest to exclude outliers
        if len(M_upper_sorted) > n_points:
            Ms_upper = np.mean(M_upper_sorted[1:n_points+1])
        else:
            Ms_upper = np.mean(M_upper_sorted)
    else:
        Ms_upper = np.max(M)

    # Lower saturation (negative field)
    lower_mask = H < -threshold
    if np.sum(lower_mask) >= n_points:
        # Get bottom n_points values (most negative, excluding outliers)
        M_lower_candidates = M[lower_mask]
        M_lower_sorted = np.sort(M_lower_candidates)  # Ascending order (most negative first)

        # Take 2nd to (n_points+1)th lowest to exclude outliers
        if len(M_lower_sorted) > n_points:
            Ms_lower = np.mean(M_lower_sorted[1:n_points+1])
        else:
            Ms_lower = np.mean(M_lower_sorted)
    else:
        Ms_lower = np.min(M)

    # Average Ms
    Ms_avg = (Ms_upper - Ms_lower) / 2

    # Vertical offset (should be ~0 after PM/DM removal)
    vertical_offset = (Ms_upper + Ms_lower) / 2

    return {
        'Ms_upper': Ms_upper,
        'Ms_lower': Ms_lower,
        'Ms_avg': Ms_avg,
        'Ms_difference': Ms_upper - Ms_lower,
        'vertical_offset': vertical_offset,
        'n_points_used': n_points
    }


def correct_vertical_offset(M, vertical_offset):
    """
    Correct vertical offset in magnetization data

    Parameters:
    -----------
    M : array
        Magnetization data
    vertical_offset : float
        Offset to remove

    Returns:
    --------
    array : Corrected magnetization
    """
    return M - vertical_offset


def process_vsm_branches(H_upper, M_upper, H_lower, M_lower, include_slope=False):
    """
    Complete VSM processing workflow for ALREADY-SPLIT branches

    Parameters:
    -----------
    H_upper, M_upper : arrays
        Upper branch data (increasing H)
    H_lower, M_lower : arrays
        Lower branch data (decreasing H)
    include_slope : bool
        Whether to include a and b parameters in fitting

    Returns:
    --------
    dict : Complete analysis results
    """
    print("\n" + "="*60)
    print("VSM BRANCH PROCESSING (Your Model)")
    print("="*60)

    # Combine for Ms extraction
    H_full = np.concatenate([H_upper, H_lower])
    M_full = np.concatenate([M_upper, M_lower])

    # Step 1: Extract Ms
    print("\n[Step 1] Extracting saturation magnetization...")
    Ms_result = extract_saturation_magnetization(H_full, M_full, n_points=5)
    print(f"  Ms_upper: {Ms_result['Ms_upper']:.6e} emu")
    print(f"  Ms_lower: {Ms_result['Ms_lower']:.6e} emu")
    print(f"  Ms_avg:   {Ms_result['Ms_avg']:.6e} emu")
    print(f"  Vertical offset: {Ms_result['vertical_offset']:.6e} emu")

    # Step 2: Correct vertical offset if needed
    if abs(Ms_result['vertical_offset']) > 1e-10:
        print(f"\n[Step 2] Correcting vertical offset...")
        M_upper_corrected = correct_vertical_offset(M_upper, Ms_result['vertical_offset'])
        M_lower_corrected = correct_vertical_offset(M_lower, Ms_result['vertical_offset'])
        print(f"  Offset removed: {Ms_result['vertical_offset']:.6e} emu")
    else:
        M_upper_corrected = M_upper.copy()
        M_lower_corrected = M_lower.copy()
        print(f"\n[Step 2] No vertical offset correction needed")

    # Re-calculate Ms after correction
    M_full_corrected = np.concatenate([M_upper_corrected, M_lower_corrected])
    Ms_result_corrected = extract_saturation_magnetization(H_full, M_full_corrected, n_points=5)

    # Step 3: Method 1 - Fit upper branch
    print("\n[Step 3] Method 1: Fitting upper branch with YOUR tanh model...")
    upper_fit = extract_coercivity_method1_fit(H_upper, M_upper_corrected, include_slope=include_slope)

    if upper_fit['success']:
        print(f"  ✓ Upper fit successful!")
        print(f"    m (Ms): {upper_fit['m']:.6e} emu")
        print(f"    s:      {upper_fit['s']:.6f}")
        print(f"    c (Heb):{upper_fit['c']:.2f} Oe")
        print(f"    Hc:     {upper_fit['Hc']:.2f} Oe")
        if include_slope:
            print(f"    a:      {upper_fit['a']:.6e} emu/Oe")
            print(f"    b:      {upper_fit['b']:.6e} emu")
        print(f"    R²:     {upper_fit['r_squared']:.6f}")
    else:
        print(f"  ✗ Upper fit failed: {upper_fit.get('error', 'Unknown error')}")

    # Step 4: Method 1 - Fit lower branch
    print("\n[Step 4] Method 1: Fitting lower branch with YOUR tanh model...")
    lower_fit = extract_coercivity_method1_fit(H_lower, M_lower_corrected, include_slope=include_slope)

    if lower_fit['success']:
        print(f"  ✓ Lower fit successful!")
        print(f"    m (Ms): {lower_fit['m']:.6e} emu")
        print(f"    s:      {lower_fit['s']:.6f}")
        print(f"    c (Heb):{lower_fit['c']:.2f} Oe")
        print(f"    Hc:     {lower_fit['Hc']:.2f} Oe")
        if include_slope:
            print(f"    a:      {lower_fit['a']:.6e} emu/Oe")
            print(f"    b:      {lower_fit['b']:.6e} emu")
        print(f"    R²:     {lower_fit['r_squared']:.6f}")
    else:
        print(f"  ✗ Lower fit failed: {lower_fit.get('error', 'Unknown error')}")

    # Step 5: Method 2 - Data crossing
    print("\n[Step 5] Method 2: Finding Hc from M=0 crossings...")
    method2_result = extract_coercivity_method2_data(H_upper, M_upper_corrected,
                                                     H_lower, M_lower_corrected)

    if method2_result['success']:
        print(f"  ✓ Crossings found!")
        print(f"    Hc_left:  {method2_result['Hc_left']:.2f} Oe")
        print(f"    Hc_right: {method2_result['Hc_right']:.2f} Oe")
        print(f"    Hc (avg): {method2_result['Hc']:.2f} Oe")
        print(f"    Heb:      {method2_result['Heb']:.2f} Oe")
    else:
        print(f"  ✗ Could not find crossings: {method2_result.get('error', 'Unknown')}")

    # Step 6: Determine final values
    print("\n[Step 6] Determining final parameters...")
    Hc_values = []
    Ms_values = []

    # Hc from upper branch fit
    if upper_fit['success'] and upper_fit['r_squared'] > 0.90:
        Hc_values.append(upper_fit['Hc'])
        Ms_values.append(upper_fit['Ms'])
        print(f"  Upper fit Hc: {upper_fit['Hc']:.2f} Oe (c = {upper_fit['c']:.2f})")

    # Hc from lower branch fit
    if lower_fit['success'] and lower_fit['r_squared'] > 0.90:
        Hc_values.append(lower_fit['Hc'])
        Ms_values.append(lower_fit['Ms'])
        print(f"  Lower fit Hc: {lower_fit['Hc']:.2f} Oe (c = {lower_fit['c']:.2f})")

    # Hc from Method 2 (data crossings)
    if method2_result['success']:
        Hc_values.append(method2_result['Hc'])
        print(f"  Method 2 Hc:  {method2_result['Hc']:.2f} Oe")

    # Add Ms from direct calculation
    Ms_values.append(Ms_result_corrected['Ms_avg'])

    # Calculate final Hc and Ms
    if len(Hc_values) > 0:
        Hc_final = np.mean(Hc_values)
        Ms_final = np.mean(Ms_values)
    else:
        Hc_final = None
        Ms_final = Ms_result_corrected['Ms_avg']
        print(f"\n  ✗ Could not determine coercivity from fits")

    # Calculate Heb from the shift between upper and lower branch c values
    # Heb = (c_lower + c_upper) / 2  (if branches are shifted)
    if upper_fit['success'] and lower_fit['success']:
        # The shift in c values indicates exchange bias
        Heb_from_fits = (lower_fit['c'] + upper_fit['c']) / 2
        print(f"  Heb from c shifts: {Heb_from_fits:.2f} Oe")
    else:
        Heb_from_fits = None

    # Heb from Method 2
    Heb_final = None
    if method2_result['success']:
        Heb_final = method2_result['Heb']
        print(f"  Heb from Method 2: {Heb_final:.2f} Oe")
    elif Heb_from_fits is not None:
        Heb_final = Heb_from_fits
    else:
        Heb_final = 0.0

    if Hc_final is not None:
        print(f"\n  FINAL Hc (averaged):  {Hc_final:.2f} Oe")
        print(f"  FINAL Heb:            {Heb_final:.2f} Oe")
        print(f"  FINAL Ms (averaged):  {Ms_final:.6e} emu")
    else:
        Hc_final = None
        Heb_final = None
        Ms_final = Ms_result_corrected['Ms_avg']
        print(f"\n  ✗ Could not determine coercivity from fits")
        print(f"  Using Ms from saturation: {Ms_final:.6e} emu")

    # Return comprehensive results
    return {
        'H_upper': H_upper,
        'M_upper_original': M_upper,
        'M_upper_corrected': M_upper_corrected,
        'H_lower': H_lower,
        'M_lower_original': M_lower,
        'M_lower_corrected': M_lower_corrected,
        'Ms_result': Ms_result_corrected,
        'upper_fit': upper_fit,
        'lower_fit': lower_fit,
        'method2_data': method2_result,
        'Hc_final': Hc_final,
        'Heb_final': Heb_final,
        'Ms_final': Ms_final,
        'vertical_offset_removed': Ms_result['vertical_offset']
    }


# Version info
__version__ = '2.0.0'
__author__ = 'VSM Analysis Tools'
__all__ = [
    'tanh_model',
    'find_coercivity_from_data',
    'extract_coercivity_method1_fit',
    'extract_coercivity_method2_data',
    'extract_saturation_magnetization',
    'correct_vertical_offset',
    'process_vsm_branches'
]


if __name__ == "__main__":
    print(f"VSM Tanh Fitting Module v{__version__}")
    print("Module loaded successfully!")
    print("\nAvailable functions:")
    for func in __all__:
        print(f"  - {func}")