"""
PA-Sim: A Generalizable Photon Avalanching Simulation Framework

An open-source Python framework for simulating photon avalanching (PA)
dynamics in lanthanide-doped nanoparticles.

References:
    [1] Lee, C., et al. (2021). Giant nonlinear optical responses from
        photon-avalanching nanoparticles. Nature, 589, 230-235.
    [2] Skripka, A., & Chan, E. M. (2025). Unraveling the myths and mysteries
        of photon avalanching nanoparticles. Materials Horizons, 12, 3575-3597.
"""

__version__ = "0.1.0"
__author__ = "PA-Sim Contributors"

from pa_sim.core.material import Material, LanthanideIon, EnergyLevel, Transition
from pa_sim.core.simulation import Simulation, PumpLaser, SolverConfig
from pa_sim.core.rate_equations import RateEquationSystem

__all__ = [
    "Material",
    "LanthanideIon",
    "EnergyLevel",
    "Transition",
    "Simulation",
    "PumpLaser",
    "SolverConfig",
    "RateEquationSystem",
]
