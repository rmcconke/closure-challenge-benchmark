# Benchmark challenge for machine learning in RANS turbulence modelling

# Current leaderboard
|   Rank | Authors                                                                                                                                   |   Overall |   alpha_15_13929_4048 |   alpha_15_13929_2024 |   alpha_05_4071_4048 |   alpha_05_4071_2024 |   AR_1_Ret_360 |   AR_3_Ret_360 |   AR_14_Ret_180 |   NASA_2DWMH |
|--------|-------------------------------------------------------------------------------------------------------------------------------------------|-----------|-----------------------|-----------------------|----------------------|----------------------|----------------|----------------|-----------------|--------------|
|      1 | [Reissmann, Fang, and Sandberg](https://github.com/rmcconke/closure-challenge-benchmark/blob/main/submissions/reissmann/score_eval.ipynb) |    0.0595 |                0.0592 |                0.1339 |               0.0606 |               0.076  |         0.0387 |         0.0341 |          0.0325 |       0.0412 |
|      2 | [Wu and Zhang](https://github.com/rmcconke/closure-challenge-benchmark/blob/main/submissions/wu/description_document.pdf)                 |    0.0624 |                0.0813 |                0.1195 |               0.0569 |               0.0848 |         0.0455 |         0.0399 |          0.035  |       0.0364 |
|      3 | [Montoya, Oulghelou, and Cinnella](https://doi.org/10.1007/s10494-025-00661-8)                                                            |    0.0779 |                0.068  |                0.1364 |               0.0591 |               0.0882 |         0.0895 |         0.0866 |          0.0487 |       0.0464 |


Notes:
- Score is a scaled MAE (lower is better). See the evaluation package [source code](https://github.com/rmcconke/closure-challenge/blob/main/src/closure_challenge/eval.py) for more details.
- Submissions are accepted anytime! See below for submission instructions.
- We now have an [arXiv preprint](https://arxiv.org/abs/2603.28884) for the challenge. However, this page is the main source of up-to-date information.

# Motivation
The field of ML augmented RANS modelling has seen significant interest for at least a decade. Many methodologies have been proposed. However, a critical problem slowing progress in the field is the absence of an open-source benchmark dataset with clear evaluation criteria. In order to compare a new technique against an existing technique, significant effort is required. We aim to eliminate this required effort and greatly accelerate progress in the field by implementing a benchmark dataset for ML in RANS.

Our goal is to create a challenging dataset that represents the actual state of ML-augmented RANS turbulence modelling. We aim to propose challenging generalization tasks, with the goal that over time, techniques which generalize better will rise to the top of the leaderboard. We do not want to cast the field in an overly optimistic light; we want to provide a hard challenge that will motivate new ideas in the field.

The benchmark task is to **predict the flow field** for a series of test cases given a specified training and validation dataset, as well as a given CFD mesh. All other decisions are left to the submitter.

This is an **ongoing** challenge. It is not associated with any particular conference or event. This running leaderboard aims to summarize the state of the art in the field of ML for RANS turbulence modelling.



If you have questions or suggestions as this challenge is developed, please open an issue in this repo. This is a community effort!

# Datasets
The following fields are available for each of the datasets:
- RANS predictions with the $k$ - $\omega$ SST model
- DNS or LES "ground truth" data, including **velocity gradients**
## Periodic hills 29 parametric variations
Original data link: [https://github.com/xiaoh/para-database-for-PIML](https://github.com/xiaoh/para-database-for-PIML)
## Periodic hills Re=10595
Original data link: [https://turbmodels.larc.nasa.gov/Other_LES_Data/2dhill_periodic.html](https://turbmodels.larc.nasa.gov/Other_LES_Data/2dhill_periodic.html)
## Square and rectangular duct
Original data link: [https://www.vinuesalab.com/duct/](https://www.vinuesalab.com/duct/)
## Curved backward-facing step
Original data link: [https://turbmodels.larc.nasa.gov/Other_LES_Data/curvedstep.html](https://turbmodels.larc.nasa.gov/Other_LES_Data/curvedstep.html)
## NASA Wall-mounted hump  
Original data link: [https://turbmodels.larc.nasa.gov/nasahump_val.html](https://turbmodels.larc.nasa.gov/nasahump_val.html)

## 3D Cases
Lightweight comparison data (probe-line CSVs, profiles, surface integrals, plot
scripts) for the 3D cases lives in [`data_3D/`](data_3D/). Heavy raw simulation data
— OpenFOAM time directories, VTK volume dumps, `polyMesh/`, `postProcessing/`,
WBJ's 1.1 GB DNS surface dumps — lives on the SURF drive:
**[https://surfdrive.surf.nl/s/G5ND38JxRXbWBJQ](https://surfdrive.surf.nl/s/G5ND38JxRXbWBJQ)**

### Square and rectangular duct
Original data link: [https://www.vinuesalab.com/duct/](https://www.vinuesalab.com/duct/)
### Wing-body junction flow (Re = 115k) — [`data_3D/ERCOFTAC_WingBodyJunction/`](data_3D/ERCOFTAC_WingBodyJunction/)
Original data link: [https://www.ercoftac.org/](https://www.kbwiki.ercoftac.org/w/index.php/DNS_1-6) (ERCOFTAC DNS 1-6)
### Ahmed Body automotive wake (Re = 760k) — [`data_3D/ERCOFTAC_AhmedBody25/`](data_3D/ERCOFTAC_AhmedBody25/)
Original data link: [https://www.ercoftac.org/](http://cfd.mace.manchester.ac.uk/ercoftac/doku.php?id=cases:case082) (ERCOFTAC Database)
### Faith Hill smooth-body separation (Re = 500k) — [`data_3D/NASA_FaithHill/`](data_3D/NASA_FaithHill/)
Original data link: [https://turbmodels.larc.nasa.gov/faith_val.html](https://turbmodels.larc.nasa.gov/Other_exp_Data/FAITH_hill_exp.html)

### Regenerating 3D plots with your model

Each `data_3D/<case>/plots/plot_profiles.py` accepts a `MODEL_DIR` env var. Drop
your predictions into a folder that mirrors `<case>/highfidelity/` (same filenames
and column schema) and run:

```bash
cd data_3D/NASA_FaithHill/plots
MODEL_DIR=/path/to/my_results python plot_profiles.py
```

A "Submitted model" curve is added to every panel. Files the script can't find are
silently skipped, so partial submissions degrade to empty panels rather than crashes.

## 2D challenge refresh — `data_closure_v2/`

A refreshed version of the 4 active 2D cases with the agreed evaluation metrics
sits in [`data_closure_v2/`](data_closure_v2/). This is staged separately from the
existing `data/` (which is wired into the `eval_submissions.py` leaderboard) so it
can be reviewed and merged deliberately.

| Case | Folder | Agreed metrics |
|------|--------|----------------|
| Periodic hills (Re = 5600 + 10595) | `data_closure_v2/Periodic_Hill-8/` | Velocity + shear stress profiles, Cf (bottom + upper wall) |
| NASA hump | `data_closure_v2/NASA_Hump-8/` | Velocity + shear stress profiles, Cp + Cf (bottom wall) |
| Square duct | `data_closure_v2/SquareDuct-8/` | Axial velocity profile + transverse velocities |
| Curved backward-facing step (CBFS) | `data_closure_v2/CBFS-8/` | Velocity + shear stress profiles, Cf (bottom wall) |

Each case folder carries `comparison_<CASE>.py` (the canonical plot script), a
`Figures/` subdirectory with pre-rendered PDFs and curated metric CSVs, plus
`00Baseline/` (k-ω SST RANS run), `01Frozen/` (frozen-baseline trace), and
`RefData/` (DNS / LES / experiment reference). The very large NASA Hump DNS dumps
(`LES.dat`, `VelocityDerivatives.dat`, `pickledLESData.pickle`, ~435 MB combined)
are kept on the SURF drive — drop them into `data_closure_v2/NASA_Hump-8/RefData/`
before running `comparison_NASA.py`.

## Draft 2D extensions — `data_2D_extended_draft/`

Three NASA TMR Collaborative Testing Challenge 2022 cases (NASA_2DZP, NASA_ASJ,
NASA_2DN00) are staged in [`data_2D_extended_draft/`](data_2D_extended_draft/). The
final layout — folder naming, evaluation-point grids, integration with the live
leaderboard — is **TBD**. See the README in that folder for details.

# Challenge rules 
## Input features and fields
There are many techniques for data-driven RANS turbulence modelling. We have provided baseline $k$-$\omega$ SST fields to generate your input feature set, but you do not need to use these. **You are free to use your own input features, base turbulence model, data assimilation technique, etc.** We have relaxed these rules based on community feedback.

## Training/validation/test split
The only strict rule in this challenge is:

It is **strictly forbidden** to train or validate on any data from the **test cases** in the table below. The purpose of this benchmark is to provide an honest evaluation and comparison between various ML techniques in turbulence modelling. If you are found to have **trained** or **validated** on any of the test cases, your submission will be automatically withdrawn, and a note will be made on the leaderboard.

Other than this strict requirement, **you are free to use your own training/validation data**. 

A suggested training/validation split is given below for the data provided with the challenge.

A checkmark in the below table indicates cases where only a single parametric variation is available; otherwise, the datasets are split into train/validation/test.

|**Flow**  | **Training (suggested)** | **Validation (suggested)** | **Test** |
|- | - | - |  - |
|**PHLL29** | (21 remaining cases)|`alpha_05_10071_4048`, `alpha_05_10071_2024`, `alpha_15_7929_4048`, `alpha_15_7929_2024`| `alpha_15_13929_4048`, `alpha_15_13929_2024`, `alpha_05_4071_4048`, `alpha_05_4071_2024`|
|**DUCT** | `AR_1_Ret_180`, `AR_3_Ret_180`,`AR_5_Ret_180`, `AR_10_Ret_180` | `AR_7_Ret_180`  |`AR_1_Ret_360`,`AR_3_Ret_360`,`AR_14_Ret_180`|
|**CBFS13700** |✓ | | |
|**NASAHUMP**|  | |✓ |
|**PHLL10595**| ✓ | | |

The below figure clarifies the validation/test split chosen for the periodic hills dataset.
![Alt text](phll_tvt_split.png)


The benchmark scores are based on your model's performance on the test datasets.



# Design philosophy
The train/val/test split in the challenge tests the following:
- Reynolds number generalization
- Geometry generalization

# Submission instructions
The scoring code is available here: [closure-challenge](https://github.com/rmcconke/closure-challenge).

You must submit your predictions on the test dataset in **CSV format**.

1. Save your interpolated predictions in CSV format under the respective directories in the `test` subdirectory of the benchmark dataset. You can easily get the evaluation points using the [python package](https://github.com/rmcconke/closure-challenge) for the challenge. These points are also provided for convenience under `data/evaluation_points`.
2. You can preview what your score will be using the benchmark dataset's [python package](https://github.com/rmcconke/closure-challenge).
3. Send your `test` subdirectory to Ryley McConkey: rmcconke@mit.edu . Also include a list of all authors, and any relevant references (e.g., papers, github repos, etc.)
4. The benchmark steward (currently, Ryley McConkey) will evaluate your predictions, and update the leaderboard accordingly.


# Citation
If you use the data or benchmark in your work, please cite the [arXiv preprint](https://arxiv.org/abs/2603.28884):
```
@article{closurechallenge,
  title={The Closure Challenge: a benchmark task for machine learning in turbulence modelling},
  author={McConkey, Ryley and Buchanan, Tyler and Smidt, Tess and Bodner, Abigail and Dwight, Richard and Cinnella, Paola},
  eprint={2603.28884},
  archivePrefix={arXiv},
  year={2026},
  doi={10.48550/arXiv.2603.28884}
}
```


