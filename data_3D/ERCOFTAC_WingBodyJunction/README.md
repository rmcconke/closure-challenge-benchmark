# ERCOFTAC Wing-Body Junction (Re = 115 000)

Wing-body junction flow — a NACA 0020 airfoil mounted on a flat plate. The
horseshoe vortex system around the leading-edge junction is the canonical hard
test for RANS in 3D corner flows. **Re = 115 000** based on chord. Source:
ERCOFTAC DNS-1-6
([KBwiki entry](https://www.kbwiki.ercoftac.org/w/index.php/DNS_1-6)).

## What's in this folder

| Subdir | Contents |
|--------|----------|
| `highfidelity/` | DNS reference: bottom-wall centerline profile (`bottom_wall_centerline.csv`), midplane upstream-of-LE profiles (`profile_midplane_-{0.01..0.45}.csv`, 10 stations), wing root-chord profile and surface CSVs. |
| `baseline_komegasst/` | k-ω SST RANS baseline at the same probe locations + `scalars.json`. |
| `plots/` | Pre-rendered comparison figures and `plot_profiles.py`. |

Heavy raw DNS surface dumps (`raw_surface/`, ~1.1 GB of VTU files) and OpenFOAM
case directories (`VTK/`, time directories, `postProcessing/`) live on the
**SURF drive** — see top-level README.

## Regenerating the plots

```bash
cd data_3D/ERCOFTAC_WingBodyJunction/plots
python plot_profiles.py
MODEL_DIR=/path/to/my_results python plot_profiles.py   # Adds "Submitted model"
```

A submission folder mirrors `highfidelity/`: same filenames (excluding
`raw_surface/`), same column schema.
