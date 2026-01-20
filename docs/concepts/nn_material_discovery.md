# Neural Network for PA Host Discovery

## The Idea

Train a model on Materials Project data to predict which materials would make good photon avalanche hosts, without running expensive DFT phonon calculations for every candidate.

## What We Could Predict

### Tier 1: Directly from MP data (feasible now)

| Target Property | Training Data Available | Relevance to PA |
|-----------------|------------------------|-----------------|
| Phonon cutoff (ℏω_max) | ~5000 materials with phonon DOS | Determines MPR rates |
| Band gap | ~150,000 materials | Optical transparency |
| Formation energy | Most materials | Stability |
| Bulk modulus | ~13,000 materials | Mechanical handling |

### Tier 2: Derived properties (needs feature engineering)

| Target Property | How to Derive | Relevance to PA |
|-----------------|---------------|-----------------|
| Hygroscopicity | Composition features (halide type) | Practical handling |
| Ln³⁺ site symmetry | Space group + Wyckoff positions | Crystal field splitting |
| Predicted MPR rate | ℏω_max + gap law | Direct PA relevance |

### Tier 3: PA-specific (requires separate database)

| Target Property | Source | Challenge |
|-----------------|--------|-----------|
| Ln³⁺ energy levels | Literature, NIST | Host-dependent shifts |
| ESA/GSA cross-sections | Judd-Ofelt from spectra | Very limited data |
| CR rates | Concentration quenching | ~20 systems characterized |

## Proposed Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    PA Host Predictor Pipeline                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  INPUT FEATURES (from composition + structure):                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ • Elemental embeddings (Magpie, mat2vec, MEGNet)         │   │
│  │ • Coordination numbers, bond lengths                      │   │
│  │ • Space group one-hot encoding                           │   │
│  │ • Electronegativity statistics                           │   │
│  │ • Ionic radii statistics                                 │   │
│  │ • Mass-weighted features (for phonon prediction)         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                            │                                     │
│                            ▼                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Neural Network (GNN or MLP)                  │   │
│  │  • Option A: Crystal Graph ConvNet (CGCNN)               │   │
│  │  • Option B: MEGNet                                       │   │
│  │  • Option C: Simple MLP on composition features          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                            │                                     │
│                            ▼                                     │
│  OUTPUT TARGETS:                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ • Phonon cutoff ℏω_max (cm⁻¹)                            │   │
│  │ • Band gap (eV)                                           │   │
│  │ • PA suitability score (0-1)                             │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Training Data

### From Materials Project (~5000 materials with phonon data)

```python
from mp_api.client import MPRester
import pandas as pd

with MPRester(api_key="YOUR_KEY") as mpr:
    # Get all materials with phonon data
    docs = mpr.materials.phonon.search(
        fields=["material_id", "formula_pretty", "structure",
                "last_peak_frequency", "ph_dos"]
    )

    data = []
    for doc in docs:
        # Extract phonon cutoff from DOS
        phonon_cutoff_thz = doc.last_peak_frequency  # THz
        phonon_cutoff_cm_inv = phonon_cutoff_thz * 33.356  # Convert to cm⁻¹

        data.append({
            "material_id": doc.material_id,
            "formula": doc.formula_pretty,
            "structure": doc.structure,
            "phonon_cutoff_cm_inv": phonon_cutoff_cm_inv,
        })

    df = pd.DataFrame(data)
```

### Labeling for PA suitability

Create a binary or continuous label based on known PA hosts:

```python
KNOWN_PA_HOSTS = {
    "NaYF4": 1.0,    # Tm³⁺ PA demonstrated
    "LiYF4": 1.0,    # Er³⁺, Tm³⁺ PA demonstrated
    "KPb2Cl5": 1.0,  # Nd³⁺ PA demonstrated (>200th order)
    "ZBLAN": 0.9,    # Er³⁺ PA in fiber
    "LaF3": 0.7,     # Potential PA host
    "YAG": 0.3,      # High phonon, poor for PA
    "SiO2": 0.1,     # Very high phonon
}

# Label based on phonon cutoff heuristic
def pa_suitability(phonon_cutoff, band_gap):
    """Heuristic PA suitability score."""
    # Ideal: 150-400 cm⁻¹ phonon, >3 eV band gap
    phonon_score = np.exp(-((phonon_cutoff - 300) / 150)**2)
    gap_score = 1.0 if band_gap > 3.0 else band_gap / 3.0
    return phonon_score * gap_score
```

## Model Options

### Option A: CGCNN (Crystal Graph Convolutional Neural Network)

Best for structure-aware predictions. Proven for property prediction.

