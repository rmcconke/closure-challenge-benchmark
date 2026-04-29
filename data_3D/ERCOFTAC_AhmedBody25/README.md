# ERCOFTAC Ahmed Body — 25° slant, automotive wake

Generic bluff-body car shape with a **25° rear slant** (the harder of the two canonical
Ahmed configurations — flow stays attached on the slant, generating strong streamwise
vortices). **Re_h = 768 000**, U_b = 40 m/s, body height h = 288 mm, slant length =
222 mm. Source: ERCOFTAC Database
[case 82](http://cfd.mace.manchester.ac.uk/ercoftac/doku.php?id=cases:case082).

## What's in this folder

| Subdir | Contents |
|--------|----------|
| `highfidelity/` | Experimental reference: surface pressure (`ahmed-25-press.csv`), centerline & spanwise wake profiles (`ahmed-25-y000-whole.csv`, `ahmed-25-yp{000,100,180,195}-xz.csv`, `ahmed-25-ym195-xz.csv`), wake cross-sections at multiple x stations (`ahmed-25-x{m038,m088,m138,m178,p000,p080,p200,p500}-yz.csv`), inlet boundary layers, and stagger-line BL profiles. |
| `baseline_komegasst/` | k-ω SST RANS baseline at the same probe locations + `scalars.json`. |
| `plots/` | Pre-rendered comparison figures (rear surface Cp, slant-region U/k profiles, wake U/k/uw contours and stagger profiles) and `plot_profiles.py`. |

Heavy raw simulation data lives on the **SURF drive** — see top-level README.

## Regenerating the plots

```bash
cd data_3D/ERCOFTAC_AhmedBody25/plots
python plot_profiles.py
MODEL_DIR=/path/to/my_results python plot_profiles.py   # Adds "Submitted model"
```

A submission folder mirrors `highfidelity/`: same filenames, same column schema.
