# PA-Sim Development Session Log
**Date:** January 20, 2025

## Overview

This session covered the development and validation of PA-Sim, a photon avalanching simulation framework, including exploration of new materials and discussion of future directions.

---

## Key Accomplishments

### 1. Created PA-Sim Framework
- Location: `/Users/ahsan/Projects/pa-sim`
- GitHub: https://github.com/snakezilla/pa-sim
- Core functionality: Rate equation solver for photon avalanche simulation

### 2. Er³⁺:KPb₂Cl₅ Material Study
**Question:** Can Er³⁺ achieve photon avalanche in the ultra-low phonon KPb₂Cl₅ host?

**Finding:** Marginal. The CR pathway requires ~2000 cm⁻¹ phonon emission (~10 phonons), making it slow. With 10× enhanced CR, S~8 emerges.

**Key insight:** Ultra-low phonon hosts only help when the CR energy mismatch is also small. KPb₂Cl₅ works great for Nd³⁺ (~600 cm⁻¹ mismatch, ~3 phonons) but not Er³⁺.

**Files:**
- `docs/studies/er_kpb2cl5_690nm_pa.md`
- `examples/er_kpb2cl5_pa_test.py`
- `examples/er_kpb2cl5_detailed_analysis.py`

### 3. Parameter Sensitivity Analysis
**Question:** How does nonlinearity order S depend on material parameters?

**Finding:** Logarithmic relationships:
```
S ≈ 2.8 × log₁₀(ESA/GSA) + constant
S ≈ 2.9 × log₁₀(W_CR) + constant
```

**Key results:**
| ESA/GSA | S | Threshold |
|---------|---|-----------|
| 10× | 7.6 | 18 kW/cm² |
| 100× | 10.6 | 2.1 kW/cm² |
| 1000× | 13.2 | 260 W/cm² |

**Files:**
- `examples/s_parameter_sensitivity.py`
- `examples/validate_against_literature.py`

### 4. Validation Results
- **What works:** Population conservation, saturation behavior, parameter trends
- **What's off:** Predicted S ~11 vs published S ~26-31 for Tm³⁺:NaYF₄ (2.5× low)
- **Why:** Simplified 4-level model, approximate parameters

---

## Key Concepts Explained

### What is Photon Avalanche?
A chain reaction in lanthanide ions:
1. Weak ground state absorption (GSA) seeds a few excited ions
2. Cross-relaxation (CR): excited + ground → 2× intermediate
3. Strong excited state absorption (ESA) from intermediate → more excited
4. Repeat → exponential growth above threshold

### Key Parameters
| Parameter | Symbol | Units | Role |
|-----------|--------|-------|------|
| GSA cross-section | σ_GSA | cm² | How easily ground state absorbs (should be WEAK) |
| ESA cross-section | σ_ESA | cm² | How easily intermediate absorbs (should be STRONG) |
| CR rate | W_CR | cm³/s | How fast the avalanche feedback works |
| Concentration | N | ions/cm³ | More ions = more CR events |
| Phonon energy | ℏω | cm⁻¹ | Determines non-radiative relaxation rates |

### Design Rules for High S
1. **Maximize ESA/GSA ratio** (>100× for S>10)
2. **Maximize CR rate** (need efficient energy transfer)
3. **Optimize concentration** (5-10 mol% typical sweet spot)
4. **Match CR energy** to minimize phonon involvement

---

## Ideas Discussed But Not Implemented

### 1. Materials Project (mp_api) Integration
- Could use MP's phonon DOS data to screen host materials
- ~5000 materials have phonon calculations
- Would predict ℏω_max from composition without DFT
- **Status:** Concept documented in `docs/FUTURE_MP_INTEGRATION.md`

### 2. Neural Network for Material Discovery
- Train on MP phonon data to predict PA host suitability
- ALIGNN achieves MAE ~25 cm⁻¹ on phonon prediction
- **Novelty:** Low (applying existing ML to new domain)
- **Status:** Concept documented in `docs/concepts/nn_material_discovery.md`

### 3. Quantitative S Prediction (Design Rules)
- Derive S = f(ESA/GSA, W_CR, N) relationship
- **Novelty:** Medium-high (not published in this form)
- **Status:** Preliminary results, needs calibration against more systems

---

## Historical Context Clarified

**Photon avalanche is NOT new (discovered 1979)**

| Year | Milestone |
|------|-----------|
| 1979 | Chivian discovers PA in bulk Pr³⁺:LaCl₃ |
| 1994 | Er³⁺ PA in bulk LiYF₄ at 690nm |
| 2021 | **First PA in nanoparticles** (Lee et al., Nature) ← This is what's "new" |
| 2025 | S > 500 achieved via sublattice reconstruction |

---

## What Would Wow Schuck Lab

1. **Quantitative S prediction tool** - Currently guidance is qualitative ("high ESA/GSA + efficient CR")
2. **Calibrated against their data** - Need their measured parameters
3. **Predict unpublished results** - Show the tool works before they run experiments

**Gap identified:** Everyone has simulations, nobody has design rules that predict S from parameters.

---

## Files Created This Session

```
pa-sim/
├── src/pa_sim/materials/database.py    # Added Er_KPb2Cl5_5pct, Er_KPb2Cl5_8pct
├── docs/
│   ├── studies/
│   │   └── er_kpb2cl5_690nm_pa.md      # Full Er³⁺ study writeup
│   ├── concepts/
│   │   └── nn_material_discovery.md    # NN approach concept
│   ├── FUTURE_MP_INTEGRATION.md        # Materials Project integration plan
│   └── SESSION_LOG_2025_01_20.md       # This file
└── examples/
    ├── er_kpb2cl5_pa_test.py           # Basic Er³⁺ simulation
    ├── er_kpb2cl5_detailed_analysis.py # Comparison with Tm³⁺
    ├── s_parameter_sensitivity.py      # Parameter sweep study
    └── validate_against_literature.py  # Validation against published data
```

---

## Next Steps (If Continuing)

1. **Calibrate model** - Get actual measured parameters from literature or collaborators
2. **Validate against more systems** - Nd³⁺:KPb₂Cl₅, Er³⁺:ZBLAN, etc.
3. **Derive analytical S formula** - If possible, derive rather than just fit
4. **Contact Schuck lab** - Propose collaboration with calibrated tool

---

## Commands to Reproduce

```bash
cd /Users/ahsan/Projects/pa-sim
source .venv/bin/activate

# Run parameter sensitivity study
python examples/s_parameter_sensitivity.py

# Run validation
python examples/validate_against_literature.py

# Run Er³⁺:KPb₂Cl₅ analysis
python examples/er_kpb2cl5_detailed_analysis.py
```

---

## References Used

1. Lee, C. et al. "Giant nonlinear optical responses from photon-avalanching nanoparticles." Nature 589, 230–235 (2021).
2. Szalkowski, M. et al. "Advances in photon avalanche luminescence." Chem. Soc. Rev. 54, 2556 (2025).
3. Gruber, J.B. et al. "Er³⁺:KPb₂Cl₅ spectroscopy." J. Crystal Growth (2006).
4. Balda, R. et al. "Photon avalanche luminescence of Er³⁺ in LiYF₄." Opt. Mater. (1994).
5. Chivian, J. et al. "The photon avalanche." Appl. Phys. Lett. 35, 124 (1979).
