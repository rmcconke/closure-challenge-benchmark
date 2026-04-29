# NASA Hump Metrics

This case generates the required NASA hump challenge metrics:

- Velocity profiles
- Reynolds shear stress profiles
- Wall pressure coefficient, `Cp`
- Wall skin-friction coefficient, `Cf`

The case setup here was prepared and run with OpenFOAM 8.

The submitted comparison is between:

- `00Baseline`: RANS(SST) OpenFOAM result using `RITAkOmegaSST`
- `RefData`: LES reference data

`01Frozen` is a separate frozen/interpolated-LES setup and is not included in
the exported comparison metrics unless `comparison_NASA.py` is edited to add it.

## Directory Layout

```text
NASA_Hump-8/
├── 00Baseline/          # OpenFOAM RITAkOmegaSST baseline case
├── 01Frozen/            # Frozen-field case using LES fields on the SST mesh
├── RefData/             # NASA/LES reference data
├── Figures/             # Generated plots and metric CSV files
├── comparison_NASA.py   # Main script for required metric plots and exports
├── readDefFile.py
└── readExpData.py
```

## Note On `01Frozen`

`01Frozen` is not part of the current required SST-vs-LES metric export. It is
a separate frozen-field case designed for interpolated LES fields on the
`00Baseline` SST mesh.

Running `01Frozen/run.sh` requires the custom OpenFOAM 8 solver:

```text
frozenSimpleFoam
```

If that solver is not available, the case may not run, but the interpolated LES
fields are still available in:

```text
01Frozen/0/
```

Important files there include:

```text
U_LES
k_LES
tauij_LES
frozenFields
inletOutletFields
```

## Generate The SST Baseline Data

Run the baseline OpenFOAM case first:

```bash
cd NASA_Hump-8/00Baseline
./run.sh
```

This runs `simpleFoam`, creates the `baselineSolution` symlink to the latest
time directory, and then runs the case post-processing script.

The baseline model is set in:

```text
00Baseline/constant/momentumTransport
```

as:

```text
RASModel        RITAkOmegaSST;
```

This custom SST model/post-processing setup is used so `gradU` is available in
the sampled profile output. The velocity-gradient components are needed for the
SST shear-stress profile calculation.

The post-processing step writes the wall and profile data used by
`comparison_NASA.py`, including:

- `postProcessing/wallValues/`
- `postProcessing/singleGraph_x0.65c/`
- `postProcessing/singleGraph_x0.8c/`
- `postProcessing/singleGraph_x0.9c/`
- `postProcessing/singleGraph_x1.0c/`
- `postProcessing/singleGraph_x1.1c/`
- `postProcessing/singleGraph_x1.2c/`
- `postProcessing/singleGraph_x1.3c/`

## Generate Required Plots And CSV Files

From the case root, run:

```bash
cd NASA_Hump-8
python3 comparison_NASA.py
```

Use a Python environment with `numpy` and `matplotlib` available. The script
also uses the local helper modules `readDefFile.py` and `readExpData.py`.

The LES pickle is read from:

```text
RefData/pickledLESData.pickle
```

If the pickle is missing, `comparison_NASA.py` calls `RefData/readAndPickle.py`
to regenerate it from the raw reference data.

## Generated Figures

The script writes these PDF plots:

```text
Figures/compareCpWall-NASA.pdf
Figures/compareCfWall-NASA.pdf
Figures/compareUxProfiles_NASA.pdf
Figures/comparekProfiles_NASA.pdf
Figures/compareupwpProfiles_NASA.pdf
```

The profile plots use `x/c` and `y/c`. Curves are shifted in the horizontal
direction for readability:

- Velocity: `0.1 Ux/Uref + x/c`
- Turbulent kinetic energy: `k/Uref^2 + x/c`
- Reynolds shear stress: `2 uv/Uref^2 + x/c`

The shift and scaling are only for plotting. The CSV files store the raw
normalized quantities.

## Generated CSV Metrics

The script writes tab-delimited CSV files:

```text
Figures/wall_Cp_Cf_NASA.csv
Figures/velocity_shear_profiles_NASA.csv
```

`wall_Cp_Cf_NASA.csv` contains side-by-side SST and LES wall data:

```text
x_over_c
Cp_RANS_SST
Cp_LES
Cf_RANS_SST
Cf_LES
```

`velocity_shear_profiles_NASA.csv` contains side-by-side SST and LES profile
data:

```text
station_x_over_c
wall_normal_over_c
Ux_over_Uref_RANS_SST
Ux_over_Uref_LES
k_over_Uref2_RANS_SST
k_over_Uref2_LES
uv_over_Uref2_RANS_SST
uv_over_Uref2_LES
```

Rows where the LES value is unavailable are dropped, so the exported CSV files
do not contain `nan` entries.

## Metric Definitions

The reference velocity is computed from `caseDef`:

```text
Uref = Mref sqrt(gamma R Tref)
```

The chord length is `c = 0.42`.

### Wall Pressure Coefficient

For SST:

```text
Cp = p / (0.5 Uref^2)
```

For LES:

```text
Cp = (p/pinf - 1) R Tref / (0.5 Uref^2)
```

### Wall Skin-Friction Coefficient

For SST, `Cf` is computed from the wall-tangential component of the OpenFOAM
wall shear stress:

```text
tau_t = wallShearStressx t_x + wallShearStressz t_z
Cf = -tau_t / (0.5 Uref^2)
```

The minus sign matches the wall-point/tangent orientation used by the VTK wall
face set.

For LES, `Cf` is computed from the wall-normal velocity gradient in local wall
coordinates:

```text
Cf = nu (dU_t/dn) / (0.5 Uref^2)
```

### Velocity Profiles

The velocity profile metric is:

```text
Ux / Uref
```

The CSV stores SST values at the OpenFOAM sampling points. LES values are
interpolated onto those same wall-normal locations.

### Shear Stress Profiles

The shear stress profile is the Reynolds shear stress component:

```text
uv / Uref^2
```

For LES this comes directly from:

```text
uv/Uinf^2
```

For SST/RANS, the modeled turbulent shear stress is reconstructed from eddy
viscosity and the sampled `gradU` field exported by `00Baseline`:

```text
uv = -nut (dUx/dz + dUz/dx)
```

The required sampled fields are:

```text
nut
dUx/dz
dUz/dx
```

These are written by the `00Baseline` `RITAkOmegaSST` setup and read by
`comparison_NASA.py`.

## Regeneration Checklist

1. Source the intended OpenFOAM environment.
2. Run `00Baseline/run.sh`.
3. Run `python3 comparison_NASA.py` from `NASA_Hump-8/`.
4. Use the PDFs in `Figures/` for visual checks.
5. Use the tab-delimited CSV files in `Figures/` for metric submission.
