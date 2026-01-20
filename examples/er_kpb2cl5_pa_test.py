"""
Test Er3+:KPb2Cl5 photon avalanche at 690nm excitation.

This script explores whether PA behavior emerges in Er3+-doped KPb2Cl5
low-phonon chloride host using 690nm pumping.

Key questions:
1. Does the system show threshold behavior?
2. What is the nonlinearity order (S)?
3. How does it compare to known PA systems?
"""

import numpy as np
from pa_sim import Simulation, PumpLaser, SolverConfig
from pa_sim.materials import load_material
from pa_sim.analysis import analyze_power_sweep, extract_nonlinearity

# Load the experimental Er:KPb2Cl5 material
material = load_material("Er_KPb2Cl5_8pct")
print(f"Material: {material.name}")
print(f"Host phonon energy: {material.phonon_energy_cm_inv} cm^-1")
print(f"Dopant concentration: {material.dopants[0].concentration:.2e} ions/cm³")
print()

# Configure pump laser at 690nm
pump = PumpLaser(
    power_density_W_cm2=1e5,  # Start with 100 kW/cm²
    wavelength_nm=690.0
)

# Solver config - need long time for steady state in low-phonon host
config = SolverConfig(
    t_end=500e-3,  # 500 ms - Er3+ in KPb2Cl5 has ms lifetimes
    method="Radau",  # Stiff solver
    rtol=1e-8,
    atol=1e-12,
)

# Create simulation
sim = Simulation(material, pump, config)

print("Running power sweep...")
print("=" * 60)

# Power sweep from 1 kW/cm² to 1 MW/cm²
powers = np.logspace(3, 6, 30)  # 30 power points

results = sim.run_power_sweep(powers, t_end=500e-3)

# Extract steady-state populations
ss_pops = []
for r in results:
    pops = r.steady_state_populations()
    ss_pops.append(pops)

# Get the emitting level (4S3/2) population
emitting_level = "Er3+:4S3/2"
if emitting_level in ss_pops[0]:
    emissions = np.array([p[emitting_level] for p in ss_pops])
else:
    # Fallback - sum all excited state populations
    print(f"Available levels: {list(ss_pops[0].keys())}")
    emissions = np.array([sum(p.values()) - p.get("Er3+:4I15/2", 0) for p in ss_pops])

print()
print("=" * 60)
print("RESULTS")
print("=" * 60)

# Analyze for PA parameters
try:
    params = analyze_power_sweep(results, emitting_level)
    print(f"\nPA Parameters for {emitting_level}:")
    print(f"  Threshold: {params.threshold:.2e} W/cm²")
    print(f"  Nonlinearity order (S): {params.nonlinearity_order:.1f}")
    print(f"  S uncertainty: ±{params.nonlinearity_uncertainty:.1f}")
    print(f"  Rise time: {params.rise_time_s*1000:.1f} ms")

    # Interpret results
    print()
    print("INTERPRETATION:")
    if params.nonlinearity_order > 10:
        print(f"  ✓ Strong PA behavior detected (S = {params.nonlinearity_order:.0f})")
        print(f"  ✓ Threshold at {params.threshold/1000:.1f} kW/cm²")
        print("  → Er3+:KPb2Cl5 shows promise for photon avalanche!")
    elif params.nonlinearity_order > 3:
        print(f"  ~ Moderate nonlinearity (S = {params.nonlinearity_order:.1f})")
        print("  → Some avalanche-like behavior, but not classic PA")
    else:
        print(f"  ✗ Low nonlinearity (S = {params.nonlinearity_order:.1f})")
        print("  → Linear or low-order multiphoton process")

except Exception as e:
    print(f"Analysis error: {e}")

    # Manual slope analysis
    print("\nManual log-log slope analysis:")
    log_p = np.log10(powers)
    log_e = np.log10(emissions + 1e-20)  # Avoid log(0)

    # Low power region (first third)
    n_low = len(powers) // 3
    slope_low, _ = np.polyfit(log_p[:n_low], log_e[:n_low], 1)
    print(f"  Low power slope: {slope_low:.1f}")

    # High power region (last third)
    slope_high, _ = np.polyfit(log_p[-n_low:], log_e[-n_low:], 1)
    print(f"  High power slope: {slope_high:.1f}")

    if slope_high > slope_low * 2:
        print("  → Suggests threshold behavior")

# Print power vs emission table
print()
print("Power (W/cm²)    Emission (arb)")
print("-" * 35)
for p, e in zip(powers[::5], emissions[::5]):  # Every 5th point
    print(f"{p:12.2e}    {e:.4e}")

# Compare to ground state population
ground_pops = np.array([p.get("Er3+:4I15/2", 0) for p in ss_pops])
print()
print(f"Ground state depletion at max power: {100*(1 - ground_pops[-1]/ground_pops[0]):.1f}%")
