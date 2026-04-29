# Curved Backward-Facing Step Metrics

This case generates the required curved backward-facing step challenge metrics:

- Velocity profiles
- Reynolds shear stress profiles
- Bottom-wall pressure coefficient, `Cp`
- Bottom-wall skin-friction coefficient, `Cf`

All cases in this directory were prepared and run with OpenFOAM 8.

The submitted comparison is between:

- `00Baseline`: RANS(SST) OpenFOAM result using `RITAkOmegaSST`
- `RefData`: LES reference data from the NASA curved-step data set

`01Frozen` is a separate frozen/interpolated-LES setup. The interpolated LES
fields on the RANS mesh are stored in `01Frozen/0/`. The current comparison
script uses its sampled `Ux_LES` profiles for the velocity-profile LES overlay
and CSV export, but the required SST baseline is still `00Baseline`.

## Directory Layout

```text
CBFS-8/
├── 00Baseline/             # OpenFOAM RITAkOmegaSST baseline case
├── 01Frozen/               # Frozen-field case using LES fields on the RANS mesh
├── Common/                 # Shared run scripts, dictionaries, and field files
├── RefData/                # NASA/LES reference data
├── Figures/                # Generated plots and metric CSV files
├── comparison_CBFS.py      # Main script for required metric plots and exports
└── readExpData.py
```

## Reference Data

The LES reference data were obtained from:

```text
https://turbmodels.larc.nasa.gov/Other_LES_Data/curvedstep.html
```

The NASA page credits S. Lardeau of CD-adapco and documents the data through:

```text
Bentaleb, Y., Lardeau, S., and Leschziner, M. A. (2012).
Large-eddy simulation of turbulent boundary layer separation from a rounded
step. Journal of Turbulence, 13(4), 1-28.

Lardeau, S. and Leschziner, M. A. (2011).
The interaction of round synthetic jets with a turbulent boundary layer
separating from a rounded ramp. Journal of Fluid Mechanics, 683, 172-211.
```

The wall data are read from:

```text
RefData/LES_walldata.txt
```

The velocity and stress profiles are read from:

```text
RefData/curvedbackstep_vel_stress.dat
```

## Note On `01Frozen`

`01Frozen` is a frozen-field setup designed for interpolated LES fields on the
RANS/SST mesh. Those interpolated LES fields are in:

```text
01Frozen/0/
```

Running `01Frozen/run.sh` requires the custom OpenFOAM solver:

```text
frozenSimpleFoam
```

Important files there include:

```text
U_LES
k_LES
p_LES
tauij_LES
```

## Generate The SST Baseline Data

Run the baseline OpenFOAM case first:

```bash
cd CBFS-8/00Baseline
./run.sh
```

This runs:

```text
modelPropagationFoam
```

and creates the `baselineSolution` symlink to the latest time directory.

The baseline model is set in:

```text
00Baseline/constant/momentumTransport
```

as:

```text
RASModel        RITAkOmegaSST;
```

`RITAkOmegaSST` is used here so the baseline post-processing exports `gradU`.
The sampled profile dictionaries write `nut` and `gradU`, which are needed for
the modeled SST shear-stress profile calculation.

After the solver run, run the post-processing script:

```bash
cd CBFS-8/00Baseline
./postProcess.sh
```

The post-processing step writes the wall and profile data used by
`comparison_CBFS.py`, including:

- `postProcessing/bottomValues/`
- `postProcessing/singleGraph_x0/`
- `postProcessing/singleGraph_x1/`
- `postProcessing/singleGraph_x2/`
- `postProcessing/singleGraph_x3/`
- `postProcessing/singleGraph_x4/`
- `postProcessing/singleGraph_x5/`
- `postProcessing/singleGraph_x6/`
- `postProcessing/singleGraph_x7/`
- `postProcessing/singleGraph_x8/`

## Generate Required Plots And CSV Files

From the case root, run:

```bash
cd CBFS-8
python3 comparison_CBFS.py
```

