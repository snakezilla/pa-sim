# PA-Sim: Technical Overview for Non-Specialists

**A Complete Guide to Understanding Photon Avalanching Simulation**

*Written for PhD-level readers from any field*

---

## Table of Contents

1. [What Problem Does This Solve?](#1-what-problem-does-this-solve)
2. [The Physical Phenomenon: Photon Avalanching](#2-the-physical-phenomenon-photon-avalanching)
3. [The Mathematical Model](#3-the-mathematical-model)
4. [How the Simulation Works](#4-how-the-simulation-works)
5. [Key Assumptions and Limitations](#5-key-assumptions-and-limitations)
6. [Validation and Scientific Defensibility](#6-validation-and-scientific-defensibility)
7. [Glossary](#7-glossary)

---

## 1. What Problem Does This Solve?

### The Short Version

Certain nanoparticles exhibit an extreme optical nonlinearity: shine a laser on them, and beyond a threshold intensity, their light emission increases dramatically—not proportionally to the input, but to the **26th power** of the input intensity. A 10% increase in laser power can cause a 1000% increase in emitted light.

This phenomenon is called **photon avalanching**, and it's useful for:
- Super-resolution microscopy (seeing things smaller than the wavelength of light)
- Ultra-sensitive force and temperature sensors
- Optical computing (using light instead of electrons for computation)

### The Problem

Researchers studying these materials need to simulate their behavior computationally, but:

1. **No standard tool exists.** Each research group writes their own code, which isn't shared or validated.
2. **Results vary wildly.** Different labs report nonlinearities ranging from 12 to 500 for similar materials—a 40× discrepancy.
3. **The physics is complex.** The simulations involve stiff differential equations spanning timescales from femtoseconds to milliseconds.

### What PA-Sim Does

PA-Sim is an open-source Python framework that:
- Provides a validated, generalizable simulation engine
- Implements standardized methods for extracting key parameters
- Allows researchers to define custom materials and compare results

---

## 2. The Physical Phenomenon: Photon Avalanching

### 2.1 Background: What Are These Materials?

The materials in question are **nanoparticles** (tiny crystals, typically 10-100 nanometers in diameter) made of a transparent host crystal (like NaYF₄, sodium yttrium fluoride) **doped** with small amounts of **lanthanide ions**.

**Lanthanides** (also called rare earth elements) are the elements from lanthanum to lutetium in the periodic table. Their electrons occupy special orbitals (called 4f orbitals) that are shielded from the environment, giving them unique optical properties:
- They have many discrete energy levels (like rungs on a ladder)
- They can absorb and emit light at very specific wavelengths
- They can transfer energy to neighboring ions

Common lanthanides used: Thulium (Tm³⁺), Neodymium (Nd³⁺), Erbium (Er³⁺), Ytterbium (Yb³⁺).

### 2.2 Energy Levels: The Ladder Analogy

Think of each lanthanide ion as having an "energy ladder" with discrete rungs:

```
        ┌─────────────┐
Level 3 │    3H4      │  ← Emitting level (12,600 cm⁻¹)
        └─────────────┘
              ↑
        ┌─────────────┐
Level 2 │    3H5      │  ← Intermediate (8,300 cm⁻¹)
        └─────────────┘
              ↑
        ┌─────────────┐
Level 1 │    3F4      │  ← "Looping" level (5,600 cm⁻¹)
        └─────────────┘
              ↑
        ┌─────────────┐
Level 0 │    3H6      │  ← Ground state (0 cm⁻¹)
        └─────────────┘
```

The labels (³H₆, ³F₄, etc.) are spectroscopic term symbols—you can think of them as names for each rung. The numbers in cm⁻¹ (wavenumbers) represent energy above the ground state.

### 2.3 Normal Light Absorption

In **normal absorption**, a photon (particle of light) hits an ion and kicks an electron from a lower level to a higher level. The energy of the photon must match the energy gap between levels.

```
Before:     After:
   ○           ●      ← Electron moved up
   │           │
   ●    +  💡  ○      ← Photon absorbed
```

The ion then **relaxes** back down, either:
- **Radiatively**: Emitting a photon (this is luminescence/fluorescence)
- **Non-radiatively**: Releasing energy as heat (vibrations in the crystal lattice)

### 2.4 The Avalanche Mechanism: Three Key Processes

Photon avalanching requires three processes working together:

#### Process 1: Ground State Absorption (GSA) — The Spark

A photon is absorbed from the ground state, exciting an ion to a high energy level.

```
   ●  ←  Excited
   │
   │   💡 (absorbed)
   │
   ○  ←  Was here
```

**Crucially, this process is WEAK** in avalanching materials. The laser wavelength is slightly off-resonance with this transition. Think of it as trying to push a swing at the wrong frequency—it works, but poorly.

#### Process 2: Excited State Absorption (ESA) — The Amplifier

If an ion is already in an intermediate excited state (Level 1), it can absorb ANOTHER photon much more efficiently, jumping to a higher level.

```
   ●  ←  Final state
   │
   │   💡 (absorbed efficiently!)
   │
   ●  ←  Was already excited here
   │
   ○  ←  Ground state
```

**This process is STRONG.** The laser is resonant with this transition. It's like pushing a swing at exactly the right moment.

#### Process 3: Cross-Relaxation (CR) — The Avalanche Trigger

This is the key mechanism. When an ion in a high excited state (Level 3) is near an ion in the ground state (Level 0), they can exchange energy:

```
BEFORE:                    AFTER:
Ion A    Ion B            Ion A    Ion B
  ●        ○                ●        ●     ← BOTH in Level 1!
  │        │                │        │
  │        │       →        │        │
  │        │                │        │
  ○        ●                ○        ○
(excited) (ground)        (intermediate) (intermediate)
```

**One excited ion creates TWO ions in the intermediate state.**

These two ions can now undergo ESA (Process 2), creating two more highly excited ions, which can undergo CR, creating four intermediate ions, then eight, then sixteen...

**This is the avalanche.** It's an exponential chain reaction, like nuclear fission but with photons instead of neutrons.

### 2.5 Why There's a Threshold

The avalanche only occurs above a **threshold** laser intensity because:

1. **Below threshold**: The weak GSA slowly populates excited states, but they decay (radiatively or non-radiatively) before the CR chain reaction can take off. The system reaches a boring, low-emission steady state.

2. **Above threshold**: GSA populates excited states faster than they decay. The CR chain reaction becomes self-sustaining. The system "ignites" into a high-emission state.

The transition between these regimes is sharp, which is why PA materials show extreme nonlinearity around the threshold.

### 2.6 Visual Summary

```
                        PHOTON AVALANCHING CYCLE

    ┌─────────────────────────────────────────────────────────┐
    │                                                         │
    │   1. Weak GSA: Ground → High (slow, inefficient)       │
    │              ↓                                          │
    │   2. Cross-Relaxation: 1 high + 1 ground → 2 middle    │
    │              ↓                                          │
    │   3. Strong ESA: Middle → High (fast, efficient)       │
    │              ↓                                          │
    │   4. Repeat from step 2 (AVALANCHE!)                   │
    │              ↓                                          │
    │   5. Emission from high level → detected signal        │
    │                                                         │
    └─────────────────────────────────────────────────────────┘
```

---

## 3. The Mathematical Model

### 3.1 The Core Idea: Population Dynamics

We track how many ions are in each energy level as a function of time. Let:

- **N₀(t)** = number of ions in ground state (Level 0) per cm³
- **N₁(t)** = number of ions in Level 1 per cm³
- **N₂(t)** = number of ions in Level 2 per cm³
- **N₃(t)** = number of ions in Level 3 per cm³

The total number of ions is conserved:

```
N₀ + N₁ + N₂ + N₃ = N_total (constant)
```

### 3.2 The Rate Equations

For each level, we write an equation describing how its population changes:

```
dNᵢ/dt = (stuff flowing IN to level i) - (stuff flowing OUT of level i)
```

This gives us a system of **coupled ordinary differential equations (ODEs)**.

#### Example: Simplified 3-Level Tm³⁺ System

For a minimal model with ground (0), intermediate (1), and emitting (3) levels:

```
dN₀/dt = -σ_GSA·Φ·N₀ + A₁₀·N₁ + A₃₀·N₃ + W_CR·N₃·N₀

dN₁/dt = -σ_ESA·Φ·N₁ + A₃₁·N₃ + W_NR·N₃ + 2·W_CR·N₃·N₀

dN₃/dt = +σ_GSA·Φ·N₀ + σ_ESA·Φ·N₁ - A₃₀·N₃ - A₃₁·N₃ - W_NR·N₃ - W_CR·N₃·N₀
```

Let me explain each term:

| Term | Meaning | Units |
|------|---------|-------|
| **σ_GSA·Φ·N₀** | GSA rate: cross-section × photon flux × ground population | ions/(cm³·s) |
| **σ_ESA·Φ·N₁** | ESA rate: cross-section × photon flux × intermediate population | ions/(cm³·s) |
| **A₃₀·N₃** | Radiative decay from level 3 to 0 (Einstein A coefficient) | ions/(cm³·s) |
| **W_NR·N₃** | Non-radiative decay (multiphonon relaxation) | ions/(cm³·s) |
| **W_CR·N₃·N₀** | Cross-relaxation rate (proportional to BOTH populations) | ions/(cm³·s) |

**Key insight**: The CR term has **N₃·N₀** (a product of two populations), making the equations **nonlinear**. This is the mathematical source of the avalanche behavior.

**Note the factor of 2** in the CR term for dN₁/dt: one CR event creates TWO ions in level 1 (one from level 3 going down, one from level 0 going up).

### 3.3 Parameters and Their Physical Meaning

| Parameter | Symbol | Typical Value | Physical Meaning |
|-----------|--------|---------------|------------------|
| GSA cross-section | σ_GSA | 10⁻²² cm² | How "big" an ion looks to a photon for ground state absorption |
| ESA cross-section | σ_ESA | 10⁻²⁰ cm² | Same, but for excited state absorption (100× larger!) |
| Photon flux | Φ | 10²² photons/(cm²·s) | Number of photons hitting unit area per second |
| Radiative rate | A | 100-1000 s⁻¹ | Probability per second of spontaneous photon emission |
| Non-radiative rate | W_NR | 10³-10⁵ s⁻¹ | Probability per second of heat dissipation |
| CR rate coefficient | W_CR | 10⁻¹⁶ cm³/s | Probability per second per ion pair of cross-relaxation |

### 3.4 Why These Equations Are "Stiff"

The equations are called **stiff** because the processes occur on vastly different timescales:

- **Absorption**: femtoseconds (10⁻¹⁵ s)
- **Non-radiative relaxation**: microseconds (10⁻⁶ s)
- **Radiative decay**: milliseconds (10⁻³ s)
- **Avalanche buildup**: tens of milliseconds (10⁻² s)

This 13-order-of-magnitude span causes problems for standard numerical solvers. A naive approach would need incredibly tiny time steps to capture the fast processes, even when we only care about the slow dynamics.

**Solution**: Use **implicit ODE solvers** (like Radau or BDF methods) that are designed for stiff systems. These are mathematically more complex but computationally efficient for this problem.

---

## 4. How the Simulation Works

### 4.1 Software Architecture

PA-Sim is organized to mirror the physics:

```
Material
  └── contains one or more LanthanideIon objects
        └── each has EnergyLevel objects
              └── connected by Transition objects
```

This makes the code intuitive for physicists: you build a material the same way you'd describe it in a paper.

### 4.2 Simulation Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    SIMULATION PIPELINE                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. DEFINE MATERIAL                                          │
│     └── Energy levels, transitions, concentrations           │
│                           ↓                                  │
│  2. BUILD RATE EQUATIONS                                     │
│     └── Automatically construct dN/dt for each level         │
│                           ↓                                  │
│  3. SET INITIAL CONDITIONS                                   │
│     └── All ions in ground state: N₀ = N_total, others = 0   │
│                           ↓                                  │
│  4. SPECIFY PUMP LASER                                       │
│     └── Wavelength, power density → photon flux              │
│                           ↓                                  │
│  5. SOLVE ODEs                                               │
│     └── scipy.integrate.solve_ivp with Radau/BDF method      │
│                           ↓                                  │
│  6. ANALYZE RESULTS                                          │
│     └── Extract threshold, nonlinearity, rise time           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 Key Outputs

After running a simulation, you get:

1. **Time series of populations**: N₀(t), N₁(t), N₂(t), N₃(t)
2. **Emission intensity**: Proportional to A × N₃(t) for the emitting level
3. **Steady-state values**: Where the system settles after the avalanche

By running simulations at different power densities, you can extract:

- **Threshold power**: Where PA "turns on"
- **Nonlinearity order (S)**: The exponent in I_emission ∝ P^S
- **Rise time**: How long it takes to reach steady state

### 4.4 Code Example (Conceptual)

```python
# 1. Define material
material = Material(name="8% Tm:NaYF4", host="NaYF4")
tm = LanthanideIon("Tm3+", concentration=1.2e21)  # ions/cm³
tm.add_level("3H6", energy=0)      # Ground
tm.add_level("3F4", energy=5600)   # Intermediate
tm.add_level("3H4", energy=12600)  # Emitting

# 2. Add transitions
tm.add_transition(0→3, type=GSA, cross_section=1e-22)
tm.add_transition(1→3, type=ESA, cross_section=5e-21)
tm.add_transition(3→0, type=RADIATIVE, rate=500)
tm.add_transition(3→1, type=CR, rate=5e-16, partner=0→1)

# 3. Run simulation
sim = Simulation(material, laser_power=50_000)  # W/cm²
result = sim.run(t_end=0.1)  # 100 ms

# 4. Analyze
print(f"Steady-state emission: {result.emission[-1]}")
```

---

## 5. Key Assumptions and Limitations

### 5.1 Assumptions Made

| Assumption | Why It's Made | When It Might Fail |
|------------|---------------|-------------------|
| **Homogeneous ion distribution** | Simplifies math; ions treated as uniformly distributed | At very high doping (>10%), ions cluster |
| **Average rate equations** | Ignores spatial correlations between specific ion pairs | For very small nanoparticles (<10 nm) |
| **Constant temperature** | Ignores laser heating | At very high powers, heating can be significant |
| **Single ion species** | Models one type of lanthanide at a time | Co-doped systems (Yb/Tm) need extension |
| **No photon reabsorption** | Emitted photons escape immediately | In large/dense samples, emitted light can be reabsorbed |
| **Instantaneous energy transfer** | CR happens instantly when ions are close | Generally valid for ns-scale processes |

### 5.2 What This Model CANNOT Do

1. **Predict exact parameter values**: The model requires experimental input for cross-sections, rates, etc. It cannot derive these from first principles.

2. **Handle spatial inhomogeneity**: Core-shell structures, surface effects, and concentration gradients require extended models.

3. **Simulate single particles**: This is a mean-field model for ensemble behavior, not stochastic single-molecule dynamics.

4. **Account for photobleaching**: Long-term degradation of the material is not modeled.

### 5.3 Parameter Uncertainty

**This is the biggest practical limitation.** The rate parameters (especially W_CR) are:
- Difficult to measure directly
- Highly dependent on synthesis conditions
- Variable between labs

PA-Sim addresses this by:
- Providing a framework for users to input their own validated parameters
- Including literature-based estimates with explicit uncertainty notes
- Enabling parameter sensitivity studies

---

## 6. Validation and Scientific Defensibility

### 6.1 Why This Tool Is Needed

The need for PA-Sim is documented in peer-reviewed literature:

> *"The methodology of PA measurements and characterization are not sufficiently standardized, and cross-lab verifications in the near future must be performed to understand the origin of these discrepancies."*
> — Szalkowski et al., Chemical Society Reviews (2025)

This paper was co-authored by the leading groups in the field (Schuck at Columbia, Chan at Berkeley Lab, Bednarkiewicz in Poland, Skripka at Oregon State).

### 6.2 Existing Alternatives and Their Limitations

| Tool | Source | Limitation |
|------|--------|------------|
| Schuck lab DRE code | GitHub (2020) | 2 stars, no documentation, system-specific |
| LuNASI PA Analysis | GitHub (2022) | Analysis only—doesn't simulate, just processes experimental data |
| SIMETUC | GitHub (2017) | Dormant since 2018, doesn't support PA specifically |
| Custom MATLAB code | Various papers | Not shared, different for each publication |

### 6.3 Validation Strategy

PA-Sim will be validated against:

1. **Lee et al., Nature (2021)**: The foundational PA nanoparticle paper
   - Power dependence curve
   - Nonlinearity order (S ≈ 26)
   - Rise time behavior

2. **Bednarkiewicz et al. (2019)**: Theoretical predictions for PASSI imaging
   - Threshold predictions
   - Resolution enhancement calculations

3. **Cross-lab reproducibility**: Running the same simulation with different groups' reported parameters should explain observed discrepancies.

### 6.4 What "Validation" Means Here

We are **not** claiming to predict experimental results from first principles. We are claiming that:

1. Given the same input parameters, our simulation produces the same output as other implementations
2. The extracted PA parameters (threshold, S, rise time) match literature reports when using literature parameters
3. The mathematical model correctly implements the published rate equations

---

## 7. Glossary

| Term | Definition |
|------|------------|
| **Avalanching** | A chain-reaction process where one event triggers multiple subsequent events |
| **Cross-relaxation (CR)** | Energy transfer between two ions where one goes down and one goes up in energy |
| **Cross-section (σ)** | Effective "target area" of an atom for absorbing light; larger = more likely to absorb |
| **Dopant** | An impurity atom intentionally added to a crystal to modify its properties |
| **ESA** | Excited State Absorption; absorption of light by an already-excited atom |
| **GSA** | Ground State Absorption; absorption of light by an atom in its lowest energy state |
| **Lanthanide** | Elements 57-71 in the periodic table (La through Lu); have unique optical properties |
| **Nanoparticle** | A particle with dimensions in the 1-100 nanometer range |
| **Nonlinearity order (S)** | The exponent in the relationship I_out ∝ I_in^S |
| **ODE** | Ordinary Differential Equation; equation involving derivatives with respect to one variable |
| **Photon flux (Φ)** | Number of photons passing through unit area per unit time |
| **Population (N)** | Number density of ions in a particular energy state |
| **Radiative decay** | De-excitation of an atom by emitting a photon |
| **Rate equation** | An ODE describing how the population of an energy level changes over time |
| **Rise time** | Time for emission to reach steady state after turning on the laser |
| **Stiff equations** | ODEs with processes on very different timescales, requiring special numerical methods |
| **Threshold** | The pump intensity above which photon avalanching occurs |
| **Upconversion** | Process where low-energy photons are converted to higher-energy photons |
| **Wavenumber (cm⁻¹)** | Unit of energy equal to the reciprocal of wavelength; 1 cm⁻¹ ≈ 1.24×10⁻⁴ eV |

---

## References

1. Lee, C., et al. (2021). Giant nonlinear optical responses from photon-avalanching nanoparticles. *Nature*, 589, 230–235.

2. Skripka, A., & Chan, E. M. (2025). Unraveling the myths and mysteries of photon avalanching nanoparticles. *Materials Horizons*, 12, 3575-3597.

3. Szalkowski, M., et al. (2025). Advances in the photon avalanche luminescence of inorganic lanthanide-doped nanomaterials. *Chemical Society Reviews*.

4. Bednarkiewicz, A., et al. (2019). Photon avalanche in lanthanide doped nanoparticles for biomedical applications: super-resolution imaging. *Nanoscale Horizons*, 4, 881–889.

---

*Document version: 1.0*
*Last updated: January 2026*
