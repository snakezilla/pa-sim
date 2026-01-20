"""
Visualization tools for PA-Sim.

Standard plots for photon avalanching analysis:
    - Power dependence (log-log)
    - Temporal dynamics (rise/decay)
    - Energy level diagrams
"""

import numpy as np
from typing import Optional, Union
import warnings

# Try to import matplotlib, provide helpful error if not available
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.collections import LineCollection
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

from pa_sim.core.simulation import SimulationResult
from pa_sim.analysis.pa_parameters import PAParameters


def _check_matplotlib():
    """Check if matplotlib is available."""
    if not HAS_MATPLOTLIB:
        raise ImportError(
            "Visualization requires matplotlib. Install with: pip install matplotlib"
        )


def plot_power_dependence(
    power_densities: np.ndarray,
    emissions: np.ndarray,
    pa_params: Optional[PAParameters] = None,
    ax: Optional["plt.Axes"] = None,
    title: str = "Power Dependence",
    xlabel: str = "Power Density (W/cm²)",
    ylabel: str = "Emission Intensity (a.u.)",
    show_threshold: bool = True,
    show_slopes: bool = True,
    **kwargs,
) -> "plt.Axes":
    """
    Plot emission intensity vs pump power (log-log scale).

    This is the canonical PA characterization plot showing:
    - Threshold power density
    - Nonlinearity order (slope)
    - Saturation region

    Args:
        power_densities: Array of power densities in W/cm^2
        emissions: Array of emission intensities
        pa_params: Optional PAParameters for annotating threshold/slopes
        ax: Matplotlib axes (creates new figure if None)
        title: Plot title
        xlabel: X-axis label
        ylabel: Y-axis label
        show_threshold: Annotate threshold on plot
        show_slopes: Show slope fits
        **kwargs: Additional kwargs passed to plt.loglog()

    Returns:
        Matplotlib axes object
    """
    _check_matplotlib()

    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 6))

    # Main data plot
    ax.loglog(power_densities, emissions, 'o-', **kwargs)

    # Annotate threshold
    if show_threshold and pa_params and pa_params.threshold_W_cm2:
        ax.axvline(
            pa_params.threshold_W_cm2,
            color='red',
            linestyle='--',
            alpha=0.7,
            label=f'Threshold: {pa_params.threshold_W_cm2:.1e} W/cm²'
        )

    # Show slope annotations
    if show_slopes and pa_params:
        if pa_params.nonlinearity_above and not np.isnan(pa_params.nonlinearity_above):
            ax.text(
                0.95, 0.05,
                f'S = {pa_params.nonlinearity_above:.1f}',
                transform=ax.transAxes,
                fontsize=12,
                verticalalignment='bottom',
                horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
            )

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)

    return ax


def plot_temporal_dynamics(
    result: SimulationResult,
    levels: Optional[list[str]] = None,
    ax: Optional["plt.Axes"] = None,
    time_unit: str = "ms",
    normalize: bool = False,
    title: Optional[str] = None,
    **kwargs,
) -> "plt.Axes":
    """
    Plot population/emission dynamics over time.

    Shows the characteristic slow rise time of PA emission.

    Args:
        result: SimulationResult from a simulation
        levels: List of level names to plot (default: all)
        ax: Matplotlib axes (creates new figure if None)
        time_unit: Time unit for x-axis ("s", "ms", "us")
        normalize: Normalize each curve to its maximum
        title: Plot title
        **kwargs: Additional kwargs passed to plt.plot()

    Returns:
        Matplotlib axes object
    """
    _check_matplotlib()

    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))

    # Time unit conversion
    time_scale = {"s": 1, "ms": 1e3, "us": 1e6}.get(time_unit, 1)
    t = result.t * time_scale

    # Select levels to plot
    if levels is None:
        levels = result.level_names

    for level_name in levels:
        try:
            pop = result.get_population(level_name)
            if normalize and pop.max() > 0:
                pop = pop / pop.max()
            ax.plot(t, pop, label=level_name, **kwargs)
        except ValueError:
            warnings.warn(f"Level '{level_name}' not found, skipping")

    ax.set_xlabel(f"Time ({time_unit})")
    ax.set_ylabel("Population" + (" (normalized)" if normalize else " (ions/cm³)"))
    ax.set_title(title or f"Temporal Dynamics at {result.power_density:.1e} W/cm²")
    ax.legend()
    ax.grid(True, alpha=0.3)

    return ax


