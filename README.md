# PA-Sim

Simulates photon avalanching in lanthanide-doped nanoparticles.

## Why

Each lab writes their own rate equation code. Nobody shares it. Results vary 40× for the same material. The 2025 Chem Soc Rev paper (Szalkowski et al.) explicitly calls for standardization. This is that.

## What it does

Solves coupled ODEs describing population dynamics across energy levels. You define a material (ions, levels, transitions), specify a pump laser, and it gives you time-resolved populations and emission.

## Governing equations

For each energy level i:

```
dNᵢ/dt = Σ(in-flux) - Σ(out-flux)
```

Expanded for a 3-level Tm³⁺ system:

```
dN₀/dt = -σ_GSA·Φ·N₀ + A₁₀·N₁ + A₃₀·N₃ + W_CR·N₃·N₀
dN₁/dt = -σ_ESA·Φ·N₁ + A₃₁·N₃ + 2·W_CR·N₃·N₀
dN₃/dt = +σ_GSA·Φ·N₀ + σ_ESA·Φ·N₁ - (A₃₀+A₃₁)·N₃ - W_CR·N₃·N₀
```

Where:
- `σ_GSA`, `σ_ESA`: absorption cross-sections (cm²)
- `Φ`: photon flux (photons/cm²/s)
- `A`: radiative decay rates (s⁻¹)
- `W_CR`: cross-relaxation coefficient (cm³/s)
- `N`: population densities (ions/cm³)

The `W_CR·N₃·N₀` term is the avalanche feedback—one excited ion + one ground ion → two intermediate ions.

## Inputs

- Energy levels (name, energy in cm⁻¹)
- Transitions (type, rate constant)
- Ion concentration (ions/cm³)
- Pump wavelength and power density

## Outputs

- `N(t)` for each level
- Steady-state populations
- Extracted PA parameters: threshold, nonlinearity order (S), rise time

## Assumptions

1. Homogeneous ion distribution (no clustering)
2. Mean-field rate equations (no spatial correlations)
3. Constant temperature (no laser heating)
4. Single ion species (no co-doping cross-terms)
5. No photon reabsorption

## Install

```bash
git clone https://github.com/ahsannaveed007/pa-sim.git
cd pa-sim
pip install -e ".[viz]"
```

## Usage

```python
from pa_sim import Simulation, PumpLaser
from pa_sim.materials import load_material
from pa_sim.analysis import analyze_power_sweep
import numpy as np

material = load_material("Tm_NaYF4_8pct")
sim = Simulation(material, PumpLaser(power_density_W_cm2=5e4))
result = sim.run()

# Power sweep
powers = np.logspace(3, 6, 20)
results = sim.run_power_sweep(powers)
params = analyze_power_sweep(results, "Tm3+:3H4")
print(params)  # threshold, S, rise time
```

## Validation

Based on Lee et al. (2021) Nature 589, 230–235. Parameters are approximate—validate against your own measurements.

## Docs

See `docs/TECHNICAL_OVERVIEW.md` for the full physics explanation.

## License

MIT
