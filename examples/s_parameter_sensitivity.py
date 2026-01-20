"""
Systematic study: How does nonlinearity order S depend on material parameters?

Goal: Derive S = f(ESA/GSA, W_CR, N_ion, phonon_energy)

This is the key missing piece - a predictive model for PA nonlinearity
that would enable rational material design.
"""

import numpy as np
from pa_sim import Simulation, PumpLaser, SolverConfig
from pa_sim.core.material import Material, LanthanideIon, TransitionType
from pa_sim.analysis import extract_nonlinearity


def create_test_material(
    esa_gsa_ratio: float = 50.0,
    w_cr: float = 5e-16,
    concentration: float = 1.2e21,
    sigma_gsa: float = 1e-22,
) -> Material:
    """Create a simplified 4-level PA material with tunable parameters."""

    ion = LanthanideIon(symbol="Test", concentration=concentration)

    # 4-level system: Ground, Intermediate, Pump target, Emitting
    ion.add_level("G", 0.0)          # Ground
    ion.add_level("I", 5600.0)       # Intermediate (looping level)
    ion.add_level("P", 8300.0)       # Pump intermediate
    ion.add_level("E", 12600.0)      # Emitting level

    # Radiative decays
    ion.add_transition(3, 0, TransitionType.RADIATIVE, rate=500.0)
    ion.add_transition(3, 1, TransitionType.RADIATIVE, rate=50.0)
    ion.add_transition(2, 1, TransitionType.RADIATIVE, rate=200.0)
    ion.add_transition(1, 0, TransitionType.RADIATIVE, rate=100.0)

    # Non-radiative relaxation
    ion.add_transition(2, 1, TransitionType.NON_RADIATIVE, rate=1e4)
    ion.add_transition(3, 2, TransitionType.NON_RADIATIVE, rate=1e3)

    # GSA (weak) - parameterized
    ion.add_transition(0, 3, TransitionType.GSA, rate=sigma_gsa, wavelength_nm=1064)

    # ESA (strong) - derived from ratio
    sigma_esa = sigma_gsa * esa_gsa_ratio
    ion.add_transition(1, 3, TransitionType.ESA, rate=sigma_esa, wavelength_nm=1064)

    # Cross-relaxation - parameterized
    ion.add_transition(
        from_level=3, to_level=1,
        transition_type=TransitionType.CR,
        rate=w_cr,
        partner_from=0, partner_to=1,
    )

    return Material(
        name="Test PA Material",
        host_matrix="Test",
        dopants=[ion],
        phonon_energy_cm_inv=350,
        temperature_K=300.0,
    )


def measure_nonlinearity(material: Material, pump_wavelength: float = 1064.0) -> tuple:
    """Run power sweep and extract S using proper threshold detection."""
    pump = PumpLaser(power_density_W_cm2=1e4, wavelength_nm=pump_wavelength)
    config = SolverConfig(t_end=100e-3, method="Radau")
    sim = Simulation(material, pump, config)

    # Power sweep - finer resolution
    powers = np.logspace(2, 7, 50)
    results = sim.run_power_sweep(powers, t_end=100e-3)

    # Extract emissions (from emitting level)
    emissions = []
    for r in results:
        pops = r.steady_state_populations()
        emit_key = [k for k in pops.keys() if ":E" in k][0]
        emissions.append(pops[emit_key])

    emissions = np.array(emissions)

    # Calculate local slopes (derivative in log-log space)
    log_p = np.log10(powers)
    log_e = np.log10(emissions + 1e-30)

    # Compute local slope at each point using 5-point window
    local_slopes = []
    for i in range(2, len(powers) - 2):
        slope, _ = np.polyfit(log_p[i-2:i+3], log_e[i-2:i+3], 1)
        local_slopes.append(slope)

    local_slopes = np.array(local_slopes)

    # S is the MAXIMUM slope (peak nonlinearity above threshold)
    S = np.max(local_slopes)
    S_idx = np.argmax(local_slopes) + 2
    threshold_power = powers[S_idx]

    # Uncertainty from local fit
    try:
        _, cov = np.polyfit(log_p[S_idx-2:S_idx+3], log_e[S_idx-2:S_idx+3], 1, cov=True)
        S_unc = np.sqrt(cov[0, 0])
    except:
        S_unc = 0.5

    return S, S_unc, powers, emissions, threshold_power


