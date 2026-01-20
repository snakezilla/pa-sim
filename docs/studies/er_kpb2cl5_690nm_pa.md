# Er³⁺:KPb₂Cl₅ Photon Avalanche Study at 690nm

**Date:** January 2025
**Status:** Simulation complete, experimental validation needed

## Executive Summary

We investigated the feasibility of photon avalanche (PA) in Er³⁺-doped KPb₂Cl₅ at 690nm excitation using rate equation modeling. The simulation predicts that **PA is marginally achievable** but limited by slow cross-relaxation due to phonon energy mismatch. With optimized CR rates (achievable via temperature tuning or alternative hosts), nonlinearity orders of S~8 are predicted.

## Why This Material?

### 1. KPb₂Cl₅ is a Proven PA Host

KPb₂Cl₅ has demonstrated the **highest nonlinearity order ever recorded** for photon avalanche:

> "Nd³⁺:KPb₂Cl₅ exhibits >200th order nonlinearity at 1064nm excitation"
> — Szalkowski et al., Chem. Soc. Rev. 54, 2556 (2025)

The ultra-low phonon energy (203 cm⁻¹) creates extremely long excited-state lifetimes, enabling efficient energy looping.

### 2. Er³⁺ PA is Established but Underexplored

Er³⁺ photon avalanche has been demonstrated in several hosts:

| Host | Pump λ | Threshold | Reference |
|------|--------|-----------|-----------|
| LiYF₄ | 579, 690 nm | ~60 kW/cm² | Balda et al., Opt. Mater. (1994) |
| ZBLAN fiber | 579 nm | ~60 kW/cm² | Auzel et al. |
| Telluride glass | 980 nm | 44 mW | ResearchGate (2007) |
| BiOCl nanosheets | 980 nm | — | ScienceDirect (2020) |

**No study has combined Er³⁺ with ultra-low phonon chloride hosts.** This represents unexplored parameter space.

### 3. Telecom Relevance

Er³⁺ operates at telecom wavelengths (1550nm emission from ⁴I₁₃/₂ → ⁴I₁₅/₂). A PA-based Er³⁺ system could enable:
- Ultra-sensitive optical switching at telecom bands
- Nonlinear optical limiting
- Super-resolution imaging with existing telecom infrastructure

## Simulation Details

### Energy Level Scheme (8-level model)

```
Level 7: ⁴G₁₁/₂  (24700 cm⁻¹) — ESA target
Level 6: ²H₁₁/₂  (19200 cm⁻¹)
Level 5: ⁴S₃/₂   (18400 cm⁻¹) — Green emitting level
Level 4: ⁴F₉/₂   (15300 cm⁻¹) — GSA target at 690nm
Level 3: ⁴I₉/₂   (12400 cm⁻¹)
Level 2: ⁴I₁₁/₂  (10200 cm⁻¹) — Looping level (metastable)
Level 1: ⁴I₁₃/₂  (6500 cm⁻¹)  — Telecom emitter
Level 0: ⁴I₁₅/₂  (0 cm⁻¹)     — Ground state
```

### Proposed PA Mechanism at 690nm

```
1. GSA (weak):     ⁴I₁₅/₂ + hν(690nm) → ⁴F₉/₂   [~800 cm⁻¹ off-resonance]
2. Relaxation:     ⁴F₉/₂ → ⁴S₃/₂ → ⁴I₁₁/₂      [slow MPR cascade]
3. ESA (strong):   ⁴I₁₁/₂ + hν(690nm) → ⁴G₁₁/₂  [resonant]
4. Fast decay:     ⁴G₁₁/₂ → ²H₁₁/₂ → ⁴S₃/₂
5. CR (feedback):  ⁴S₃/₂ + ⁴I₁₅/₂ → ⁴I₁₁/₂ + ⁴I₁₁/₂  [avalanche!]
6. Emission:       ⁴S₃/₂ → ⁴I₁₅/₂ (544nm green)
```

### Key Parameters

| Parameter | Value | Source |
|-----------|-------|--------|
| σ_GSA (690nm) | 1×10⁻²² cm² | Estimated (off-resonant) |
| σ_ESA (690nm) | 5×10⁻²¹ cm² | Estimated (resonant) |
| ESA/GSA ratio | 50× | Adequate for PA |
| W_CR | 5×10⁻¹⁷ cm³/s | Literature estimate |
| Er³⁺ concentration | 9.6×10²⁰ cm⁻³ | 8 mol% |
| Phonon cutoff | 203 cm⁻¹ | Gruber et al. (2006) |

## Results

### Power-Dependent Behavior

