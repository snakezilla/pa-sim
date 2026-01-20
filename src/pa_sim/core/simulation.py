"""
Simulation orchestration for PA-Sim.

This module provides the main Simulation class that coordinates the setup
and execution of photon avalanching simulations using scipy's ODE solvers.

The system of ODEs is inherently "stiff" because process timescales differ
by many orders of magnitude (femtosecond absorption vs millisecond decay).
Therefore, implicit ODE solvers (Radau, BDF) are used for stability.
"""

import numpy as np
from scipy.integrate import solve_ivp
from dataclasses import dataclass, field
from typing import Optional, Literal
import time

from pa_sim.core.material import Material
from pa_sim.core.rate_equations import RateEquationSystem


@dataclass
class PumpLaser:
    """
    Pump laser configuration.

    Attributes:
        wavelength_nm: Pump wavelength in nanometers
        power_density_W_cm2: Power density in W/cm^2
        modulation: Optional time-dependent modulation function
    """

    wavelength_nm: float = 1064.0
    power_density_W_cm2: float = 1e4  # 10 kW/cm^2

    def __post_init__(self):
        if self.power_density_W_cm2 <= 0:
            raise ValueError("Power density must be positive")
        if self.wavelength_nm <= 0:
            raise ValueError("Wavelength must be positive")


@dataclass
class SolverConfig:
    """
    ODE solver configuration.

    Attributes:
        t_start: Start time in seconds
        t_end: End time in seconds
        method: Solver method ('Radau', 'BDF', or 'LSODA' for stiff systems)
        rtol: Relative tolerance
        atol: Absolute tolerance
        max_step: Maximum step size (None for automatic)
        dense_output: Whether to use dense output for interpolation
    """

    t_start: float = 0.0
    t_end: float = 1e-2  # 10 ms default
    method: Literal["Radau", "BDF", "LSODA"] = "Radau"
    rtol: float = 1e-8
    atol: float = 1e-12
    max_step: Optional[float] = None
    dense_output: bool = True


@dataclass
class SimulationResult:
    """
    Results from a PA simulation.

    Attributes:
        t: Time points array (seconds)
        populations: Population array, shape (n_levels, n_timepoints)
        level_names: Names of each level
        power_density: Pump power density used
        material_name: Name of the material simulated
        solver_info: Dictionary with solver statistics
    """

    t: np.ndarray
    populations: np.ndarray
    level_names: list[str]
    power_density: float
    material_name: str
    solver_info: dict = field(default_factory=dict)

    def get_population(self, level_name: str) -> np.ndarray:
        """Get population time series for a specific level."""
        try:
            idx = self.level_names.index(level_name)
            return self.populations[idx, :]
        except ValueError:
            raise ValueError(f"Level '{level_name}' not found. Available: {self.level_names}")

    def steady_state_populations(self, tail_fraction: float = 0.1) -> dict[str, float]:
        """
        Estimate steady-state populations from the tail of the simulation.

        Args:
            tail_fraction: Fraction of time series to average (default 10%)

        Returns:
            Dictionary mapping level names to steady-state populations
        """
        n_tail = max(1, int(len(self.t) * tail_fraction))
        ss = {}
        for i, name in enumerate(self.level_names):
            ss[name] = np.mean(self.populations[i, -n_tail:])
        return ss

    def total_emission(self, emitting_level: str, radiative_rate: float) -> np.ndarray:
        """
        Calculate emission intensity from a level.

        Args:
            emitting_level: Name of the emitting level
            radiative_rate: Radiative decay rate A in s^-1

        Returns:
            Emission intensity proportional to A * N(t)
        """
        pop = self.get_population(emitting_level)
        return radiative_rate * pop