Use a Python environment with `numpy` and `matplotlib` available. For this
workspace, the `gepfoam` conda environment works:

```bash
MPLCONFIGDIR=/tmp/matplotlib-gepfoam \
  /home/renzhi/anaconda3/envs/gepfoam/bin/python comparison_CBFS.py
```

The script also uses the local helper module `readExpData.py`.

## Generated Figures

The script writes these PDF plots:

```text
Figures/compareCpWall-CBFS.pdf
Figures/compareCfWall-CBFS.pdf
Figures/compareUxProfiles_CBFS.pdf
Figures/compareuvProfiles_CBFS.pdf
```

The profile plots use `x/h` and `y/h`. Curves are shifted in the horizontal
direction for readability:

- Velocity: `Ux/Uref + x/h`
- Reynolds shear stress: `50 uv/Uref^2 + x/h`

The shift and scaling are only for plotting. The CSV files store the raw
normalized quantities.

## Generated CSV Metrics

The script writes tab-delimited CSV files:

```text
Figures/wall_Cp_Cf_CBFS.csv
Figures/velocity_shear_profiles_CBFS.csv
```

`wall_Cp_Cf_CBFS.csv` contains side-by-side SST and LES wall data:

```text
x_over_h
Cp_RANS_SST
Cp_LES
Cf_RANS_SST
Cf_LES
```

`velocity_shear_profiles_CBFS.csv` contains side-by-side SST and LES profile
data:

```text
station_x_over_h
wall_normal_over_h
Ux_over_Uref_RANS_SST
Ux_over_Uref_LES
uv_over_Uref2_RANS_SST
uv_over_Uref2_LES
```

Rows where either the SST or LES value is unavailable are dropped, so the
exported CSV files do not contain `nan` entries.

## Metric Definitions

The reference scales are:

```text
Uref = 1.0
pref = 0.0
h = 1.0
```

### Bottom-Wall Pressure Coefficient

For SST:

```text
Cp = (p - pref) / (0.5 Uref^2)
```

For LES, `Cp` is read directly from the third column of:

```text
RefData/LES_walldata.txt
```

### Bottom-Wall Skin-Friction Coefficient

For SST, `Cf` is computed from the wall-tangential component of the OpenFOAM
wall shear stress:

```text
tau_t = wallShearStress · t
Cf = -tau_t / (0.5 Uref^2)
```

The local tangent vector `t` is computed from the ordered bottom-wall
coordinates. The minus sign matches the wall-point/tangent orientation used by
the bottom-wall sampling.

For LES, the wall-data file stores `Cf/2` in the fourth column, so the script
uses:

```text
Cf = 2 (column 4)
```

### Velocity Profiles

The velocity profile metric is:

```text
Ux / Uref
```

The CSV stores SST values at the OpenFOAM sampling points. LES values from
`01Frozen` are linearly interpolated onto those same wall-normal locations.

### Shear Stress Profiles

The shear stress profile is the Reynolds shear stress component:

```text
uv / Uref^2
```

For LES this comes from:

```text
uv/U_in^2
```

in `RefData/curvedbackstep_vel_stress.dat`.

For SST/RANS, the modeled turbulent shear stress is reconstructed from eddy
viscosity and the sampled `gradU` field exported by `00Baseline`:

```text
uv = -nut (dUx/dy + dUy/dx)
```

The required sampled fields are:

```text
nut
dUx/dy
dUy/dx
```

These are written by the `00Baseline` `RITAkOmegaSST` setup and read by
`comparison_CBFS.py`.

## Regeneration Checklist

1. Source the intended OpenFOAM environment.
2. Run `00Baseline/run.sh`.
3. Run `00Baseline/postProcess.sh`.
4. Run `python3 comparison_CBFS.py` from `CBFS-8/`.
5. Use the PDFs in `Figures/` for visual checks.
6. Use the tab-delimited CSV files in `Figures/` for metric submission.
