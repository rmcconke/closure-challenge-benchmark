# NASA Faith Hill — smooth-body separation

Axisymmetric ground-mounted hill, **Re_h = 500 000**, U_∞ = 50.3 m/s (M = 0.143),
hill height h = 152.4 mm. Source: Bell, Heineck, Zilliac, Mehta, Long
(AIAA 2012-0704); NASA TMR — [Faith Hill experimental data](https://turbmodels.larc.nasa.gov/Other_exp_Data/FAITH_hill_exp.html).

## What's in this folder

| Subdir | Contents |
|--------|----------|
| `highfidelity/` | Experimental reference: PIV centerline (`PIV_centerline_2Hz_4000samps.csv`, 1 kHz), PSP wall pressure (`PSP_centerline_p150.csv`), FISF surface skin friction (`FISF_FAITH_surface.csv`). |
| `baseline_komegasst/` | k-ω SST RANS baseline at the same probe locations + `scalars.json`. |
| `plots/` | Pre-rendered comparison figures (PIV U / k contours, profiles at 8 stations, PSP Cp, FISF Cf) and `plot_profiles.py`. |

Heavy raw simulation data (full OpenFOAM time directories, VTK volume dumps,
`postProcessing/`, `polyMesh/`) lives on the **SURF drive** linked from the top-level
README — too large for git.

## Regenerating the plots

```bash
cd data_3D/NASA_FaithHill/plots
python plot_profiles.py                   # Exp + Baseline only
MODEL_DIR=/path/to/my_results python plot_profiles.py   # Adds "Submitted model"
```

A submission folder mirrors `highfidelity/`: same filenames, same column schema. Any
file the script doesn't find is silently skipped, so partial submissions degrade to
empty panels rather than crashes.
