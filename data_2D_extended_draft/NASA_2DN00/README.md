# NASA 2DN00 — NACA 0012 Airfoil

Validation case from the **NASA TMR Collaborative Testing Challenge 2022** ([turb-prs2022](https://tmbwg.github.io/turbmodels/turb-prs2022.html)).

Four AoA: **α = 10°, 15°, 17°, 18°** (canonical challenge spec).

## Required metrics
1. **CL vs. α**
2. **CD vs. CL**
3. **Cp vs. x/c** at each AoA — compare with experiment
4. **Cf vs. x/c (upper surface)** at each AoA — no experiment available

## Folder layout
```
NASA_2DN00/
├── 10deg/                Per-AoA OpenFOAM case
│   ├── 0/                  initial conditions (T, U, alphat, k, nut, omega, p)
│   ├── constant/
│   │   ├── polyMesh/         449 × 129 grid (NASA TMR third-finest)
│   │   ├── thermophysicalProperties
│   │   └── turbulenceProperties (RASModel kOmegaSST)
│   ├── system/             controlDict (rhoSimpleFoam, endTime=10000), fvSchemes, fvSolution, decomposeParDict, residuals, yPlus, wallShearStress, probes, writeCellCentres
│   ├── run.sh              decomposePar → mpirun -np 8 rhoSimpleFoam -parallel → reconstructPar
│   └── clean.sh
├── 15deg/                  (same structure)
├── 17deg/                  (same structure)
├── 18deg/                  (same structure)
├── baseline_komegasst/     k-ω SST integral profiles (.dat + .csv) — output of getFinalAirfoilResults.py once cases are run
├── highfidelity/           Ladson + Gregory experiments + CFL3D SST cross-check
└── plots/                  Comparison code + figures
    └── plot_profiles.py    set MODEL_DIR env var to overlay your model
```

## Status

The 4 AoA case dirs ship with **initial conditions only** (no converged time directory yet). To produce the converged baseline:

```bash
cd 10deg && ./run.sh   # uses 8 MPI ranks; ~10–30 min per AoA
# (repeat for 15deg / 17deg / 18deg)
```

After all 4 are converged, rerun `getFinalAirfoilResults.py` (sourced from the original NASA challenge submission) to produce/update the .dat files in `baseline_komegasst/`.

The integral .dat / .csv files currently shipped in `baseline_komegasst/` were copied from the original NASA challenge submission (`OLD_NASA_CHALLENGE_SUBMISSION/finalModel/baselineResults/`) — they are pure k-ω SST baseline numbers from a previous run of these same cases.

## Solver / setup
- **Solver**: `rhoSimpleFoam` (compressible steady)
- **Turbulence model**: `kOmegaSST` (pure baseline — no augmentation)
- **Grid**: 449 × 129, NASA TMR third-finest
- **Re**: 6×10⁶ (Ladson) / 2.88×10⁶ (Gregory)
- **Mach**: 0.15

## Submission format
Three zone-format .dat files (or .csv equivalents):
- `2DN00_cl_cd.dat`         — columns: `alpha, deg`, `cl`, `cd` (one zone, four rows)
- `2DN00_cp_at4alphas.dat`  — columns: `x/c`, `cp`. One zone per AoA: `alpha=10 deg`, `alpha=15 deg`, `alpha=17 deg`, `alpha=18 deg`
- `2DN00_cf_at4alphas.dat`  — columns: `x/c`, `cf`. Same zone structure as Cp

## Provenance
Per-AoA case directories copied from `OLD_SETUPS/04_2DN00/00Baseline/rhoSimpleFoam_Final/Case2/{10,15,17,18}_deg/`, with the `polyMesh` symlink (originally pointing to `Grids/polyMesh2/`) materialized into each case for self-containment.