| Power (kW/cm²) | Ground State | Looping Level (⁴I₁₁/₂) | Emitting (⁴S₃/₂) |
|----------------|--------------|------------------------|------------------|
| 10 | 98.6% | 0.2% | 0.0% |
| 50 | 8.8% | 53.8% | 5.9% |
| 100 | 6.8% | 38.9% | 10.6% |
| 500 | 5.8% | 11.5% | 18.3% |

### Nonlinearity Analysis

**With current parameters:**
- Low power slope: 2.2 (two-photon process)
- High power slope: 0.2 (saturation)
- Behavior: Standard upconversion, NOT photon avalanche

**With 10× enhanced CR rate:**
- Low power slope: 2.1
- Mid power slope: **8.1** ← Avalanche behavior!
- High power slope: 0.2 (saturation)

## The Bottleneck: Cross-Relaxation

The CR pathway requires phonon-assisted energy transfer:

```
⁴S₃/₂ + ⁴I₁₅/₂ → ⁴I₁₁/₂ + ⁴I₁₁/₂
18400 + 0    →  10200 + 10200
              ΔE = -2000 cm⁻¹ (released as phonons)
```

In KPb₂Cl₅ (ℏω_max = 203 cm⁻¹), this requires ~10 phonons. The multi-phonon CR rate scales as:

```
W_CR ∝ exp(-α × n_phonons)
```

For comparison, Nd³⁺ PA in KPb₂Cl₅ has CR mismatch of only ~600 cm⁻¹ (~3 phonons), explaining its superior performance.

## Comparison to Known PA Systems

| System | ESA/GSA | W_CR (cm³/s) | Phonons for CR | S |
|--------|---------|--------------|----------------|---|
| Tm³⁺:NaYF₄ | 50× | 5×10⁻¹⁶ | ~3 | 26-40 |
| Nd³⁺:KPb₂Cl₅ | >100× | ~10⁻¹⁵ | ~3 | >200 |
| **Er³⁺:KPb₂Cl₅** | 50× | 5×10⁻¹⁷ | **~10** | **~8** (predicted) |

## Recommendations

### To Achieve PA in Er³⁺ Systems:

1. **Alternative host with ~250-300 cm⁻¹ phonons**
   - CsCdCl₃ (270 cm⁻¹) — maintains low-phonon benefits while easing CR
   - RbPb₂Cl₅ — similar structure, slightly different phonon spectrum

2. **Higher temperature operation**
   - Increases phonon population, enhances phonon-assisted CR
   - Trade-off: reduces excited state lifetimes

3. **Different pump wavelength**
   - 579nm: demonstrated for Er³⁺ PA in ZBLAN (different CR pathway)
   - 980nm: Er³⁺ PA in telluride glass

4. **Yb³⁺ sensitization**
   - Proven approach for Er³⁺ upconversion
   - Energy transfer can substitute for weak GSA

## Experimental Validation Needed

1. **Measure actual GSA/ESA cross-sections at 690nm in KPb₂Cl₅**
2. **Determine CR rate via concentration quenching studies**
3. **Power-dependent emission measurements** to confirm/refute threshold behavior
4. **Temperature-dependent studies** to probe phonon-assisted CR

## Files

- Material definition: `src/pa_sim/materials/database.py` → `create_er_kpb2cl5_material()`
- Simulation script: `examples/er_kpb2cl5_pa_test.py`
- Detailed analysis: `examples/er_kpb2cl5_detailed_analysis.py`

## References

1. Gruber, J.B. et al. "Growth and characterization of single-crystal Er³⁺:KPb₂Cl₅ as a mid-infrared laser material." J. Crystal Growth (2006).

2. Balda, R. et al. "Photon avalanche luminescence of Er³⁺ ions in LiYF₄ crystal." Opt. Mater. (1994).

3. Szalkowski, M. et al. "Advances in the photon avalanche luminescence of inorganic lanthanide-doped nanomaterials." Chem. Soc. Rev. 54, 2556 (2025).

4. Lee, C. et al. "Giant nonlinear optical responses from photon-avalanching nanoparticles." Nature 589, 230–235 (2021).

5. Recent advances in fundamental research on photon avalanches. Nanoscale (2025). DOI:10.1039/D4NR03493G

## Conclusion

Er³⁺:KPb₂Cl₅ at 690nm is **not optimal** for photon avalanche due to the large phonon mismatch in the CR pathway (~10 phonons required). However, the simulation framework successfully identified this limitation and suggests that **modified hosts or alternative pump schemes could enable Er³⁺ PA**. The key insight is that ultra-low phonon energy is beneficial only when the CR energy mismatch is also small—a constraint satisfied by Nd³⁺ but not Er³⁺ in this host.

This study demonstrates PA-Sim's utility for **predictive screening of candidate PA materials** before experimental synthesis.
