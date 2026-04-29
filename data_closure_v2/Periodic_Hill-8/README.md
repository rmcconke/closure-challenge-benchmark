# Periodic Hill Metrics

This directory contains the Periodic Hill cases used for the 2D challenge
requirements:

- Velocity profiles
- Reynolds shear stress profiles
- Skin-friction coefficient, `Cf`, on both bottom and upper walls

Two Reynolds-number cases are included:

- `Re_5600`
- `Re_10595`

Both cases compare:

- `00Baseline`: RANS(SST) OpenFOAM result using `RITAkOmegaSST`
- `RefData`: LES reference data from `Hill_Breuer.csv`

The case setup was prepared and run with OpenFOAM 8.

## Directory Layout

```text
Periodic_Hill-8/
├── Re_5600/
│   ├── 00Baseline/
│   ├── 01Frozen/
│   ├── RefData/
│   ├── Figures/
│   └── comparison_PeriodicHill.py
├── Re_10595/
│   ├── 00Baseline/
│   ├── 01Frozen/
│   ├── RefData/
│   ├── Figures/
│   └── comparison_PeriodicHill.py
├── common/
└── Info/
```

`01Frozen` is not used by the current required metric export. The exported
metrics compare only `00Baseline` and LES.

## Generate The Required Metrics

From either Reynolds-number case directory, run:

```bash
python3 comparison_PeriodicHill.py
```

For example:

```bash
cd Periodic_Hill-8/Re_5600
python3 comparison_PeriodicHill.py
```

or:

```bash
cd Periodic_Hill-8/Re_10595
python3 comparison_PeriodicHill.py
```

Use a Python environment with `numpy` and `matplotlib` available.

## Inputs Used

The SST/RANS data are read from:

```text
00Baseline/postProcessing/singleGraph_x*/
00Baseline/postProcessing/wallProfiles/
```

The LES data are read from the local case reference file:

```text
RefData/Hill_Breuer.csv
```

So `Re_5600/comparison_PeriodicHill.py` uses `Re_5600/RefData/Hill_Breuer.csv`,
and `Re_10595/comparison_PeriodicHill.py` uses
`Re_10595/RefData/Hill_Breuer.csv`.

## Generated Figures

Each case writes these PDF figures into its local `Figures/` directory.

For `Re_5600`:

```text
Figures/compareUxProfiles_PeriodicHill_Re5600.pdf
Figures/compareuvProfiles_PeriodicHill_Re5600.pdf
Figures/compareCf_bottomWall_PeriodicHill_Re5600.pdf
Figures/compareCf_topWall_PeriodicHill_Re5600.pdf
Figures/compareCp_bottomWall_PeriodicHill_Re5600.pdf
Figures/compareCp_topWall_PeriodicHill_Re5600.pdf
```

For `Re_10595`:

```text
Figures/compareUxProfiles_PeriodicHill_Re10595.pdf
Figures/compareuvProfiles_PeriodicHill_Re10595.pdf
Figures/compareCf_bottomWall_PeriodicHill_Re10595.pdf
Figures/compareCf_topWall_PeriodicHill_Re10595.pdf
Figures/compareCp_bottomWall_PeriodicHill_Re10595.pdf
Figures/compareCp_topWall_PeriodicHill_Re10595.pdf
```

The challenge-required wall-friction plots are the `compareCf_*` files. The
`Cp` plots are also generated as extra diagnostics.

## Generated CSV Metrics

Each case writes tab-delimited CSV files.

For `Re_5600`:

```text
Figures/wall_Cp_Cf_PeriodicHill_Re5600.csv
Figures/velocity_shear_profiles_PeriodicHill_Re5600.csv
```

For `Re_10595`:

```text
Figures/wall_Cp_Cf_PeriodicHill_Re10595.csv
Figures/velocity_shear_profiles_PeriodicHill_Re10595.csv
```

The wall CSV contains:

```text
wall
x_over_h
Cp_RANS_SST
Cp_LES
Cf_RANS_SST
Cf_LES
```

The profile CSV contains:

```text
station_x_over_h
y_over_h
Ux_over_Uref_RANS_SST
Ux_over_Uref_LES
uv_over_Uref2_RANS_SST
uv_over_Uref2_LES
```

Rows where the LES value is unavailable are dropped, so the CSV files do not
contain `nan` entries.

## Reference Values

Both comparison scripts currently use:

```text
Uref = 1.0
Pref = 1.0
```

The viscosity differs by Reynolds-number case:

```text
Re_5600:  nu = 1.785714285714286e-4
Re_10595: nu = 9.438414346389807e-5
```

## Metric Definitions

### Velocity Profiles

The velocity profile metric is:

```text
Ux / Uref
```

The plots show shifted profiles:

```text
Ux/Uref + x/h
```

The CSV files store the unshifted normalized values.

### Reynolds Shear Stress Profiles

The shear stress profile metric is:

```text
uv / Uref^2
```

For SST/RANS, the modeled Reynolds shear stress is calculated from the sampled
eddy viscosity and velocity gradient:

```text
uv = -nut (dUx/dy + dUy/dx)
```

The required sampled fields are:

```text
nut
dUx/dy
dUy/dx
```

For LES, `uv` is read directly from `RefData/Hill_Breuer.csv`.

The plots show shifted profiles:

```text
20 uv/Uref^2 + x/h
```

The CSV files store the unshifted normalized values.

### Skin-Friction Coefficient

For SST/RANS, `Cf` is calculated from the wall-tangential component of OpenFOAM
`wallShearStress`:

```text
Cf = -(tau_w . t) / (0.5 Uref^2)
```

where `t` is the local wall tangent vector.

For LES, `Cf` is calculated from the first off-wall LES velocity gradient:

```text
U_t = u t_x + v t_y
dU_t/dn ≈ U_t(first interior point) / dn
Cf = nu (dU_t/dn) / (0.5 Uref^2)
```

This is evaluated separately for the bottom wall and upper wall.

### Pressure Coefficient

`Cp` is not part of the required Periodic Hill metric list, but it is exported
and plotted as an additional diagnostic:

```text
Cp = (p - Pref) / (0.5 Uref^2)
```

For LES, the pressure field `pm` from `Hill_Breuer.csv` is used.

## Regeneration Checklist

1. Source the intended OpenFOAM 8 environment.
2. Run or post-process the relevant `00Baseline` case so `singleGraph_x*` and
   `wallProfiles` are available.
3. Confirm profile outputs include `nut` and `gradU`.
4. Run `python3 comparison_PeriodicHill.py` from `Re_5600/` or `Re_10595/`.
5. Use the PDFs for visual checks and the tab-delimited CSVs for metric export.
