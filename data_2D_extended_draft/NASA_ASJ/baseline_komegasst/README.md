# ASJ — k-ω SST baseline

OpenFOAM `kOmegaSST` (compressible) RANS run on the second-finest grid (2×97×97 / 2×61×97 / 2×257×225 zones).

Source: original Dwight 2022 NASA TMR Collaborative Testing Challenge submission, baseline run (no ML correction).

## Files
| File | Description | Columns |
|------|-------------|---------|
| `ASJ_u_vs_x.dat` / `.csv`         | Centerline axial velocity decay | `x/Dj`, `u/Uj` |
| `ASJ_u_at5stations.dat` / `.csv`  | Radial velocity profiles at 5 stations | `u/Uj`, `y/Dj` (one zone per station) |
| `ASJ_uv_at5stations.dat` / `.csv` | Radial Reynolds-shear-stress profiles at the same 5 stations | `u'v'/Uj^2`, `y/Dj` (one zone per station) |

The 5 stations are the same as in the ARN PIV reference dataset (`x/Dj=2`, `5`, `10`, `15`, `20`).
