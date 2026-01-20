"""
Detailed analysis of Er3+:KPb2Cl5 PA simulation.

Investigate why PA behavior isn't emerging and what parameters
would need to change.
"""

import numpy as np
from pa_sim import Simulation, PumpLaser, SolverConfig
from pa_sim.materials import load_material

# Load materials for comparison
er_material = load_material("Er_KPb2Cl5_8pct")
tm_material = load_material("Tm_NaYF4_8pct")  # Known PA system

print("=" * 70)
print("COMPARING Er3+:KPb2Cl5 vs Tm3+:NaYF4 (known PA system)")
print("=" * 70)

# Get key parameters
er_ion = er_material.dopants[0]
tm_ion = tm_material.dopants[0]

print("\nKEY PA PARAMETERS:")
print("-" * 70)

# Find GSA and ESA cross-sections
def get_transition_rate(ion, from_lvl, to_lvl, t_type):
    for t in ion.transitions:
        if t.from_level == from_lvl and t.to_level == to_lvl and t.transition_type.name == t_type:
            return t.rate
    return None

# Tm3+ parameters
tm_gsa = get_transition_rate(tm_ion, 0, 3, "GSA")
tm_esa = get_transition_rate(tm_ion, 1, 3, "ESA")
tm_cr = None
for t in tm_ion.transitions:
    if t.transition_type.name == "CR":
        tm_cr = t.rate
        break

print(f"\nTm3+:NaYF4 (KNOWN PA):")
print(f"  σ_GSA: {tm_gsa:.2e} cm²")
print(f"  σ_ESA: {tm_esa:.2e} cm²")
print(f"  ESA/GSA ratio: {tm_esa/tm_gsa:.0f}")
print(f"  W_CR: {tm_cr:.2e} cm³/s")
print(f"  Concentration: {tm_ion.concentration:.2e} ions/cm³")
print(f"  Phonon energy: {tm_material.phonon_energy_cm_inv} cm⁻¹")

# Er3+ parameters
er_gsa = get_transition_rate(er_ion, 0, 4, "GSA")  # To 4F9/2
er_esa = get_transition_rate(er_ion, 2, 7, "ESA")  # 4I11/2 -> 4G11/2
er_cr = None
for t in er_ion.transitions:
    if t.transition_type.name == "CR":
        er_cr = t.rate
        break

print(f"\nEr3+:KPb2Cl5 (EXPERIMENTAL):")
print(f"  σ_GSA: {er_gsa:.2e} cm²")
print(f"  σ_ESA: {er_esa:.2e} cm²")
print(f"  ESA/GSA ratio: {er_esa/er_gsa:.0f}")
print(f"  W_CR: {er_cr:.2e} cm³/s")
print(f"  Concentration: {er_ion.concentration:.2e} ions/cm³")
print(f"  Phonon energy: {er_material.phonon_energy_cm_inv} cm⁻¹")

print(f"\n" + "=" * 70)
print("DIAGNOSIS:")
print("=" * 70)

# Check ESA/GSA ratio - needs to be high for PA
ratio_er = er_esa / er_gsa
ratio_tm = tm_esa / tm_gsa
print(f"\n1. ESA/GSA Ratio:")
print(f"   Er³⁺: {ratio_er:.0f}x")
print(f"   Tm³⁺: {ratio_tm:.0f}x")
if ratio_er < 30:
    print("   ⚠ Er³⁺ ESA/GSA ratio may be too low for strong PA")
else:
    print("   ✓ ESA/GSA ratio adequate")

# Check CR rate
cr_ratio = er_cr / tm_cr
print(f"\n2. Cross-Relaxation Rate:")
print(f"   Er³⁺: {er_cr:.2e} cm³/s")
print(f"   Tm³⁺: {tm_cr:.2e} cm³/s")
print(f"   Ratio: {cr_ratio:.1f}x")
if er_cr < tm_cr * 0.1:
    print("   ⚠ Er³⁺ CR rate may be too slow for efficient PA")
else:
    print("   ✓ CR rate adequate")

# Check concentration
conc_ratio = er_ion.concentration / tm_ion.concentration
print(f"\n3. Ion Concentration:")
print(f"   Er³⁺: {er_ion.concentration:.2e} ions/cm³")
print(f"   Tm³⁺: {tm_ion.concentration:.2e} ions/cm³")

# Time-resolved analysis at different powers
print(f"\n" + "=" * 70)
print("TIME-RESOLVED POPULATION DYNAMICS")
print("=" * 70)

powers_to_test = [1e4, 5e4, 1e5, 5e5]  # W/cm²