```python
from matgl.models import M3GNet  # or CGCNN

model = M3GNet(
    element_types=["H", "Li", ..., "Pu"],
    is_intensive=True,
    readout_type="set2set",
)

# Train on phonon cutoff prediction
model.fit(structures, phonon_cutoffs, epochs=500)
```

### Option B: Composition-only MLP (faster, simpler)

Use elemental embeddings without structure:

```python
from matminer.featurizers.composition import ElementProperty

featurizer = ElementProperty.from_preset("magpie")

X = featurizer.featurize_dataframe(df, col_id="formula")
y = df["phonon_cutoff_cm_inv"]

from sklearn.neural_network import MLPRegressor
model = MLPRegressor(hidden_layer_sizes=(256, 128, 64), max_iter=1000)
model.fit(X, y)
```

### Option C: Transfer learning from pre-trained materials models

Use embeddings from models trained on millions of materials:

```python
from matgl.models import MEGNet

# Pre-trained MEGNet embeddings
pretrained = MEGNet.load("MP-2021.2.8-EFS")

# Extract structure embeddings
embeddings = [pretrained.get_embedding(s) for s in structures]

# Train lightweight head for phonon prediction
from sklearn.ensemble import GradientBoostingRegressor
head = GradientBoostingRegressor()
head.fit(embeddings, phonon_cutoffs)
```

## Validation Strategy

1. **Hold out known PA hosts** - Test if model correctly identifies NaYF4, LiYF4, KPb2Cl5 as good candidates
2. **Cross-validation on phonon cutoff** - Measure MAE on held-out materials
3. **Physical sanity checks**:
   - Heavier elements → lower phonon cutoff
   - Halides < Oxides < Nitrides in phonon energy
   - Fluorides should cluster near 300-500 cm⁻¹

## What the NN Could Tell Us

### Screening question: "Find me chlorides with ℏω_max < 250 cm⁻¹"

Without NN: Run DFT phonon calculations on thousands of chlorides (~days/material)
With NN: Predict in milliseconds, then verify top candidates with DFT

### Discovery question: "What compositions might give ultra-low phonon hosts?"

```python
# Generate candidate compositions
from pymatgen.core import Composition
from itertools import product

candidates = []
for A in ["K", "Rb", "Cs"]:
    for B in ["Pb", "Cd", "Sn"]:
        for X in ["Cl", "Br", "I"]:
            for stoich in ["ABX3", "A2BX4", "AB2X5"]:
                candidates.append(make_composition(A, B, X, stoich))

# Predict phonon cutoff for all
predictions = model.predict(candidates)

# Rank by predicted PA suitability
ranked = sorted(zip(candidates, predictions), key=lambda x: x[1])
print("Top candidates for ultra-low phonon PA hosts:")
for comp, pred in ranked[:10]:
    print(f"  {comp}: predicted ℏω_max = {pred:.0f} cm⁻¹")
```

## Limitations

1. **Phonon data is sparse** - Only ~5000 materials in MP have phonon calculations
2. **Dopant effects ignored** - Ln³⁺ dopants perturb local phonon modes
3. **No CR prediction** - Cross-relaxation rates require ion-ion interaction modeling
4. **Extrapolation risk** - NN may fail on compositions far from training data

## Implementation Plan

### Phase 1: Proof of concept (1-2 weeks)
- [ ] Download MP phonon dataset
- [ ] Train simple MLP on composition → phonon cutoff
- [ ] Validate on known PA hosts

### Phase 2: Structure-aware model (2-4 weeks)
- [ ] Implement CGCNN or MEGNet
- [ ] Add band gap as secondary target
- [ ] Cross-validate on held-out materials

### Phase 3: PA suitability predictor (1-2 weeks)
- [ ] Combine phonon + band gap into PA score
- [ ] Screen MP database for new candidates
- [ ] Generate ranked list for experimental validation

### Phase 4: Integration with PA-Sim (ongoing)
- [ ] Auto-suggest host materials for given dopant
- [ ] Estimate MPR rates from predicted phonon cutoff
- [ ] Flag materials for detailed DFT verification

## References

- Xie, T. & Grossman, J.C. "Crystal Graph Convolutional Neural Networks for an Accurate and Interpretable Prediction of Material Properties." Phys. Rev. Lett. 120, 145301 (2018).
- Chen, C. et al. "Graph Networks as a Universal Machine Learning Framework for Molecules and Crystals." Chem. Mater. 31, 3564–3572 (2019).
- Ward, L. et al. "Matminer: An open source toolkit for materials data mining." Comput. Mater. Sci. 152, 60–69 (2018).
