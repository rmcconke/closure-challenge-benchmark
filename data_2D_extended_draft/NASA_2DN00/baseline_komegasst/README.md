# 2DN00 — k-ω SST baseline

OpenFOAM `kOmegaSST` (compressible) RANS run on the third-finest 449×129 grid.

Source: original Dwight 2022 NASA TMR Collaborative Testing Challenge submission, baseline run (no ML correction). Run at the four canonical AoAs.

## Files
| File | Description | Columns | AoA zones |
|------|-------------|---------|-----------|
| `2DN00_cl_cd.dat` / `.csv`        | Polar | `alpha, deg`, `cl`, `cd` | one zone, 4 rows |
| `2DN00_cp_at4alphas.dat` / `.csv` | Surface pressure | `x/c`, `cp`  | 10° / 15° / 17° / 18° |
| `2DN00_cf_at4alphas.dat` / `.csv` | Surface skin friction (upper) | `x/c`, `cf` | 10° / 15° / 17° / 18° |
