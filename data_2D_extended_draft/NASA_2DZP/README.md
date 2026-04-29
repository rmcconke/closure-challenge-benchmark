# NASA 2DZP — 2D Zero-Pressure-Gradient Flat Plate

Validation case from the **NASA TMR Collaborative Testing Challenge 2022** ([turb-prs2022](https://tmbwg.github.io/turbmodels/turb-prs2022.html)).

## Required metrics
1. **Cf vs. x** — skin-friction along plate
2. **u⁺ vs. log₁₀(y⁺)** at x = 0.97 — boundary-layer profile compared with theory

## Folder layout
```
NASA_2DZP/
├── 0/                    OpenFOAM initial conditions (T, U, alphat, k, nut, omega, p)
├── 10000/                OpenFOAM converged solution (+ C/Cx/Cy/Cz/gradU/gradk/gradp/wallShearStress/yPlus)
├── constant/             turbulenceProperties (kOmegaSST), thermophysicalProperties, polyMesh (545×385)
├── system/               controlDict (rhoSimpleFoam, endTime=10000), fvSchemes, fvSolution, singleGraph_x0.97, singleGraph_y0
├── postProcessing/       residuals, singleGraph_x0.97, singleGraph_y0, wallShearStress, yPlus, probes
├── orig.0/               pristine 0/ for clean re-runs
├── run.sh                ./run.sh                  → runs rhoSimpleFoam serial then ./postProcess.sh
├── postProcess.sh
├── clean.sh
├── foam.foam
├── getFinalPlateResults.py    Reads postProcessing/ and writes baseline_komegasst/2DZP_*.dat (Tecplot zone format)
├── readExpData.py             NASA Tecplot zone parser
├── log.run                    OpenFOAM run log
├── baseline_komegasst/   k-ω SST RANS integral profiles (.dat + .csv) — outputs of getFinalPlateResults.py
├── highfidelity/         Theory / experimental references (.dat + .csv)
└── plots/                Comparison code + figures
    └── plot_profiles.py  set MODEL_DIR env var to overlay your model
```

## Solver / setup
- **Solver**: `rhoSimpleFoam` (compressible steady)
- **Turbulence model**: `kOmegaSST` (pure baseline — no augmentation)
- **Grid**: 545 × 385, finest of NASA TMR sequence
- **Re_L**: 5×10⁶ (L = 2)
- **Inflow**: M = 0.2

## Submission format
Provide two zone-format .dat files (or .csv equivalents) in a directory; point `MODEL_DIR` at it:
- `2DZP_cf.dat`   — columns: `x`, `Cf`
- `2DZP_u+y+.dat` — columns: `log(y+)`, `u+`

Then `python plots/plot_profiles.py` overlays baseline + experiment + your model.

## Provenance
Copied from `OLD_SETUPS/00_2DZP/00Baseline/simpleFoam/` (note: the directory was named `simpleFoam/` historically, but the solver is `rhoSimpleFoam` per `system/controlDict`).
