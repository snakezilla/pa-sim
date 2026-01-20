#!/usr/bin/env python3
"""
PA-Sim Quick Start Example

Demonstrates basic usage of PA-Sim to simulate photon avalanching
in Tm3+-doped NaYF4 nanoparticles.

This example reproduces the key features from:
    Lee, C., et al. (2021). Nature, 589, 230-235.
"""

import numpy as np

from pa_sim import Simulation, PumpLaser, SolverConfig
from pa_sim.materials import load_material
from pa_sim.analysis import analyze_power_sweep

# Try to import matplotlib for visualization
try:
    import matplotlib.pyplot as plt
    from pa_sim.visualization import plot_power_dependence, plot_temporal_dynamics
    HAS_VIZ = True
except ImportError:
    HAS_VIZ = False
    print("Note: Install matplotlib for visualization (pip install matplotlib)")


def main():
    print("=" * 60)
    print("PA-Sim: Photon Avalanching Simulation")
    print("=" * 60)

    # 1. Load a pre-defined material
    print("\n1. Loading 8% Tm:NaYF4 material...")
    material = load_material("Tm_NaYF4_8pct")
    print(f"   Material: {material.name}")
    print(f"   Host: {material.host_matrix}")
    print(f"   Dopant: {material.dopants[0].symbol}")
    print(f"   Concentration: {material.dopants[0].concentration:.2e} ions/cm³")

    # Show energy levels
    tm = material.dopants[0]
    print("\n   Energy levels:")
    for level in tm.levels:
        print(f"     {level.index}: {level.name} at {level.energy_cm_inv:.0f} cm⁻¹")

    # 2. Single simulation at high power
    print("\n2. Running single simulation at 50 kW/cm²...")
    laser = PumpLaser(wavelength_nm=1064.0, power_density_W_cm2=5e4)
    config = SolverConfig(t_end=100e-3, method="Radau")  # 100 ms

    sim = Simulation(material, laser, config)
    result = sim.run()

    print(f"   Solver: {result.solver_info['method']}")
    print(f"   Time points: {result.solver_info['n_timepoints']}")
    print(f"   Elapsed: {result.solver_info['elapsed_seconds']:.3f} s")

    # Check steady state
    ss = result.steady_state_populations()
    print("\n   Steady-state populations:")
    for name, pop in ss.items():
        print(f"     {name}: {pop:.2e} ions/cm³")

    # 3. Power sweep to characterize PA
    print("\n3. Running power sweep (20 points from 1 kW/cm² to 1 MW/cm²)...")
    powers = np.logspace(3, 6, 20)

    def progress(i, n, power):
        if i % 5 == 0:
            print(f"   Progress: {i+1}/{n} ({power:.1e} W/cm²)")

    results = sim.run_power_sweep(powers, t_end=100e-3, progress_callback=progress)

    # 4. Extract PA parameters
    print("\n4. Extracting PA parameters...")
    emitting_level = "Tm3+:3H4"
    pa_params = analyze_power_sweep(results, emitting_level)

    print(f"\n{pa_params}")

    # 5. Visualization (if matplotlib available)
    if HAS_VIZ:
        print("\n5. Generating plots...")

        # Figure 1: Power dependence
        fig1, ax1 = plt.subplots(figsize=(8, 6))
        emissions = np.array([
            r.total_emission(emitting_level, 500.0)[-1]  # A = 500 s^-1
            for r in results
        ])
        plot_power_dependence(powers, emissions, pa_params, ax=ax1)
        ax1.set_title("Photon Avalanche Power Dependence")
        fig1.savefig("power_dependence.png", dpi=150, bbox_inches='tight')
        print("   Saved: power_dependence.png")

        # Figure 2: Temporal dynamics at different powers
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        for idx in [0, len(results)//2, -1]:
            r = results[idx]
            pop = r.get_population(emitting_level)
            t_ms = r.t * 1e3
            label = f"{r.power_density:.0e} W/cm²"
            ax2.plot(t_ms, pop / pop.max(), label=label)
        ax2.set_xlabel("Time (ms)")
        ax2.set_ylabel("Normalized Emission")
        ax2.set_title("PA Rise Dynamics at Different Powers")
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        fig2.savefig("temporal_dynamics.png", dpi=150, bbox_inches='tight')
        print("   Saved: temporal_dynamics.png")

        plt.show()

    print("\n" + "=" * 60)
    print("Simulation complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
