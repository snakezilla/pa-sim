"""
Materials database for PA-Sim.

This module provides pre-defined material configurations and utilities for
loading/saving material definitions. The database is intentionally kept
minimal - users are encouraged to contribute validated parameter sets.

The Tm3+:NaYF4 example is based on the 2021 Nature paper:
    Lee, C., et al. (2021). Nature, 589, 230-235.
"""

import json
from pathlib import Path
from typing import Optional

from pa_sim.core.material import (
    Material,
    LanthanideIon,
    EnergyLevel,
    Transition,
    TransitionType,
)


# Path to built-in materials database
_DATABASE_PATH = Path(__file__).parent / "materials.json"


class MaterialDatabase:
    """
    Database of pre-defined materials.

    Provides access to validated material configurations from the literature.
    Users can also add their own materials.
    """

    def __init__(self, database_path: Optional[Path] = None):
        """
        Initialize the database.

        Args:
            database_path: Path to JSON database file. If None, uses built-in.
        """
        self.database_path = database_path or _DATABASE_PATH
        self._materials: dict[str, dict] = {}
        self._load_database()

    def _load_database(self):
        """Load materials from JSON file."""
        if self.database_path.exists():
            with open(self.database_path, "r") as f:
                data = json.load(f)
                self._materials = data.get("materials", {})

    def save_database(self):
        """Save current materials to JSON file."""
        with open(self.database_path, "w") as f:
            json.dump({"materials": self._materials}, f, indent=2)

    def list_materials(self) -> list[str]:
        """Return list of available material names."""
        return list(self._materials.keys())

    def get(self, name: str) -> Material:
        """
        Load a material by name.

        Args:
            name: Material identifier (e.g., "Tm_NaYF4_8pct")

        Returns:
            Material instance
        """
        if name not in self._materials:
            raise KeyError(f"Material '{name}' not found. Available: {self.list_materials()}")
        return Material.from_dict(self._materials[name])

    def add(self, name: str, material: Material):
        """
        Add a material to the database.

        Args:
            name: Identifier for the material
            material: Material instance to add
        """
        self._materials[name] = material.to_dict()


def load_material(name: str) -> Material:
    """
    Convenience function to load a material by name.

    Args:
        name: Material identifier or "list" to show available materials

    Returns:
        Material instance
    """
    db = MaterialDatabase()

    if name.lower() == "list":
        available = db.list_materials()
        if not available:
            available = list(get_builtin_materials().keys())
        raise ValueError(f"Available materials: {available}")

    # Try database first
    try:
        return db.get(name)
    except KeyError:
        pass

    # Try built-in materials
    builtins = get_builtin_materials()
    if name in builtins:
        return builtins[name]

    raise KeyError(f"Material '{name}' not found. Available: {list(builtins.keys())}")


def get_builtin_materials() -> dict[str, Material]:
    """
    Return dictionary of built-in material definitions.

    These are hard-coded examples based on published literature.
    """
    return {
        "Tm_NaYF4_8pct": create_tm_nayf4_material(concentration_pct=8.0),
        "Tm_NaYF4_0.5pct": create_tm_nayf4_material(concentration_pct=0.5),
        "Tm_LiYF4_3pct": create_tm_liyf4_material(concentration_pct=3.0),
    }


