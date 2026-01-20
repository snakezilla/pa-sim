# Materials Project Integration Concept

## The Opportunity

[Materials Project](https://materialsproject.org) contains DFT-calculated properties for ~150,000+ materials, including **phonon band structures and DOS**. This could enable automated screening of host matrices for photon avalanche applications.

## What MP Provides (Relevant to PA)

| Property | Relevance to PA | MP Endpoint |
|----------|----------------|-------------|
| Phonon DOS | Phonon cutoff energy → MPR rates | `mpr.materials.phonon` |
| Phonon band structure | Detailed phonon spectrum | `mpr.get_phonon_bandstructure_by_material_id()` |
| Dielectric tensor | Refractive index, optical transparency | `mpr.materials.dielectric` |
| Band gap | Optical transparency window | `mpr.materials.summary` |
| Formation energy | Thermodynamic stability | `mpr.materials.thermo` |
| Crystal structure | Dopant site symmetry | `mpr.materials.structure` |

## What MP Does NOT Provide (Still Needed)

- **Lanthanide energy levels** — Requires crystal field analysis or spectroscopic measurement
- **Absorption/emission cross-sections** — Judd-Ofelt calculations from experimental spectra
- **Cross-relaxation rates** — Concentration quenching studies
- **ESA spectra** — Specialized pump-probe spectroscopy

The 4f electrons in lanthanides are highly localized and not well-described by standard DFT.

## Proposed Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     PA-Sim Workflow                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐     ┌──────────────┐     ┌─────────────┐ │
│  │ Materials    │     │ Host Matrix  │     │ Lanthanide  │ │
│  │ Project API  │────▶│ Properties   │────▶│ Database    │ │
│  │ (mp_api)     │     │              │     │             │ │
│  └──────────────┘     └──────────────┘     └─────────────┘ │
│        │                     │                    │         │
│        ▼                     ▼                    ▼         │
│  ┌──────────────┐     ┌──────────────┐     ┌─────────────┐ │
│  │ Phonon DOS   │     │ Gap Law MPR  │     │ Energy      │ │
│  │ → ℏω_max     │────▶│ Calculator   │◀────│ Levels      │ │
│  └──────────────┘     └──────────────┘     └─────────────┘ │
│                              │                              │
│                              ▼                              │
│                    ┌──────────────────┐                    │
│                    │ Rate Equation    │                    │
│                    │ System           │                    │
│                    └──────────────────┘                    │
│                              │                              │
│                              ▼                              │
│                    ┌──────────────────┐                    │
│                    │ PA Simulation    │                    │
│                    └──────────────────┘                    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Use Case 1: Screen Hosts by Phonon Energy

```python
from mp_api.client import MPRester
from pa_sim.screening import PhononScreener

# Find materials with phonon cutoff 150-300 cm⁻¹
with MPRester(api_key="YOUR_KEY") as mpr:
    screener = PhononScreener(mpr)

    candidates = screener.find_hosts(
        phonon_cutoff_range=(150, 300),  # cm⁻¹
        band_gap_min=3.0,                 # eV (optically transparent)
        contains_elements=["F", "Cl"],    # Halides preferred
        exclude_elements=["O"],           # Avoid oxides (high phonon)
        stability_threshold=0.1,          # eV/atom above hull
    )

    for mat in candidates:
        print(f"{mat.formula}: ℏω_max = {mat.phonon_cutoff} cm⁻¹")
```

## Use Case 2: Calculate MPR Rates from Phonon DOS

The multiphonon relaxation rate follows the energy gap law:

```
W_MPR = W_0 × exp(-α × ΔE / ℏω_max)
```

With the full phonon DOS, we can calculate this more accurately:

```python
from pa_sim.physics import MultiphononRelaxation

# Get phonon DOS from Materials Project
phonon_dos = mpr.get_phonon_dos_by_material_id("mp-2534")  # NaYF4

mpr_calc = MultiphononRelaxation(phonon_dos)

# Calculate MPR rate for 3H4 → 3H5 transition in Tm³⁺
# ΔE = 12600 - 8300 = 4300 cm⁻¹
rate = mpr_calc.calculate_rate(
    energy_gap_cm_inv=4300,
    temperature_K=300,
)
print(f"W_MPR = {rate:.2e} s⁻¹")
```

## Use Case 3: Automated PA Candidate Discovery

```python
from pa_sim.discovery import PAMaterialDiscovery

discovery = PAMaterialDiscovery(
    dopant="Nd3+",           # Specify lanthanide
    pump_wavelength_nm=1064,  # Target pump wavelength
    mpr_api_key="YOUR_KEY",
)

# Screen Materials Project for potential PA hosts
results = discovery.screen_hosts(
    max_candidates=100,
    require_nonhygroscopic=True,
)

# Run PA simulations on top candidates
for host in results[:10]:
    material = discovery.build_material(host, dopant_concentration_pct=5.0)
    params = discovery.simulate_pa(material)

    if params.nonlinearity_order > 10:
        print(f"🎯 {host.formula}: S = {params.nonlinearity_order:.0f}")
```

## Implementation Roadmap

### Phase 1: Phonon Data Integration
- [ ] Add `mp_api` as optional dependency
- [ ] Create `PhononScreener` class
- [ ] Implement phonon cutoff extraction from DOS
- [ ] Cache MP queries to avoid rate limits

### Phase 2: Gap Law Calculator
- [ ] Implement Miyakawa-Dexter gap law with full phonon DOS
- [ ] Validate against literature MPR rates
- [ ] Auto-calculate MPR transitions when host is specified

### Phase 3: Discovery Pipeline
- [ ] Build end-to-end screening workflow
- [ ] Create lanthanide spectroscopy database (from literature)
- [ ] Implement Judd-Ofelt parameter estimation
- [ ] Generate ranked candidate lists

## Data Sources to Combine

| Data Type | Source | Coverage |
|-----------|--------|----------|
| Host phonon properties | Materials Project | ~5000 materials with phonon data |
| Lanthanide energy levels | NIST ASD, literature | All Ln³⁺ ions |
| Judd-Ofelt parameters | Literature compilation | ~100 host/dopant combinations |
| Cross-relaxation rates | Literature | ~20 well-characterized systems |

## Limitations

1. **MP phonon data is incomplete** — Not all materials have calculated phonon spectra
2. **DFT phonon accuracy** — Calculated values can differ from experiment by 10-20%
3. **Dopant perturbation** — MP calculations are for pure hosts; dopants modify local phonon modes
4. **No direct CR rates** — Cross-relaxation requires ion-ion interaction modeling beyond DFT

## References

- [Materials Project Documentation](https://docs.materialsproject.org/)
- [mp-api Python client](https://github.com/materialsproject/api)
- Miyakawa, T. & Dexter, D.L. "Phonon sidebands, multiphonon relaxation of excited states, and phonon-assisted energy transfer." Phys. Rev. B 1, 2961 (1970).
