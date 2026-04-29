# ASJ — High-fidelity reference

## Files
| File | Description | Source |
|------|-------------|--------|
| `ARN-jet-lines-expt.dat` / `.csv`    | Consensus PIV dataset (Acoustic Reference Nozzle), M_jet ≈ 0.5. Centerline + radial profiles at the 5 specified stations | Bridges & Wernet, NASA — see [NASA TMR ASJ](https://turbmodels.larc.nasa.gov/jetsubsonic_val.html). Variables: `x/Dj`, `y/Dj`, `u/Uj`, `v/Uj`, `u'v'/Uj^2`, `k/Uj^2` (k not meaningful for x/Dj > 22.2) |
| `jetsubsonic_wind_sstv.dat` / `.csv` | NASA WIND SST-V CFD reference run on a P3D grid for cross-checking | NASA TMR / WIND-US |

`.dat` files are NASA Tecplot zone format. `.csv` versions are flat tables with a `zone` column.
