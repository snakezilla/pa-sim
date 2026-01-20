"""
Material definition classes for PA-Sim.

This module provides the data structures for defining lanthanide-doped
materials, including energy levels, transitions, and ion configurations.
The design mirrors the physics: a Material contains LanthanideIons,
which contain EnergyLevels connected by Transitions.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import json


class TransitionType(Enum):
    """Types of transitions between energy levels."""

    RADIATIVE = "radiative"           # Spontaneous emission (A coefficient)
    NON_RADIATIVE = "non_radiative"   # Multiphonon relaxation (W_nr)
    GSA = "gsa"                       # Ground state absorption
    ESA = "esa"                       # Excited state absorption
    ETU = "etu"                       # Energy transfer upconversion
    CR = "cr"                         # Cross-relaxation (key PA feedback)
    ENERGY_MIGRATION = "migration"    # Ion-to-ion energy migration


@dataclass
class Transition:
    """
    A transition between energy levels.

    Attributes:
        from_level: Index of the originating energy level
        to_level: Index of the destination energy level
        transition_type: Type of physical process
        rate: Rate constant (units depend on transition type):
            - Radiative/Non-radiative: s^-1
            - GSA/ESA: Cross-section in cm^2 (will be multiplied by photon flux)
            - ETU/CR: cm^3/s (will be multiplied by ion concentrations)
        partner_from: For two-ion processes (ETU, CR), the partner's initial level
        partner_to: For two-ion processes (ETU, CR), the partner's final level
        wavelength_nm: Associated wavelength (for absorption/emission)
        notes: Optional description or literature reference
    """

    from_level: int
    to_level: int
    transition_type: TransitionType
    rate: float
    partner_from: Optional[int] = None
    partner_to: Optional[int] = None
    wavelength_nm: Optional[float] = None
    notes: str = ""

    def is_two_ion_process(self) -> bool:
        """Check if this transition involves two ions."""
        return self.transition_type in (TransitionType.ETU, TransitionType.CR)

    def is_pump_dependent(self) -> bool:
        """Check if this transition depends on pump intensity."""
        return self.transition_type in (TransitionType.GSA, TransitionType.ESA)


@dataclass
class EnergyLevel:
    """
    An energy level of a lanthanide ion.

    Attributes:
        index: Integer index (0 = ground state)
        name: Spectroscopic term symbol (e.g., "3H6", "3F4", "1G4")
        energy_cm_inv: Energy in cm^-1 (wavenumbers) above ground state
        degeneracy: 2J + 1 for the level
    """

    index: int
    name: str
    energy_cm_inv: float
    degeneracy: int = 1

    def energy_eV(self) -> float:
        """Return energy in electron volts."""
        return self.energy_cm_inv * 1.23984e-4

    def energy_J(self) -> float:
        """Return energy in Joules."""
        return self.energy_cm_inv * 1.986e-23


@dataclass
class LanthanideIon:
    """
    A lanthanide ion dopant species.

    Attributes:
        symbol: Chemical symbol with charge (e.g., "Tm3+", "Yb3+", "Nd3+")
        concentration: Doping concentration in ions/cm^3
        levels: List of energy levels for this ion
        transitions: List of all transitions involving this ion
    """

    symbol: str
    concentration: float  # ions/cm^3
    levels: list[EnergyLevel] = field(default_factory=list)
    transitions: list[Transition] = field(default_factory=list)

    def num_levels(self) -> int:
        """Return number of energy levels."""
        return len(self.levels)

    def get_level_by_name(self, name: str) -> Optional[EnergyLevel]:
        """Find an energy level by its spectroscopic name."""
        for level in self.levels:
            if level.name == name:
                return level
        return None

    def get_transitions_from(self, level_index: int) -> list[Transition]:
        """Get all transitions originating from a given level."""
        return [t for t in self.transitions if t.from_level == level_index]

    def get_transitions_to(self, level_index: int) -> list[Transition]:
        """Get all transitions terminating at a given level."""
        return [t for t in self.transitions if t.to_level == level_index]

    def add_level(self, name: str, energy_cm_inv: float, degeneracy: int = 1) -> EnergyLevel:
        """Add an energy level and return it."""
        level = EnergyLevel(
            index=len(self.levels),
            name=name,
            energy_cm_inv=energy_cm_inv,
            degeneracy=degeneracy,
        )
        self.levels.append(level)
        return level

    def add_transition(
        self,
        from_level: int,
        to_level: int,
        transition_type: TransitionType,
        rate: float,
        **kwargs,
    ) -> Transition:
        """Add a transition and return it."""
        transition = Transition(
            from_level=from_level,
            to_level=to_level,
            transition_type=transition_type,
            rate=rate,
            **kwargs,
        )
        self.transitions.append(transition)
        return transition


@dataclass
class Material:
    """
    A complete material definition for PA simulation.

    Attributes:
        name: Descriptive name (e.g., "8% Tm:NaYF4 nanoparticles")
        host_matrix: Chemical formula of host (e.g., "NaYF4", "LiYF4")
        dopants: List of lanthanide ion dopants
        phonon_energy_cm_inv: Maximum phonon energy of the host matrix
        size_nm: Particle size in nm (for nanoparticles)
        temperature_K: Temperature in Kelvin
        notes: Additional information or literature references
    """

    name: str
    host_matrix: str
    dopants: list[LanthanideIon] = field(default_factory=list)
    phonon_energy_cm_inv: float = 350.0  # Default for fluorides
    size_nm: Optional[float] = None
    temperature_K: float = 300.0
    notes: str = ""

    def get_ion(self, symbol: str) -> Optional[LanthanideIon]:
        """Get a dopant ion by its symbol."""
        for ion in self.dopants:
            if ion.symbol == symbol:
                return ion
        return None

    def total_levels(self) -> int:
        """Return total number of energy levels across all dopants."""
        return sum(ion.num_levels() for ion in self.dopants)

    def to_dict(self) -> dict:
        """Serialize to a dictionary for JSON export."""
        return {
            "name": self.name,
            "host_matrix": self.host_matrix,
            "phonon_energy_cm_inv": self.phonon_energy_cm_inv,
            "size_nm": self.size_nm,
            "temperature_K": self.temperature_K,
            "notes": self.notes,
            "dopants": [
                {
                    "symbol": ion.symbol,
                    "concentration": ion.concentration,
                    "levels": [
                        {
                            "index": lvl.index,
                            "name": lvl.name,
                            "energy_cm_inv": lvl.energy_cm_inv,
                            "degeneracy": lvl.degeneracy,
                        }
                        for lvl in ion.levels
                    ],
                    "transitions": [
                        {
                            "from_level": t.from_level,
                            "to_level": t.to_level,
                            "type": t.transition_type.value,
                            "rate": t.rate,
                            "partner_from": t.partner_from,
                            "partner_to": t.partner_to,
                            "wavelength_nm": t.wavelength_nm,
                            "notes": t.notes,
                        }
                        for t in ion.transitions
                    ],
                }
                for ion in self.dopants
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Material":
        """Create a Material from a dictionary (e.g., loaded from JSON)."""
        dopants = []
        for ion_data in data.get("dopants", []):
            ion = LanthanideIon(
                symbol=ion_data["symbol"],
                concentration=ion_data["concentration"],
            )
            for lvl_data in ion_data.get("levels", []):
                ion.levels.append(EnergyLevel(
                    index=lvl_data["index"],
                    name=lvl_data["name"],
                    energy_cm_inv=lvl_data["energy_cm_inv"],
                    degeneracy=lvl_data.get("degeneracy", 1),
                ))
            for t_data in ion_data.get("transitions", []):
                ion.transitions.append(Transition(
                    from_level=t_data["from_level"],
                    to_level=t_data["to_level"],
                    transition_type=TransitionType(t_data["type"]),
                    rate=t_data["rate"],
                    partner_from=t_data.get("partner_from"),
                    partner_to=t_data.get("partner_to"),
                    wavelength_nm=t_data.get("wavelength_nm"),
                    notes=t_data.get("notes", ""),
                ))
            dopants.append(ion)

        return cls(
            name=data["name"],
            host_matrix=data["host_matrix"],
            dopants=dopants,
            phonon_energy_cm_inv=data.get("phonon_energy_cm_inv", 350.0),
            size_nm=data.get("size_nm"),
            temperature_K=data.get("temperature_K", 300.0),
            notes=data.get("notes", ""),
        )

    def to_json(self, filepath: str) -> None:
        """Save material definition to a JSON file."""
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def from_json(cls, filepath: str) -> "Material":
        """Load material definition from a JSON file."""
        with open(filepath, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)