def plot_energy_levels(
    material: "Material",
    ax: Optional["plt.Axes"] = None,
    show_transitions: bool = True,
    highlight_pa_loop: bool = True,
    figsize: tuple = (10, 8),
) -> "plt.Axes":
    """
    Plot energy level diagram for a material.

    Visualizes the energy levels and key transitions including the PA loop.

    Args:
        material: Material to visualize
        ax: Matplotlib axes (creates new figure if None)
        show_transitions: Draw arrows for transitions
        highlight_pa_loop: Highlight the CR feedback loop
        figsize: Figure size if creating new figure

    Returns:
        Matplotlib axes object
    """
    _check_matplotlib()
    from pa_sim.core.material import TransitionType

    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)

    # Colors for different transition types
    transition_colors = {
        TransitionType.RADIATIVE: 'green',
        TransitionType.NON_RADIATIVE: 'gray',
        TransitionType.GSA: 'blue',
        TransitionType.ESA: 'purple',
        TransitionType.CR: 'red',
        TransitionType.ETU: 'orange',
    }

    # Plot levels for each ion
    x_offset = 0
    ion_width = 2.0
    level_width = 1.5

    for ion in material.dopants:
        x_center = x_offset + ion_width / 2

        # Draw energy levels as horizontal lines
        for level in ion.levels:
            y = level.energy_cm_inv / 1000  # Convert to units of 1000 cm^-1
            x_left = x_center - level_width / 2
            x_right = x_center + level_width / 2

            ax.hlines(y, x_left, x_right, colors='black', linewidth=2)
            ax.text(
                x_right + 0.1, y,
                level.name,
                verticalalignment='center',
                fontsize=10
            )

        # Draw transitions as arrows
        if show_transitions:
            for t in ion.transitions:
                from_level = ion.levels[t.from_level]
                to_level = ion.levels[t.to_level]

                y_from = from_level.energy_cm_inv / 1000
                y_to = to_level.energy_cm_inv / 1000

                color = transition_colors.get(t.transition_type, 'black')
                style = '->' if y_to > y_from else '->'

                # Offset arrows horizontally to avoid overlap
                x_arrow = x_center + 0.1 * (hash(str(t.rate)) % 5 - 2)

                if t.transition_type == TransitionType.CR and highlight_pa_loop:
                    # Highlight CR with thicker arrow
                    ax.annotate(
                        '', xy=(x_arrow, y_to), xytext=(x_arrow, y_from),
                        arrowprops=dict(arrowstyle=style, color=color, lw=2)
                    )
                else:
                    ax.annotate(
                        '', xy=(x_arrow, y_to), xytext=(x_arrow, y_from),
                        arrowprops=dict(arrowstyle=style, color=color, lw=1, alpha=0.7)
                    )

        # Ion label
        ax.text(
            x_center, -0.5,
            ion.symbol,
            horizontalalignment='center',
            fontsize=12,
            fontweight='bold'
        )

        x_offset += ion_width + 1

    # Legend for transition types
    legend_handles = [
        mpatches.Patch(color=color, label=ttype.value.replace('_', ' ').title())
        for ttype, color in transition_colors.items()
    ]
    ax.legend(handles=legend_handles, loc='upper right')

    ax.set_ylabel("Energy (×1000 cm⁻¹)")
    ax.set_title(f"Energy Level Diagram: {material.name}")
    ax.set_xlim(-0.5, x_offset)
    ax.set_xticks([])

    return ax


def plot_power_sweep_summary(
    results: list[SimulationResult],
    emitting_level: str,
    radiative_rate: float = 1.0,
    figsize: tuple = (14, 5),
) -> "plt.Figure":
    """
    Create a comprehensive summary figure from a power sweep.

    Three-panel figure showing:
    1. Power dependence (log-log)
    2. Temporal dynamics at different powers
    3. Rise time vs power

    Args:
        results: List of SimulationResults from power sweep
        emitting_level: Name of the emitting level
        radiative_rate: Radiative rate for emission calculation
        figsize: Figure size

    Returns:
        Matplotlib figure object
    """
    _check_matplotlib()
    from pa_sim.analysis.pa_parameters import analyze_power_sweep, extract_rise_time

    fig, axes = plt.subplots(1, 3, figsize=figsize)

    # Extract data
    powers = np.array([r.power_density for r in results])
    emissions = np.array([
        r.total_emission(emitting_level, radiative_rate)[-1]
        for r in results
    ])

    # Panel 1: Power dependence
    pa_params = analyze_power_sweep(results, emitting_level, radiative_rate)
    plot_power_dependence(
        powers, emissions, pa_params,
        ax=axes[0], title="(a) Power Dependence"
    )

    # Panel 2: Temporal dynamics at selected powers
    # Select low, threshold, and high power
    sorted_idx = np.argsort(powers)
    idx_low = sorted_idx[0]
    idx_thresh = sorted_idx[len(sorted_idx) // 2]
    idx_high = sorted_idx[-1]

    for idx, label in [(idx_low, 'Low'), (idx_thresh, 'Threshold'), (idx_high, 'High')]:
        r = results[idx]
        pop = r.get_population(emitting_level)
        t_ms = r.t * 1e3
        axes[1].plot(t_ms, pop / pop.max(), label=f'{label} ({r.power_density:.0e} W/cm²)')

    axes[1].set_xlabel("Time (ms)")
    axes[1].set_ylabel("Normalized Emission")
    axes[1].set_title("(b) Temporal Dynamics")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    # Panel 3: Rise time vs power
    rise_times = []
    for r in results:
        pop = r.get_population(emitting_level)
        tau = extract_rise_time(r.t, pop)
        rise_times.append(tau * 1e3)  # Convert to ms

    axes[2].semilogx(powers, rise_times, 'o-')
    if pa_params.threshold_W_cm2:
        axes[2].axvline(pa_params.threshold_W_cm2, color='red', linestyle='--', alpha=0.7)
    axes[2].set_xlabel("Power Density (W/cm²)")
    axes[2].set_ylabel("Rise Time (ms)")
    axes[2].set_title("(c) Rise Time")
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    return fig
