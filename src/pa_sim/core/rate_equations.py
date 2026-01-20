"""
Rate equation system for photon avalanching dynamics.

This module implements the coupled, non-linear ordinary differential equations
(ODEs) that govern the population dynamics of energy levels in lanthanide ions.

The governing equation for each energy level i is:
    dN_i/dt = Σ(Processes Populating Level i) - Σ(Processes Depopulating Level i)

Physical processes modeled:
    - Ground State Absorption (GSA): σ_GSA * Φ * N_0
    - Excited State Absorption (ESA): σ_ESA * Φ * N_i
    - Spontaneous Emission: A_ij * N_i
    - Non-Radiative Relaxation: W_nr * N_i
    - Energy Transfer Upconversion (ETU): W_ETU * N_i * N_j
    - Cross-Relaxation (CR): W_CR * N_i * N_0 (key PA feedback loop)

References:
    [1] Lee, C., et al. (2021). Nature, 589, 230-235.
    [2] Skripka, A., & Chan, E. M. (2025). Materials Horizons, 12, 3575-3597.
"""

import numpy as np
from typing import Callable, Optional
from dataclasses import dataclass

from pa_sim.core.material import Material, LanthanideIon, TransitionType


# Physical constants
H_PLANCK = 6.62607015e-34  # J*s
C_LIGHT = 2.99792458e8     # m/s