for power in powers_to_test:
    pump = PumpLaser(power_density_W_cm2=power, wavelength_nm=690.0)
    config = SolverConfig(t_end=200e-3, method="Radau")
    sim = Simulation(er_material, pump, config)
    result = sim.run()

    # Get final populations
    final_pops = result.populations[:, -1]
    total = final_pops.sum()

    print(f"\nPower = {power/1000:.0f} kW/cm²:")
    print(f"  Ground (4I15/2):    {100*final_pops[0]/total:5.1f}%")
    print(f"  Metastable (4I13/2): {100*final_pops[1]/total:5.1f}%")
    print(f"  Loop level (4I11/2): {100*final_pops[2]/total:5.1f}%")
    print(f"  4I9/2:              {100*final_pops[3]/total:5.1f}%")
    print(f"  4F9/2:              {100*final_pops[4]/total:5.1f}%")
    print(f"  Emitting (4S3/2):   {100*final_pops[5]/total:5.1f}%")

# Suggest parameter modifications
print(f"\n" + "=" * 70)
print("RECOMMENDATIONS FOR IMPROVING PA:")
print("=" * 70)

print("""
1. INCREASE CR RATE (W_CR):
   Current: 5×10⁻¹⁷ cm³/s (10x lower than Tm³⁺)
   The CR pathway 4S3/2 + 4I15/2 → 2×4I11/2 requires ~2000 cm⁻¹
   phonon emission (~10 phonons in KPb2Cl5).

   Options:
   a) Find a better CR pathway with smaller energy mismatch
   b) Increase temperature to enhance phonon-assisted CR
   c) Use a host with slightly higher phonon energy (~300 cm⁻¹)

2. ENSURE PROPER LEVEL POPULATION DYNAMICS:
   The 4I11/2 level needs to accumulate population for ESA.
   Currently, relaxation pathways may be draining it too fast.

3. CONSIDER ALTERNATIVE PUMP WAVELENGTH:
   - 579nm has demonstrated PA in Er³⁺:ZBLAN
   - 980nm shows PA in Er³⁺:telluride glass

4. TRY SENSITIZED PA:
   Add Yb³⁺ as sensitizer for energy transfer to Er³⁺.
   This is a proven approach for Er³⁺ upconversion systems.
""")

# Test with increased CR rate
print(f"\n" + "=" * 70)
print("SIMULATION WITH ENHANCED CR RATE (10x)")
print("=" * 70)

# Modify the material with higher CR
from pa_sim.core.material import Material, LanthanideIon, TransitionType

er_enhanced = LanthanideIon(symbol="Er3+", concentration=er_ion.concentration)

# Copy levels
for lvl in er_ion.levels:
    er_enhanced.add_level(lvl.name, lvl.energy_cm_inv, lvl.degeneracy)

# Copy transitions but enhance CR
for t in er_ion.transitions:
    if t.transition_type == TransitionType.CR:
        # 10x higher CR rate
        er_enhanced.add_transition(
            t.from_level, t.to_level, t.transition_type, rate=t.rate * 10,
            partner_from=t.partner_from, partner_to=t.partner_to
        )
    else:
        if hasattr(t, 'partner_from'):
            er_enhanced.add_transition(
                t.from_level, t.to_level, t.transition_type, rate=t.rate,
                partner_from=t.partner_from, partner_to=t.partner_to,
                wavelength_nm=t.wavelength_nm
            )
        else:
            er_enhanced.add_transition(
                t.from_level, t.to_level, t.transition_type, rate=t.rate,
                wavelength_nm=t.wavelength_nm
            )

enhanced_material = Material(
    name="Enhanced Er:KPb2Cl5",
    host_matrix="KPb2Cl5",
    dopants=[er_enhanced],
    phonon_energy_cm_inv=203,
    temperature_K=300.0,
)

# Power sweep with enhanced material
pump = PumpLaser(power_density_W_cm2=1e5, wavelength_nm=690.0)
config = SolverConfig(t_end=200e-3, method="Radau")
sim_enhanced = Simulation(enhanced_material, pump, config)

powers = np.logspace(3, 6, 20)
results_enhanced = sim_enhanced.run_power_sweep(powers, t_end=200e-3)

# Extract emissions
emissions_enhanced = []
for r in results_enhanced:
    pops = r.steady_state_populations()
    emissions_enhanced.append(pops.get("Er3+:4S3/2", 0))

emissions_enhanced = np.array(emissions_enhanced)

# Calculate slopes
log_p = np.log10(powers)
log_e = np.log10(emissions_enhanced + 1e-10)

n_third = len(powers) // 3
slope_low = np.polyfit(log_p[:n_third], log_e[:n_third], 1)[0]
slope_mid = np.polyfit(log_p[n_third:2*n_third], log_e[n_third:2*n_third], 1)[0]
slope_high = np.polyfit(log_p[-n_third:], log_e[-n_third:], 1)[0]

print(f"\nWith 10x enhanced CR rate:")
print(f"  Low power slope:  {slope_low:.1f}")
print(f"  Mid power slope:  {slope_mid:.1f}")
print(f"  High power slope: {slope_high:.1f}")

if slope_mid > slope_low * 1.5 and slope_mid > 5:
    print("\n  ✓ Avalanche-like behavior emerges with enhanced CR!")
else:
    print("\n  ⚠ PA behavior still not evident - may need further optimization")
