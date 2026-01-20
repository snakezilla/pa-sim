"""
Photon Avalanche Parameter Extraction.

This module provides standardized methods for extracting key PA parameters
from simulation results, following the methodology recommended in:
    Szalkowski et al. (2025). Chemical Society Reviews, DOI: 10.1039/D4CS00177J

Key parameters:
    - Threshold power density (I_th): Where PA begins
    - Nonlinearity order (S): Slope of log-log power dependence
    - Rise time (τ_rise): Time to reach steady state

The standardization of these extraction methods addresses the reproducibility
issues identified in the PA research community.
"""

import numpy as np
from scipy.optimize import curve_fit
from scipy.signal import find_peaks
from dataclasses import dataclass
from typing import Optional

from pa_sim.core.simulation import SimulationResult


@dataclass
class PAParameters:
    """
    Extracted photon avalanche parameters.

    Attributes:
        threshold_W_cm2: Threshold power density in W/cm^2
        threshold_uncertainty: Uncertainty in threshold estimate
        nonlinearity_below: Nonlinearity order below threshold
        nonlinearity_above: Nonlinearity order above threshold (S parameter)
        nonlinearity_uncertainty: Uncertainty in S
        rise_time_s: Rise time in seconds (at threshold)
        rise_time_power_dependence: How rise time varies with power
        saturation_W_cm2: Power density where saturation begins
        dynamic_range: Ratio of saturation to threshold power
    """

    threshold_W_cm2: float
    threshold_uncertainty: Optional[float] = None
    nonlinearity_below: Optional[float] = None
    nonlinearity_above: float = 1.0
    nonlinearity_uncertainty: Optional[float] = None
    rise_time_s: Optional[float] = None
    rise_time_power_dependence: Optional[float] = None
    saturation_W_cm2: Optional[float] = None
    dynamic_range: Optional[float] = None

    def __str__(self) -> str:
        """Human-readable summary."""
        lines = [
            "Photon Avalanche Parameters:",
            f"  Threshold: {self.threshold_W_cm2:.2e} W/cm²",
            f"  Nonlinearity (S): {self.nonlinearity_above:.1f}",
        ]
        if self.rise_time_s:
            lines.append(f"  Rise time: {self.rise_time_s * 1e3:.2f} ms")
        if self.saturation_W_cm2:
            lines.append(f"  Saturation: {self.saturation_W_cm2:.2e} W/cm²")
        if self.dynamic_range:
            lines.append(f"  Dynamic range: {self.dynamic_range:.1f}x")
        return "\n".join(lines)