@dataclass
class RateEquationSystem:
    """
    Builds and evaluates the rate equation system for a material.

    This class constructs the system of coupled ODEs from a Material definition
    and provides the derivative function needed by scipy's ODE solvers.

    Attributes:
        material: The Material to simulate
        pump_wavelength_nm: Pump laser wavelength in nm
        n_levels: Total number of energy levels in the system
    """

    material: Material
    pump_wavelength_nm: float = 1064.0

    def __post_init__(self):
        """Initialize the equation system."""
        self._build_index_map()
        self._precompute_rates()

    def _build_index_map(self):
        """Build mapping from (ion_index, level_index) to global index."""
        self.n_levels = 0
        self.index_map = {}  # (ion_idx, level_idx) -> global_idx
        self.reverse_map = {}  # global_idx -> (ion_idx, level_idx)

        for ion_idx, ion in enumerate(self.material.dopants):
            for level in ion.levels:
                global_idx = self.n_levels
                self.index_map[(ion_idx, level.index)] = global_idx
                self.reverse_map[global_idx] = (ion_idx, level.index)
                self.n_levels += 1

    def _precompute_rates(self):
        """Precompute rate matrices for efficiency."""
        n = self.n_levels

        # Single-ion decay rates (radiative + non-radiative)
        # decay_matrix[i, j] = rate from level i to level j
        self.decay_matrix = np.zeros((n, n))

        # Absorption cross-sections (GSA and ESA)
        # absorption_from[i] = cross-section for absorption from level i
        # absorption_to[i] = level that absorption from level i goes to
        self.gsa_rates = {}  # level_idx -> (to_level, cross_section)
        self.esa_rates = {}  # level_idx -> (to_level, cross_section)

        # Two-ion processes (ETU, CR)
        # Each entry: (ion1_from, ion1_to, ion2_from, ion2_to, rate)
        self.two_ion_processes = []

        for ion_idx, ion in enumerate(self.material.dopants):
            for t in ion.transitions:
                from_global = self.index_map[(ion_idx, t.from_level)]
                to_global = self.index_map[(ion_idx, t.to_level)]

                if t.transition_type == TransitionType.RADIATIVE:
                    self.decay_matrix[from_global, to_global] += t.rate

                elif t.transition_type == TransitionType.NON_RADIATIVE:
                    self.decay_matrix[from_global, to_global] += t.rate

                elif t.transition_type == TransitionType.GSA:
                    self.gsa_rates[from_global] = (to_global, t.rate)

                elif t.transition_type == TransitionType.ESA:
                    self.esa_rates[from_global] = (to_global, t.rate)

                elif t.transition_type in (TransitionType.ETU, TransitionType.CR):
                    if t.partner_from is not None and t.partner_to is not None:
                        partner_from_global = self.index_map[(ion_idx, t.partner_from)]
                        partner_to_global = self.index_map[(ion_idx, t.partner_to)]
                        self.two_ion_processes.append((
                            from_global, to_global,
                            partner_from_global, partner_to_global,
                            t.rate,
                            t.transition_type,
                        ))

    def photon_flux(self, power_density_W_cm2: float) -> float:
        """
        Calculate photon flux from power density.

        Args:
            power_density_W_cm2: Pump power density in W/cm^2

        Returns:
            Photon flux in photons/(cm^2 * s)
        """
        # Convert wavelength to frequency
        wavelength_m = self.pump_wavelength_nm * 1e-9
        photon_energy = H_PLANCK * C_LIGHT / wavelength_m  # Joules

        # Power density W/cm^2 = J/(s*cm^2)
        # Flux = power_density / photon_energy
        return power_density_W_cm2 / photon_energy

    def derivative(
        self,
        t: float,
        N: np.ndarray,
        photon_flux: float,
    ) -> np.ndarray:
        """
        Compute dN/dt for all energy levels.

        This is the core function passed to scipy's ODE solver.

        Args:
            t: Current time (not used explicitly, but required by solver)
            N: Population array, N[i] = population of global level i
            photon_flux: Pump photon flux in photons/(cm^2 * s)

        Returns:
            dN/dt array of same shape as N
        """
        dN = np.zeros_like(N)

        # 1. Single-ion decay processes (radiative + non-radiative)
        for i in range(self.n_levels):
            for j in range(self.n_levels):
                if self.decay_matrix[i, j] > 0:
                    rate = self.decay_matrix[i, j] * N[i]
                    dN[i] -= rate  # Depopulates level i
                    dN[j] += rate  # Populates level j

        # 2. Ground State Absorption (GSA)
        for from_level, (to_level, cross_section) in self.gsa_rates.items():
            rate = cross_section * photon_flux * N[from_level]
            dN[from_level] -= rate
            dN[to_level] += rate

        # 3. Excited State Absorption (ESA)
        for from_level, (to_level, cross_section) in self.esa_rates.items():
            rate = cross_section * photon_flux * N[from_level]
            dN[from_level] -= rate
            dN[to_level] += rate

        # 4. Two-ion processes (ETU, CR)
        # For CR (cross-relaxation), the key PA feedback:
        #   Ion 1: from_level -> to_level (typically emitting level -> intermediate)
        #   Ion 2: partner_from (ground) -> partner_to (intermediate)
        #   This creates TWO ions in the intermediate state from ONE excited ion
        for (from1, to1, from2, to2, rate, ttype) in self.two_ion_processes:
            # Rate is proportional to product of populations
            # Units: rate [cm^3/s] * N1 [ions/cm^3] * N2 [ions/cm^3] = [ions/cm^3/s]
            process_rate = rate * N[from1] * N[from2]

            dN[from1] -= process_rate  # Ion 1 leaves from_level
            dN[to1] += process_rate    # Ion 1 goes to to_level
            dN[from2] -= process_rate  # Ion 2 leaves from_level
            dN[to2] += process_rate    # Ion 2 goes to to_level

        return dN

    def get_derivative_func(
        self,
        power_density_W_cm2: float,
    ) -> Callable[[float, np.ndarray], np.ndarray]:
        """
        Return a derivative function bound to a specific power density.

        This is convenient for passing to scipy.integrate.solve_ivp.

        Args:
            power_density_W_cm2: Pump power density in W/cm^2

        Returns:
            Function f(t, N) -> dN/dt
        """
        flux = self.photon_flux(power_density_W_cm2)
        return lambda t, N: self.derivative(t, N, flux)

    def initial_populations(self, total_concentration: Optional[float] = None) -> np.ndarray:
        """
        Create initial population array (all ions in ground state).

        Args:
            total_concentration: Override total ion concentration.
                If None, uses concentrations from material definition.

        Returns:
            Initial population array
        """
        N0 = np.zeros(self.n_levels)

        for ion_idx, ion in enumerate(self.material.dopants):
            # All population starts in ground state (level 0)
            ground_global = self.index_map[(ion_idx, 0)]
            conc = total_concentration if total_concentration else ion.concentration
            N0[ground_global] = conc

        return N0

    def get_level_name(self, global_idx: int) -> str:
        """Get the name of a level from its global index."""
        ion_idx, level_idx = self.reverse_map[global_idx]
        ion = self.material.dopants[ion_idx]
        level = ion.levels[level_idx]
        return f"{ion.symbol}:{level.name}"

    def get_level_names(self) -> list[str]:
        """Get names of all levels in order."""
        return [self.get_level_name(i) for i in range(self.n_levels)]
