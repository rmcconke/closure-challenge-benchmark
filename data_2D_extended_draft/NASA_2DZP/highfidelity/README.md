# 2DZP — High-fidelity reference

Theoretical/empirical references for the ZPG flat plate. Sourced from the [NASA Turbulence Modeling Resource](https://turbmodels.larc.nasa.gov/flatplate_val.html).

## Files
| File | Description | Source |
|------|-------------|--------|
| `cf_as_function_of_x.dat` | Theoretical Cf(x) at Re_L = 5×10⁶ with 5% error band; multiple zones for different correlations | White, *Viscous Fluid Flow*, McGraw-Hill, New York, 1974 (Cf as fn of Re_x) |
| `u+y+.dat`                | u⁺ vs y⁺ at Re_θ = 10000 (Coles velocity law w/ van Driest damping) | Bardina et al., NASA TM 110446, April 1997 |
| `u+y+theory_many.dat`     | Multiple wall-law theories (Spalding κ=0.41, B=5.0; etc.) for context | NASA TMR |

Each `.dat` is in NASA Tecplot zone format. `.csv` versions are flat tables with a `zone` column.
