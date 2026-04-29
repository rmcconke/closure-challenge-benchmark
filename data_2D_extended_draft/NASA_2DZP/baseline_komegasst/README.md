# 2DZP — k-ω SST baseline

OpenFOAM `kOmegaSST` RANS run on the finest 545×385 grid (Re_L = 5×10⁶, L = 2).

Source: original Dwight 2022 NASA TMR Collaborative Testing Challenge submission, baseline run (no ML correction).

## Files
| File | Description | Columns |
|------|-------------|---------|
| `2DZP_cf.dat` / `.csv`   | Skin-friction along plate | `x`, `Cf` |
| `2DZP_u+y+.dat` / `.csv` | Inner-scaled BL profile at x = 0.97 | `log(y+)`, `u+` |

Tecplot zone format `.dat` files are the canonical NASA TMR submission format. The `.csv` versions are flat tables with a `zone` column for ML-pipeline convenience.