class Simulation:
    """
    Main simulation class for photon avalanching dynamics.

    Example usage:
        >>> material = load_material("Tm_NaYF4_8pct")
        >>> sim = Simulation(material, PumpLaser(power_density_W_cm2=5e4))
        >>> result = sim.run()
        >>> plt.plot(result.t * 1e3, result.populations[2, :])  # ms, level 2

    Attributes:
        material: Material to simulate
        laser: Pump laser configuration
        solver_config: ODE solver configuration
        rate_system: The underlying rate equation system
    """

    def __init__(
        self,
        material: Material,
        laser: Optional[PumpLaser] = None,
        solver_config: Optional[SolverConfig] = None,
    ):
        """
        Initialize a simulation.

        Args:
            material: Material definition
            laser: Pump laser configuration (default: 1064 nm, 10 kW/cm^2)
            solver_config: Solver configuration (default: Radau, 10 ms)
        """
        self.material = material
        self.laser = laser or PumpLaser()
        self.solver_config = solver_config or SolverConfig()

        # Build the rate equation system
        self.rate_system = RateEquationSystem(
            material=material,
            pump_wavelength_nm=self.laser.wavelength_nm,
        )

    def run(
        self,
        initial_populations: Optional[np.ndarray] = None,
        t_eval: Optional[np.ndarray] = None,
    ) -> SimulationResult:
        """
        Run the simulation.

        Args:
            initial_populations: Custom initial populations (default: all in ground state)
            t_eval: Specific time points to evaluate (default: automatic)

        Returns:
            SimulationResult with time series of all level populations
        """
        # Set up initial conditions
        if initial_populations is None:
            N0 = self.rate_system.initial_populations()
        else:
            N0 = initial_populations

        # Get the derivative function
        deriv_func = self.rate_system.get_derivative_func(
            self.laser.power_density_W_cm2
        )

        # Set up time span
        t_span = (self.solver_config.t_start, self.solver_config.t_end)

        # Solver options
        options = {
            "rtol": self.solver_config.rtol,
            "atol": self.solver_config.atol,
            "dense_output": self.solver_config.dense_output,
        }
        if self.solver_config.max_step is not None:
            options["max_step"] = self.solver_config.max_step

        # Run the solver
        start_time = time.perf_counter()

        solution = solve_ivp(
            deriv_func,
            t_span,
            N0,
            method=self.solver_config.method,
            t_eval=t_eval,
            **options,
        )

        elapsed = time.perf_counter() - start_time

        if not solution.success:
            raise RuntimeError(f"ODE solver failed: {solution.message}")

        # Package results
        return SimulationResult(
            t=solution.t,
            populations=solution.y,
            level_names=self.rate_system.get_level_names(),
            power_density=self.laser.power_density_W_cm2,
            material_name=self.material.name,
            solver_info={
                "method": self.solver_config.method,
                "nfev": solution.nfev,
                "njev": getattr(solution, "njev", None),
                "nlu": getattr(solution, "nlu", None),
                "elapsed_seconds": elapsed,
                "n_timepoints": len(solution.t),
            },
        )

    def run_power_sweep(
        self,
        power_densities: np.ndarray,
        t_end: Optional[float] = None,
        progress_callback: Optional[callable] = None,
    ) -> list[SimulationResult]:
        """
        Run simulations across a range of power densities.

        This is essential for characterizing PA behavior: threshold, nonlinearity.

        Args:
            power_densities: Array of power densities in W/cm^2
            t_end: Override simulation end time (should be long enough for steady state)
            progress_callback: Optional callback(i, n, power) for progress reporting

        Returns:
            List of SimulationResults, one per power density
        """
        results = []
        original_power = self.laser.power_density_W_cm2
        original_t_end = self.solver_config.t_end

        if t_end is not None:
            self.solver_config.t_end = t_end

        try:
            for i, power in enumerate(power_densities):
                if progress_callback:
                    progress_callback(i, len(power_densities), power)

                self.laser.power_density_W_cm2 = power
                # Rebuild rate system with new power (flux changes)
                result = self.run()
                results.append(result)
        finally:
            # Restore original settings
            self.laser.power_density_W_cm2 = original_power
            self.solver_config.t_end = original_t_end

        return results

    def run_temporal_dynamics(
        self,
        t_points: np.ndarray,
    ) -> SimulationResult:
        """
        Run simulation with specific time points for detailed temporal analysis.

        Useful for analyzing rise times and decay dynamics.

        Args:
            t_points: Array of time points in seconds

        Returns:
            SimulationResult evaluated at the specified time points
        """
        self.solver_config.t_end = t_points[-1]
        return self.run(t_eval=t_points)