def create_tm_nayf4_material(concentration_pct: float = 8.0) -> Material:
    """
    Create Tm3+:NaYF4 material based on Lee et al. (2021) Nature.

    This is the canonical PA system demonstrating giant nonlinearities.
    The simplified 4-level model captures the essential PA physics.

    Energy level scheme for Tm3+ (simplified):
        Level 0: 3H6 (ground state)
        Level 1: 3F4 (intermediate, ~5600 cm^-1)
        Level 2: 3H5 (~8300 cm^-1)
        Level 3: 3H4 (emitting, ~12600 cm^-1)

    Key PA mechanism:
        - GSA: 3H6 -> 3H4 (weak, at 1064 nm off-resonance)
        - ESA: 3F4 -> 3H4 (strong, resonant at 1064 nm)
        - CR: 3H4 + 3H6 -> 3F4 + 3F4 (avalanche feedback)

    Args:
        concentration_pct: Tm3+ doping concentration in mol%

    Returns:
        Material instance
    """
    # Convert mol% to ions/cm^3
    # NaYF4 density ~4.2 g/cm^3, MW ~166 g/mol
    # Site density ~1.5e22 ions/cm^3 for Y sites
    site_density = 1.5e22  # Y sites per cm^3
    concentration = concentration_pct / 100 * site_density

    # Create the Tm3+ ion
    tm = LanthanideIon(symbol="Tm3+", concentration=concentration)

    # Add energy levels
    tm.add_level("3H6", 0.0, degeneracy=13)           # Ground state
    tm.add_level("3F4", 5600.0, degeneracy=9)         # Intermediate (looping level)
    tm.add_level("3H5", 8300.0, degeneracy=11)        # Intermediate
    tm.add_level("3H4", 12600.0, degeneracy=9)        # Emitting level

    # Add transitions
    # Note: Rate values are approximate - users should validate against their systems

    # Radiative decays
    tm.add_transition(3, 0, TransitionType.RADIATIVE, rate=500.0,
                      wavelength_nm=800, notes="3H4 -> 3H6 emission")
    tm.add_transition(3, 1, TransitionType.RADIATIVE, rate=50.0,
                      notes="3H4 -> 3F4")
    tm.add_transition(2, 1, TransitionType.RADIATIVE, rate=200.0,
                      notes="3H5 -> 3F4")
    tm.add_transition(1, 0, TransitionType.RADIATIVE, rate=100.0,
                      wavelength_nm=1800, notes="3F4 -> 3H6")

    # Non-radiative relaxation (multiphonon)
    tm.add_transition(2, 1, TransitionType.NON_RADIATIVE, rate=1e4,
                      notes="3H5 -> 3F4 multiphonon")
    tm.add_transition(3, 2, TransitionType.NON_RADIATIVE, rate=1e3,
                      notes="3H4 -> 3H5 multiphonon (relatively slow in fluorides)")

    # Ground State Absorption at 1064 nm (weak, off-resonance)
    # Cross-section in cm^2
    tm.add_transition(0, 3, TransitionType.GSA, rate=1e-22,
                      wavelength_nm=1064, notes="Weak GSA at 1064 nm")

    # Excited State Absorption at 1064 nm (strong, resonant)
    # This is the key pump step in PA
    tm.add_transition(1, 3, TransitionType.ESA, rate=5e-21,
                      wavelength_nm=1064, notes="Strong ESA 3F4 -> 3H4")

    # Cross-Relaxation: THE KEY PA FEEDBACK LOOP
    # 3H4 + 3H6 -> 3F4 + 3F4
    # One excited ion creates TWO intermediate ions
    # Rate in cm^3/s
    tm.add_transition(
        from_level=3, to_level=1,  # Ion 1: 3H4 -> 3F4
        transition_type=TransitionType.CR,
        rate=5e-16,
        partner_from=0, partner_to=1,  # Ion 2: 3H6 -> 3F4
        notes="CR: 3H4 + 3H6 -> 2(3F4) - avalanche feedback"
    )

    # Create the material
    material = Material(
        name=f"{concentration_pct}% Tm:NaYF4 nanoparticles",
        host_matrix="β-NaYF4",
        dopants=[tm],
        phonon_energy_cm_inv=350,  # Low phonon energy fluoride
        size_nm=20.0,
        temperature_K=300.0,
        notes="Based on Lee et al. (2021) Nature 589, 230-235. "
              "Parameters are approximate - validate against experiments.",
    )

    return material


def create_tm_liyf4_material(concentration_pct: float = 3.0) -> Material:
    """
    Create Tm3+:LiYF4 material for PASSI imaging.

    LiYF4 has slightly different crystal field than NaYF4.

    Args:
        concentration_pct: Tm3+ doping concentration in mol%

    Returns:
        Material instance
    """
    # LiYF4 density ~4.0 g/cm^3
    site_density = 1.4e22
    concentration = concentration_pct / 100 * site_density

    tm = LanthanideIon(symbol="Tm3+", concentration=concentration)

    # Similar level structure to NaYF4 Tm3+
    tm.add_level("3H6", 0.0, degeneracy=13)
    tm.add_level("3F4", 5700.0, degeneracy=9)
    tm.add_level("3H5", 8400.0, degeneracy=11)
    tm.add_level("3H4", 12700.0, degeneracy=9)

    # Radiative
    tm.add_transition(3, 0, TransitionType.RADIATIVE, rate=450.0, wavelength_nm=790)
    tm.add_transition(3, 1, TransitionType.RADIATIVE, rate=40.0)
    tm.add_transition(2, 1, TransitionType.RADIATIVE, rate=180.0)
    tm.add_transition(1, 0, TransitionType.RADIATIVE, rate=90.0, wavelength_nm=1850)

    # Non-radiative
    tm.add_transition(2, 1, TransitionType.NON_RADIATIVE, rate=8e3)
    tm.add_transition(3, 2, TransitionType.NON_RADIATIVE, rate=8e2)

    # GSA (weak)
    tm.add_transition(0, 3, TransitionType.GSA, rate=8e-23, wavelength_nm=1064)

    # ESA (strong)
    tm.add_transition(1, 3, TransitionType.ESA, rate=4e-21, wavelength_nm=1064)

    # Cross-relaxation
    tm.add_transition(
        from_level=3, to_level=1,
        transition_type=TransitionType.CR,
        rate=4e-16,
        partner_from=0, partner_to=1,
        notes="CR avalanche feedback"
    )

    return Material(
        name=f"{concentration_pct}% Tm:LiYF4",
        host_matrix="LiYF4",
        dopants=[tm],
        phonon_energy_cm_inv=400,
        temperature_K=300.0,
        notes="LiYF4 host for PASSI imaging applications.",
    )