def run_parameter_sweep():
    """Systematically vary parameters and measure S."""

    print("=" * 70)
    print("PARAMETER SENSITIVITY STUDY: S = f(ESA/GSA, W_CR, N)")
    print("=" * 70)

    results = []

    # 1. ESA/GSA ratio sweep
    print("\n1. ESA/GSA Ratio Sweep (W_CR=5e-16, N=1.2e21)")
    print("-" * 50)
    esa_gsa_ratios = [10, 20, 50, 100, 200, 500, 1000]
    for ratio in esa_gsa_ratios:
        mat = create_test_material(esa_gsa_ratio=ratio)
        S, S_unc, _, _, thresh = measure_nonlinearity(mat)
        print(f"  ESA/GSA = {ratio:4d}×  →  S = {S:.1f} ± {S_unc:.1f}  (thresh: {thresh:.1e} W/cm²)")
        results.append(("ESA/GSA", ratio, S, S_unc))

    # 2. CR rate sweep
    print("\n2. Cross-Relaxation Rate Sweep (ESA/GSA=50, N=1.2e21)")
    print("-" * 50)
    cr_rates = [1e-17, 5e-17, 1e-16, 5e-16, 1e-15, 5e-15]
    for w_cr in cr_rates:
        mat = create_test_material(w_cr=w_cr)
        S, S_unc, _, _, thresh = measure_nonlinearity(mat)
        print(f"  W_CR = {w_cr:.0e} cm³/s  →  S = {S:.1f} ± {S_unc:.1f}  (thresh: {thresh:.1e} W/cm²)")
        results.append(("W_CR", w_cr, S, S_unc))

    # 3. Concentration sweep
    print("\n3. Ion Concentration Sweep (ESA/GSA=50, W_CR=5e-16)")
    print("-" * 50)
    concentrations = [1e20, 5e20, 1e21, 2e21, 5e21]
    for conc in concentrations:
        mat = create_test_material(concentration=conc)
        S, S_unc, _, _, thresh = measure_nonlinearity(mat)
        print(f"  N = {conc:.0e} cm⁻³  →  S = {S:.1f} ± {S_unc:.1f}  (thresh: {thresh:.1e} W/cm²)")
        results.append(("N", conc, S, S_unc))

    # 4. Combined optimization
    print("\n4. Optimized Parameters")
    print("-" * 50)
    # Try high ESA/GSA + high CR + optimal concentration
    mat_optimized = create_test_material(
        esa_gsa_ratio=500,
        w_cr=1e-15,
        concentration=2e21,
    )
    S_opt, S_unc_opt, powers, emissions, thresh_opt = measure_nonlinearity(mat_optimized)
    print(f"  ESA/GSA=500, W_CR=1e-15, N=2e21  →  S = {S_opt:.1f} ± {S_unc_opt:.1f}  (thresh: {thresh_opt:.1e} W/cm²)")

    # Derive relationships
    print("\n" + "=" * 70)
    print("PRELIMINARY RELATIONSHIPS")
    print("=" * 70)

    # Fit S vs log(ESA/GSA)
    esa_data = [(r[1], r[2]) for r in results if r[0] == "ESA/GSA"]
    x = np.log10([d[0] for d in esa_data])
    y = [d[1] for d in esa_data]
    slope, intercept = np.polyfit(x, y, 1)
    print(f"\n  S ≈ {slope:.1f} × log₁₀(ESA/GSA) + {intercept:.1f}")

    # Fit S vs log(W_CR)
    cr_data = [(r[1], r[2]) for r in results if r[0] == "W_CR"]
    x = np.log10([d[0] for d in cr_data])
    y = [d[1] for d in cr_data]
    slope_cr, intercept_cr = np.polyfit(x, y, 1)
    print(f"  S ≈ {slope_cr:.1f} × log₁₀(W_CR) + {intercept_cr:.1f}")

    print("\n" + "=" * 70)
    print("DESIGN IMPLICATIONS")
    print("=" * 70)
    print("""
    To maximize nonlinearity order S:

    1. MAXIMIZE ESA/GSA ratio
       - Use off-resonant GSA (pump wavelength detuned from ground state absorption)
       - Ensure resonant ESA from intermediate level
       - Target ESA/GSA > 100× for S > 10

    2. MAXIMIZE Cross-Relaxation rate
       - Use high dopant concentrations (but avoid clustering)
       - Choose hosts where CR energy mismatch is small
       - Low phonon hosts help only if CR mismatch is small

    3. OPTIMIZE Concentration
       - Higher N increases CR rate (W_CR × N²)
       - But too high causes concentration quenching
       - Sweet spot typically 5-10 mol%

    4. The multiplicative effect:
       S scales roughly as: log(ESA/GSA) × log(W_CR × N)
    """)

    return results


if __name__ == "__main__":
    results = run_parameter_sweep()