def extract_threshold(
    power_densities: np.ndarray,
    emission_intensities: np.ndarray,
    method: str = "derivative",
) -> tuple[float, float]:
    """
    Extract the PA threshold power density.

    The threshold is where the avalanching feedback loop becomes dominant,
    characterized by a rapid increase in the slope of the log-log plot.

    Args:
        power_densities: Array of power densities in W/cm^2
        emission_intensities: Array of steady-state emission intensities
        method: Extraction method:
            - "derivative": Maximum of d(log I)/d(log P)
            - "intersection": Intersection of linear fits below/above threshold
            - "inflection": Inflection point of the curve

    Returns:
        (threshold_power, uncertainty)
    """
    # Work in log space
    log_P = np.log10(power_densities)
    log_I = np.log10(emission_intensities + 1e-30)  # Avoid log(0)

    if method == "derivative":
        # Compute numerical derivative (slope in log-log space)
        d_log_I = np.gradient(log_I, log_P)

        # Find the maximum slope (steepest part of the curve)
        # The threshold is typically just before this maximum
        max_idx = np.argmax(d_log_I)

        # Refine by finding where slope exceeds some multiple of initial slope
        initial_slope = np.mean(d_log_I[:max(3, len(d_log_I) // 10)])
        threshold_idx = np.where(d_log_I > 2 * initial_slope)[0]

        if len(threshold_idx) > 0:
            thresh_idx = threshold_idx[0]
        else:
            thresh_idx = max_idx

        threshold = power_densities[thresh_idx]

        # Estimate uncertainty from width of transition region
        if max_idx > 0 and max_idx < len(power_densities) - 1:
            uncertainty = (power_densities[max_idx] - power_densities[thresh_idx]) / 2
        else:
            uncertainty = threshold * 0.1

        return threshold, uncertainty

    elif method == "intersection":
        # Fit two lines: below and above threshold region
        # Find approximate threshold first using derivative method
        d_log_I = np.gradient(log_I, log_P)
        max_slope_idx = np.argmax(d_log_I)

        # Fit line to data before the steep region
        n_below = max(3, max_slope_idx // 2)
        below_mask = np.arange(n_below)

        # Fit line to data after the steep region
        n_above = max(3, (len(log_P) - max_slope_idx) // 2)
        above_mask = np.arange(max_slope_idx + n_above // 2, len(log_P))

        if len(below_mask) < 2 or len(above_mask) < 2:
            # Fall back to derivative method
            return extract_threshold(power_densities, emission_intensities, "derivative")

        # Linear fits
        slope_below, intercept_below = np.polyfit(log_P[below_mask], log_I[below_mask], 1)
        slope_above, intercept_above = np.polyfit(log_P[above_mask], log_I[above_mask], 1)

        # Find intersection
        if abs(slope_above - slope_below) < 0.1:
            # Slopes too similar, fall back
            return extract_threshold(power_densities, emission_intensities, "derivative")

        log_P_thresh = (intercept_below - intercept_above) / (slope_above - slope_below)
        threshold = 10 ** log_P_thresh

        # Uncertainty from fit quality
        uncertainty = threshold * 0.1  # Placeholder

        return threshold, uncertainty

    elif method == "inflection":
        # Find inflection point (maximum of second derivative)
        d2_log_I = np.gradient(np.gradient(log_I, log_P), log_P)

        # Smooth to reduce noise
        from scipy.ndimage import gaussian_filter1d
        d2_smooth = gaussian_filter1d(d2_log_I, sigma=2)

        inflection_idx = np.argmax(d2_smooth)
        threshold = power_densities[inflection_idx]
        uncertainty = threshold * 0.15

        return threshold, uncertainty

    else:
        raise ValueError(f"Unknown method: {method}")


def extract_nonlinearity(
    power_densities: np.ndarray,
    emission_intensities: np.ndarray,
    threshold: Optional[float] = None,
    region: str = "above",
) -> tuple[float, float]:
    """
    Extract the nonlinearity order (S parameter) from power dependence.

    For PA emission: I ∝ P^S, where S can exceed 20-30 for strong PA.

    Args:
        power_densities: Array of power densities in W/cm^2
        emission_intensities: Array of steady-state emission intensities
        threshold: Known threshold (if None, will be estimated)
        region: Which region to fit:
            - "above": Above threshold (the PA regime)
            - "below": Below threshold (pre-avalanche)
            - "both": Return both values

    Returns:
        (nonlinearity, uncertainty)
    """
    if threshold is None:
        threshold, _ = extract_threshold(power_densities, emission_intensities)

    log_P = np.log10(power_densities)
    log_I = np.log10(emission_intensities + 1e-30)
    log_thresh = np.log10(threshold)

    if region == "above":
        mask = log_P > log_thresh
    elif region == "below":
        mask = log_P < log_thresh
    elif region == "both":
        S_below, unc_below = extract_nonlinearity(
            power_densities, emission_intensities, threshold, "below"
        )
        S_above, unc_above = extract_nonlinearity(
            power_densities, emission_intensities, threshold, "above"
        )
        return (S_below, S_above), (unc_below, unc_above)
    else:
        raise ValueError(f"Unknown region: {region}")

    if np.sum(mask) < 3:
        return np.nan, np.nan

    # Linear fit in log-log space: log(I) = S * log(P) + const
    coeffs, cov = np.polyfit(log_P[mask], log_I[mask], 1, cov=True)
    S = coeffs[0]
    uncertainty = np.sqrt(cov[0, 0])

    return S, uncertainty


def extract_rise_time(
    t: np.ndarray,
    population: np.ndarray,
    method: str = "90pct",
) -> float:
    """
    Extract the luminescence rise time from temporal dynamics.

    PA is characterized by slow rise times (tens to hundreds of ms at threshold)
    due to the multi-step energy looping process.

    Args:
        t: Time array in seconds
        population: Population (or emission) time series
        method: Extraction method:
            - "90pct": Time to reach 90% of steady state
            - "63pct": Time constant (1 - 1/e)
            - "fit": Fit exponential rise model

    Returns:
        Rise time in seconds
    """
    # Normalize to steady state
    steady_state = np.mean(population[-len(population) // 10:])
    if steady_state <= 0:
        return np.nan

    normalized = population / steady_state

    if method == "90pct":
        # Time to reach 90% of steady state
        idx_90 = np.where(normalized >= 0.9)[0]
        if len(idx_90) > 0:
            return t[idx_90[0]]
        return t[-1]

    elif method == "63pct":
        # Time constant (1 - 1/e ≈ 0.632)
        idx_63 = np.where(normalized >= 0.632)[0]
        if len(idx_63) > 0:
            return t[idx_63[0]]
        return t[-1]

    elif method == "fit":
        # Fit exponential rise: N(t) = N_ss * (1 - exp(-t/tau))
        def rise_model(t, tau):
            return 1 - np.exp(-t / tau)

        try:
            # Initial guess from 63% method
            tau_guess = extract_rise_time(t, population, "63pct")
            popt, _ = curve_fit(rise_model, t, normalized, p0=[tau_guess], maxfev=1000)
            return popt[0]
        except (RuntimeError, ValueError):
            return extract_rise_time(t, population, "63pct")

    else:
        raise ValueError(f"Unknown method: {method}")


def analyze_power_sweep(
    results: list[SimulationResult],
    emitting_level: str,
    radiative_rate: float = 1.0,
) -> PAParameters:
    """
    Comprehensive PA parameter extraction from a power sweep.

    This is the main analysis function that extracts all key PA parameters
    from a series of simulations at different power densities.

    Args:
        results: List of SimulationResults from Simulation.run_power_sweep()
        emitting_level: Name of the emitting level to analyze
        radiative_rate: Radiative rate for emission calculation (default: 1.0, gives relative units)

    Returns:
        PAParameters dataclass with all extracted values
    """
    # Extract power densities and steady-state emissions
    powers = np.array([r.power_density for r in results])
    emissions = np.array([
        r.total_emission(emitting_level, radiative_rate)[-1]  # Steady state
        for r in results
    ])

    # Extract threshold
    threshold, thresh_unc = extract_threshold(powers, emissions)

    # Extract nonlinearity
    S_below, _ = extract_nonlinearity(powers, emissions, threshold, "below")
    S_above, S_unc = extract_nonlinearity(powers, emissions, threshold, "above")

    # Find result closest to threshold for rise time
    thresh_idx = np.argmin(np.abs(powers - threshold))
    thresh_result = results[thresh_idx]
    pop = thresh_result.get_population(emitting_level)
    rise_time = extract_rise_time(thresh_result.t, pop)

    # Estimate saturation (where slope starts decreasing)
    log_P = np.log10(powers)
    log_I = np.log10(emissions + 1e-30)
    d_log_I = np.gradient(log_I, log_P)

    # Saturation is where slope drops below threshold nonlinearity
    above_thresh = powers > threshold
    if np.any(above_thresh):
        slopes_above = d_log_I[above_thresh]
        if len(slopes_above) > 3:
            max_slope_idx = np.argmax(slopes_above)
            # Look for where slope drops to half of max
            for i in range(max_slope_idx + 1, len(slopes_above)):
                if slopes_above[i] < slopes_above[max_slope_idx] / 2:
                    sat_idx = np.where(above_thresh)[0][i]
                    saturation = powers[sat_idx]
                    break
            else:
                saturation = None
        else:
            saturation = None
    else:
        saturation = None

    # Dynamic range
    dynamic_range = saturation / threshold if saturation else None

    return PAParameters(
        threshold_W_cm2=threshold,
        threshold_uncertainty=thresh_unc,
        nonlinearity_below=S_below,
        nonlinearity_above=S_above,
        nonlinearity_uncertainty=S_unc,
        rise_time_s=rise_time,
        saturation_W_cm2=saturation,
        dynamic_range=dynamic_range,
    )
