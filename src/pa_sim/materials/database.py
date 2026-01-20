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
        "Er_KPb2Cl5_5pct": create_er_kpb2cl5_material(concentration_pct=5.0),
        "Er_KPb2Cl5_8pct": create_er_kpb2cl5_material(concentration_pct=8.0),
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


def create_er_kpb2cl5_material(concentration_pct: float = 5.0) -> Material:
    """
    Create Er3+:KPb2Cl5 material for testing PA at 690nm.

    EXPERIMENTAL: This is an untested configuration exploring PA in a
    low-phonon chloride host. KPb2Cl5 has demonstrated PA with Nd3+ at
    >200th order nonlinearity. Er3+ PA potential is being investigated.

    Energy level scheme for Er3+ (simplified 7-level model):
        Level 0: 4I15/2 (ground state, 0 cm^-1)
        Level 1: 4I13/2 (~6500 cm^-1, metastable ~ms lifetime)
        Level 2: 4I11/2 (~10200 cm^-1, metastable in low-phonon hosts)
        Level 3: 4I9/2 (~12400 cm^-1)
        Level 4: 4F9/2 (~15300 cm^-1)
        Level 5: 4S3/2 (~18400 cm^-1, green emitting)
        Level 6: 2H11/2 (~19200 cm^-1)

    Proposed PA mechanism at 690nm (14493 cm^-1):
        - GSA: 4I15/2 -> 4F9/2 (weak, ~800 cm^-1 off-resonance)
        - MPR: 4F9/2 -> 4S3/2 -> 4I11/2 (slow in low-phonon host)
        - ESA: 4I11/2 + 690nm -> ~24700 cm^-1 (4G levels)
        - CR: High level + 4I15/2 -> 2x 4I11/2 (avalanche feedback)
        - Emission: 4S3/2 -> 4I15/2 at 550nm (green)

    References:
        - Gruber et al., J. Cryst. Growth (2006) - Er3+ spectroscopy in KPb2Cl5
        - Balda et al., Opt. Mater. (1994) - Er3+ PA in LiYF4 at 690nm

    Args:
        concentration_pct: Er3+ doping concentration in mol%

    Returns:
        Material instance
    """
    # KPb2Cl5 density ~4.78 g/cm^3
    # Pb2+ site density for rare-earth substitution ~1.2e22 /cm^3
    site_density = 1.2e22
    concentration = concentration_pct / 100 * site_density

    er = LanthanideIon(symbol="Er3+", concentration=concentration)

    # Add energy levels (values from spectroscopic studies)
    er.add_level("4I15/2", 0.0, degeneracy=16)          # Ground state
    er.add_level("4I13/2", 6500.0, degeneracy=14)       # Metastable (~3-11 ms in KPb2Cl5)
    er.add_level("4I11/2", 10200.0, degeneracy=12)      # Intermediate metastable
    er.add_level("4I9/2", 12400.0, degeneracy=10)
    er.add_level("4F9/2", 15300.0, degeneracy=10)
    er.add_level("4S3/2", 18400.0, degeneracy=4)        # Green emitting level
    er.add_level("2H11/2", 19200.0, degeneracy=12)
    er.add_level("4G11/2", 24700.0, degeneracy=12)      # Upper level for ESA

    # Radiative decay rates (s^-1) - estimated from literature
    # Low phonon energy significantly extends radiative lifetimes
    er.add_transition(5, 0, TransitionType.RADIATIVE, rate=500.0,
                      wavelength_nm=544, notes="4S3/2 -> 4I15/2 green emission")
    er.add_transition(6, 0, TransitionType.RADIATIVE, rate=800.0,
                      wavelength_nm=520, notes="2H11/2 -> 4I15/2")
    er.add_transition(4, 0, TransitionType.RADIATIVE, rate=300.0,
                      wavelength_nm=654, notes="4F9/2 -> 4I15/2 red emission")
    er.add_transition(3, 0, TransitionType.RADIATIVE, rate=100.0,
                      wavelength_nm=806, notes="4I9/2 -> 4I15/2")
    er.add_transition(2, 0, TransitionType.RADIATIVE, rate=50.0,
                      wavelength_nm=980, notes="4I11/2 -> 4I15/2")
    er.add_transition(1, 0, TransitionType.RADIATIVE, rate=90.0,
                      wavelength_nm=1540, notes="4I13/2 -> 4I15/2 telecom")
    er.add_transition(7, 5, TransitionType.RADIATIVE, rate=1000.0,
                      notes="4G11/2 -> 4S3/2")

    # Non-radiative relaxation (multiphonon)
    # KPb2Cl5 phonon cutoff: 203 cm^-1 (bulk), ~128 cm^-1 (nanoparticles)
    # Gap law: W_NR ~ W0 * exp(-alpha * deltaE / hω_max)
    # Large gaps (>1000 cm^-1) have very slow MPR in this host

    # 2H11/2 -> 4S3/2: ~800 cm^-1 gap, requires ~4 phonons
    er.add_transition(6, 5, TransitionType.NON_RADIATIVE, rate=1e3,
                      notes="2H11/2 -> 4S3/2 MPR, ~4 phonons")

    # 4S3/2 -> 4F9/2: ~3100 cm^-1 gap, requires ~15 phonons - VERY SLOW
    er.add_transition(5, 4, TransitionType.NON_RADIATIVE, rate=10.0,
                      notes="4S3/2 -> 4F9/2 MPR, ~15 phonons, very slow")

    # 4F9/2 -> 4I9/2: ~2900 cm^-1 gap, ~14 phonons - VERY SLOW
    er.add_transition(4, 3, TransitionType.NON_RADIATIVE, rate=10.0,
                      notes="4F9/2 -> 4I9/2 MPR")

    # 4I9/2 -> 4I11/2: ~2200 cm^-1 gap, ~11 phonons - SLOW
    er.add_transition(3, 2, TransitionType.NON_RADIATIVE, rate=50.0,
                      notes="4I9/2 -> 4I11/2 MPR")

    # 4I11/2 -> 4I13/2: ~3700 cm^-1 gap, ~18 phonons - EXTREMELY SLOW
    er.add_transition(2, 1, TransitionType.NON_RADIATIVE, rate=5.0,
                      notes="4I11/2 -> 4I13/2 MPR, extremely slow in chlorides")

    # 4I13/2 -> 4I15/2: ~6500 cm^-1 gap, ~32 phonons - NEGLIGIBLE
    er.add_transition(1, 0, TransitionType.NON_RADIATIVE, rate=0.1,
                      notes="4I13/2 -> 4I15/2 MPR, negligible")

    # 4G11/2 fast relaxation cascade
    er.add_transition(7, 6, TransitionType.NON_RADIATIVE, rate=1e4,
                      notes="4G11/2 -> 2H11/2 fast relaxation")

    # Ground State Absorption at 690 nm (WEAK - key for PA)
    # 690nm = 14493 cm^-1, target is 4F9/2 at 15300 cm^-1
    # Detuning: ~800 cm^-1 off-resonance -> weak absorption
    # Cross-section estimated ~1e-22 cm^2 (weak, off-resonant)
    er.add_transition(0, 4, TransitionType.GSA, rate=1e-22,
                      wavelength_nm=690, notes="Weak GSA at 690nm, off-resonant to 4F9/2")

    # Excited State Absorption at 690 nm (STRONG - pump step)
    # From 4I11/2 (10200) + 14493 = 24693 cm^-1 -> 4G11/2 level
    # Cross-section estimated ~5e-21 cm^2 (resonant)
    er.add_transition(2, 7, TransitionType.ESA, rate=5e-21,
                      wavelength_nm=690, notes="Strong ESA 4I11/2 -> 4G11/2")

    # Cross-Relaxation: THE AVALANCHE FEEDBACK LOOP
    # 4S3/2 + 4I15/2 -> 4I11/2 + 4I11/2
    # Energy balance: 18400 + 0 = 10200 + 10200 - 2000 (phonon release)
    # Requires ~10 phonons - slower than ideal but may still work
    # W_CR estimated from Er3+ literature: ~5e-17 cm^3/s
    er.add_transition(
        from_level=5, to_level=2,  # Ion 1: 4S3/2 -> 4I11/2
        transition_type=TransitionType.CR,
        rate=5e-17,
        partner_from=0, partner_to=2,  # Ion 2: 4I15/2 -> 4I11/2
        notes="CR: 4S3/2 + 4I15/2 -> 2(4I11/2) - avalanche feedback, ~10 phonons"
    )

    # Alternative CR pathway (faster, lower phonon involvement)
    # 2H11/2 + 4I15/2 -> 4I9/2 + 4I9/2
    # Energy: 19200 + 0 = 12400 + 12400 + 5600 (needs 5600 cm^-1 phonons - too many)
    # This pathway is unfavorable

    return Material(
        name=f"{concentration_pct}% Er:KPb2Cl5 (EXPERIMENTAL)",
        host_matrix="KPb2Cl5",
        dopants=[er],
        phonon_energy_cm_inv=203,  # Ultra-low phonon energy chloride
        size_nm=50.0,  # Bulk crystal
        temperature_K=300.0,
        notes="EXPERIMENTAL: Er3+ in KPb2Cl5 low-phonon host for 690nm PA. "
              "Based on spectroscopic data from Gruber et al. and PA mechanism "
              "analogous to Er3+:LiYF4 at 690nm (Balda et al. 1994). "
              "Parameters are estimates - requires experimental validation.",
    )
