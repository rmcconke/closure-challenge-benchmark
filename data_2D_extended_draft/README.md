# Extended 2D cases — draft staging

Three additional 2D cases from the **NASA TMR Collaborative Testing Challenge 2022**
([turb-prs2022](https://tmbwg.github.io/turbmodels/turb-prs2022.html)) staged here for
review. Final layout (folder names, evaluation-point grids, integration with the
existing `data/` leaderboard) is **TBD by Ryley** — these files are dropped in as
provided so they can be reorganised without re-extracting from the source dataset.

## Cases

| Folder | Case | Suggested metrics |
|--------|------|-------------------|
| `NASA_2DZP/`  | 2D Zero-Pressure-Gradient flat plate    | Cf(x); u⁺(log y⁺) at x = 0.97, vs theory |
| `NASA_ASJ/`   | Axisymmetric Subsonic Jet (M_jet ≈ 0.5) | u/Uj along axis; u/Uj and u'v'/Uj² at 5 stations, vs Bridges & Wernet PIV |
| `NASA_2DN00/` | NACA 0012 airfoil, α = 10 / 15 / 17 / 18° | C_L(α), C_D vs C_L, C_p(x/c), C_f(x/c upper), vs Ladson + Gregory |

## Per-case layout (as staged)

```
NASA_<CASE>/
├── README.md                  Case description, refs, submission format
├── baseline_komegasst/        k-ω SST RANS baseline (.dat NASA Tecplot + .csv flat)
├── highfidelity/              Theory / experiment / CFD-cross-check references
├── plots/
│   ├── plot_profiles.py       Set MODEL_DIR env var to overlay your model
│   └── *.pdf                  Pre-rendered baseline-vs-experiment plots
├── system/                    OpenFOAM control dicts (small, kept for re-runs)
├── *.sh                       Run / clean / postProcess scripts
└── *.py                       Result-extraction helpers
```

**Excluded from this staging** (kept on the SURF drive — the full case folders live
in `ML4Fluids_2D_Dataset/Extended_2D_Dataset/<CASE>/` upstream):

- OpenFOAM time directories (`10000/`, `0.25/`, `10deg/`, `15deg/`, `17deg/`, `18deg/`).
- `constant/polyMesh/` (mesh files).
- `postProcessing/` raw probe dumps.
- `foam.foam` and `*.log` files.

If a metric needs the full converged field rather than the curated CSVs in
`highfidelity/` / `baseline_komegasst/`, pull the corresponding case from SURF or from
the upstream `Extended_2D_Dataset/` source.
