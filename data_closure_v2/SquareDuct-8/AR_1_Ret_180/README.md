# Square Duct AR=1, Ret=180

This case provides the required square-duct metric:

- axial velocity profile along the diagonal
- transverse velocity magnitude along the diagonal

The comparison is between:

- `RANS(SST)`: baseline SST result from `00Baseline/beta11`
- `LES`: interpolated reference/DNS field from `01Frozen/beta11`

OpenFOAM version used: `OpenFOAM 8`

## Run The Comparison

From this directory:

```bash
python comparison_SquareDuct.py
```

The old scripts are now compatibility wrappers:

```bash
python write_profiles.py
python plot_U_dig_baseline_dns.py
```

Both commands call `comparison_SquareDuct.py` and generate the same standardized outputs.

## Inputs

The script reads the latest diagonal profile files from:

- `00Baseline/beta11/postProcessing/singleGraphDiag/<latest>/line_U.xy`
- `01Frozen/beta11/postProcessing/singleGraphDiag/<latest>/line_U_LES.xy`

Each profile file is expected to contain:

```text
x y z Ux Uy Uz
```

The case parameters are read from `caseDef`:

- `h = 0.001`
- `AR = 1`
- `Re_b = 2500`
- `Re_tau = 164.5651`
- `nu = 1.5e-5`

The bulk velocity used for normalization is:

```text
Ub = Re_b * nu / h = 37.5
```

## Outputs

All standardized outputs are written to `Figures/`:

- `Figures/compareUxProfiles_SquareDuct_AR1_ReTau180.pdf`
- `Figures/compareUpProfiles_SquareDuct_AR1_ReTau180.pdf`
- `Figures/velocity_diagonal_profiles_SquareDuct_AR1_ReTau180.csv`

The plot labels follow the same convention used in the other challenge cases:

- `RANS(SST)` for the baseline SST result
- `LES` for the interpolated reference field

## CSV Format

The CSV file is tab-delimited and stores the RANS(SST) and LES quantities side by side.

Main columns:

- `r_over_h`
- `x`, `y`, `z`
- `Ux_RANS_SST`, `Uy_RANS_SST`, `Uz_RANS_SST`, `Up_RANS_SST`
- `Ux_LES`, `Uy_LES`, `Uz_LES`, `Up_LES`
- `Ux_over_Ub_RANS_SST`, `Ux_over_Ub_LES`
- `Up_over_Ub_RANS_SST`, `Up_over_Ub_LES`

where:

```text
r/h = sqrt(y^2 + z^2) / h
Up = sqrt(Uy^2 + Uz^2)
```

Rows are written on the RANS(SST) diagonal sampling locations. LES values are interpolated onto those locations in `r/h`, and rows outside the available LES range are dropped.

## Solver Note

`01Frozen/beta11` requires the customized frozen solver to run fully. If that solver is unavailable, the interpolated reference fields and existing diagonal post-processing files can still be used by `comparison_SquareDuct.py`.
