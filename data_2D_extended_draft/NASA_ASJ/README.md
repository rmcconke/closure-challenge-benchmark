# NASA ASJ — Axisymmetric Subsonic Jet

Validation case from the **NASA TMR Collaborative Testing Challenge 2022** ([turb-prs2022](https://tmbwg.github.io/turbmodels/turb-prs2022.html)). Acoustic reference Mach M_jet ≈ 0.5.

## Required metrics
1. **u/U_jet vs. x/D_jet** — centerline velocity decay
2. **u/U_jet vs. y/D_jet at 5 specified stations** — radial velocity profiles
3. **u'v'/U_jet² vs. y/D_jet at 5 specified stations** — Reynolds-stress profiles

Compare with the Bridges & Wernet ARN (Acoustic Reference Nozzle) consensus PIV dataset.

## Folder layout
```
NASA_ASJ/
├── 0/                    OpenFOAM initial conditions (T, U, alphat, k, nut, omega, p)
├── 0.25/                 Converged + time-averaged solution (U, UMean, k, kMean, omega, omegaMean, p, pMean, T, gradU, wallShearStress, …)
├── constant/             turbulenceProperties (kOmegaSST), thermophysicalProperties, polyMesh
├── system/               controlDict (rhoPimpleFoam, endTime=0.25), fvSchemes, fvSolution, singleGraph_*, residuals, fieldAverage
├── postProcessing/       singleGraph_x{0,2,5,10,15,20}Dj, singleGraph_y0, residuals, probes
├── convergencePlots/     Ux/Uy/k/omega/p convergence + centerline + x/D plots (PDFs)
├── run.sh                ./run.sh         → rhoPimpleFoam → probeConvergence.py → linePlotterMean.py → comparisonPlotterMean.py
├── postProcess.sh
├── clean.sh
├── foam.foam
├── getFinalJetResults.py     Reads postProcessing/ and writes baseline_komegasst/ASJ_*.dat
├── readExpData.py
├── linePlotterMean.py        ParaView-based line extraction of Mean fields
├── comparisonPlotterMean.py  Comparison plots vs Bridges & Wernet experiment
├── probeConvergence.py
├── log.run                   OpenFOAM run log (~10MB)
├── baseline_komegasst/   k-ω SST integral profiles (.dat + .csv)
├── highfidelity/         ARN PIV experiment + NASA WIND SSTV CFD reference
└── plots/                Comparison code + figures
    └── plot_profiles.py  set MODEL_DIR env var to overlay your model
```

## Solver / setup
- **Solver**: `rhoPimpleFoam` (compressible **transient**, with `fieldAverage` to produce mean fields)
- **Turbulence model**: `kOmegaSST` (pure baseline — no augmentation)
- **Time-averaging window**: ~last half of run, captured in `*Mean` fields
- **Mach**: M_jet = 0.5
- **Why transient**: the jet shear layer is convectively unstable; a steady SIMPLE iteration does not converge cleanly. The official NASA TMR baseline (this case) uses time-stepping with field averaging — `UMean`, `kMean`, etc. are the equivalent of a converged steady RANS solution.

## Submission format
Provide three zone-format .dat files (or .csv equivalents) in `MODEL_DIR`:
- `ASJ_u_vs_x.dat`         — columns: `x/Dj`, `u/Uj` (one zone, centerline)
- `ASJ_u_at5stations.dat`  — columns: `u/Uj`, `y/Dj` (one zone per station: x/Dj=2, 5, 10, 15, 20)
- `ASJ_uv_at5stations.dat` — columns: `u'v'/Uj^2`, `y/Dj` (same zone structure)

## Provenance
Copied from `OLD_SETUPS/02_ASJ/00Baseline/CFDDomain/compressibleTransient/`. The `getFinalJetResults.py` in that folder writes to `epsilonModel/baselineResults/ASJ_*.dat` — this is the case that produced the NASA challenge baseline integral profiles in `baseline_komegasst/`.
