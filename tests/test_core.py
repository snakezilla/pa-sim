"""
Tests for PA-Sim core functionality.
"""

import numpy as np
import pytest

from pa_sim.core.material import (
    Material,
    LanthanideIon,
    EnergyLevel,
    Transition,
    TransitionType,
)
from pa_sim.core.rate_equations import RateEquationSystem
from pa_sim.core.simulation import Simulation, PumpLaser, SolverConfig
from pa_sim.materials import load_material


class TestMaterial:
    """Tests for Material class."""

    def test_create_simple_material(self):
        """Test creating a simple material."""
        ion = LanthanideIon(symbol="Tm3+", concentration=1e21)
        ion.add_level("3H6", 0.0)
        ion.add_level("3F4", 5600.0)

        material = Material(
            name="Test Tm material",
            host_matrix="NaYF4",
            dopants=[ion],
        )

        assert material.name == "Test Tm material"
        assert len(material.dopants) == 1
        assert material.dopants[0].num_levels() == 2

    def test_add_transitions(self):
        """Test adding transitions to an ion."""
        ion = LanthanideIon(symbol="Tm3+", concentration=1e21)
        ion.add_level("3H6", 0.0)
        ion.add_level("3F4", 5600.0)
        ion.add_level("3H4", 12600.0)

        # Add radiative decay
        t = ion.add_transition(2, 0, TransitionType.RADIATIVE, rate=500.0)
        assert t.transition_type == TransitionType.RADIATIVE
        assert t.rate == 500.0

        # Add CR
        cr = ion.add_transition(
            2, 1, TransitionType.CR, rate=5e-16,
            partner_from=0, partner_to=1
        )
        assert cr.is_two_ion_process()

    def test_material_serialization(self):
        """Test JSON serialization round-trip."""
        ion = LanthanideIon(symbol="Er3+", concentration=5e20)
        ion.add_level("4I15/2", 0.0)
        ion.add_level("4I13/2", 6500.0)
        ion.add_transition(1, 0, TransitionType.RADIATIVE, rate=100.0)

        material = Material(
            name="Test material",
            host_matrix="YAG",
            dopants=[ion],
            temperature_K=300.0,
        )

        # Round-trip through dict
        data = material.to_dict()
        restored = Material.from_dict(data)

        assert restored.name == material.name
        assert restored.host_matrix == material.host_matrix
        assert len(restored.dopants) == 1
        assert restored.dopants[0].symbol == "Er3+"


class TestRateEquations:
    """Tests for RateEquationSystem."""

    def test_photon_flux_calculation(self):
        """Test photon flux calculation."""
        material = load_material("Tm_NaYF4_8pct")
        system = RateEquationSystem(material, pump_wavelength_nm=1064.0)

        # 1 W/cm² at 1064 nm
        flux = system.photon_flux(1.0)

        # Photon energy at 1064 nm ≈ 1.87e-19 J
        # Flux should be ≈ 1 / 1.87e-19 ≈ 5.3e18 photons/cm²/s
        assert 5e18 < flux < 6e18

    def test_initial_populations(self):
        """Test initial population setup."""
        material = load_material("Tm_NaYF4_8pct")
        system = RateEquationSystem(material)

        N0 = system.initial_populations()

        # All population should be in ground states
        assert N0.sum() > 0
        # Ground state (index 0) should have all population
        assert N0[0] == material.dopants[0].concentration

    def test_derivative_shape(self):
        """Test that derivative returns correct shape."""
        material = load_material("Tm_NaYF4_8pct")
        system = RateEquationSystem(material)

        N0 = system.initial_populations()
        flux = system.photon_flux(1e4)

        dN = system.derivative(0, N0, flux)

        assert dN.shape == N0.shape


class TestSimulation:
    """Tests for Simulation class."""

    def test_basic_simulation(self):
        """Test running a basic simulation."""
        material = load_material("Tm_NaYF4_8pct")
        laser = PumpLaser(power_density_W_cm2=1e4)
        config = SolverConfig(t_end=1e-3)  # 1 ms, short for test

        sim = Simulation(material, laser, config)
        result = sim.run()

        assert len(result.t) > 0
        assert result.populations.shape[0] == 4  # 4 levels
        assert result.populations.shape[1] == len(result.t)

    def test_population_conservation(self):
        """Test that total population is conserved."""
        material = load_material("Tm_NaYF4_8pct")
        laser = PumpLaser(power_density_W_cm2=1e4)
        config = SolverConfig(t_end=1e-3)

        sim = Simulation(material, laser, config)
        result = sim.run()

        # Sum populations at each time point
        total_pop = result.populations.sum(axis=0)

        # Should be constant (within numerical tolerance)
        assert np.allclose(total_pop, total_pop[0], rtol=1e-6)

    def test_steady_state_reached(self):
        """Test that simulation reaches steady state."""
        material = load_material("Tm_NaYF4_8pct")
        laser = PumpLaser(power_density_W_cm2=5e4)
        config = SolverConfig(t_end=100e-3)  # 100 ms

        sim = Simulation(material, laser, config)
        result = sim.run()

        # Last 10% should be approximately constant
        n_tail = len(result.t) // 10
        for i in range(result.populations.shape[0]):
            pop = result.populations[i, :]
            tail = pop[-n_tail:]
            # Standard deviation should be small compared to mean
            if tail.mean() > 0:
                assert tail.std() / tail.mean() < 0.01

    def test_power_sweep(self):
        """Test power sweep functionality."""
        material = load_material("Tm_NaYF4_8pct")
        sim = Simulation(material)

        powers = np.logspace(3, 5, 5)  # 5 powers for quick test
        results = sim.run_power_sweep(powers, t_end=10e-3)

        assert len(results) == 5
        # Higher power should give higher excited state population
        ss_pops = [r.steady_state_populations()["Tm3+:3H4"] for r in results]
        # Should generally increase (though not strictly monotonic near saturation)
        assert ss_pops[-1] > ss_pops[0]


class TestPAParameters:
    """Tests for PA parameter extraction."""

    def test_threshold_extraction(self):
        """Test threshold extraction from synthetic data."""
        from pa_sim.analysis.pa_parameters import extract_threshold

        # Create synthetic PA-like data
        powers = np.logspace(3, 6, 50)
        threshold = 1e4

        # Below threshold: slope ~2, above threshold: slope ~20
        emissions = np.where(
            powers < threshold,
            powers ** 2,
            (threshold ** 2) * (powers / threshold) ** 20
        )

        thresh_est, _ = extract_threshold(powers, emissions)

        # Should be within factor of 2 of true threshold
        assert 0.5 * threshold < thresh_est < 2 * threshold

    def test_nonlinearity_extraction(self):
        """Test nonlinearity order extraction."""
        from pa_sim.analysis.pa_parameters import extract_nonlinearity

        # Create data with known slope
        powers = np.logspace(4, 6, 20)
        slope = 15.0
        emissions = powers ** slope

        S, unc = extract_nonlinearity(powers, emissions, threshold=1e4, region="above")

        # Should recover the slope accurately
        assert abs(S - slope) < 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
