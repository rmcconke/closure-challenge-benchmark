"""
Paired bootstrap over evaluation points for the Closure Challenge leaderboard.

Question answered: if a different random draw of ~1000 evaluation points had been
taken from each flow field, how much would the leaderboard scores -- and the gaps
between adjacent ranks -- move?

This is NOT an estimate of uncertainty in the reference DNS/LES data itself. It is
the uncertainty contributed by the finite point sample used for evaluation.

Method
------
The per-case score is

    s_case = mean_i ||U_pred_i - U_true_i||  /  mean_i ||U_true_i||

a ratio of two means over the same N points. The evaluation points are independent
random draws from each field, so resampling the point indices with replacement
gives the sampling distribution of the score directly.

Two design choices worth stating in the paper:

1. PAIRED. The same resampled indices are used for every entry, because all
   entries are evaluated at identical points. Point-to-point difficulty (near-wall
   and separated-shear-layer points are hard for everyone) then cancels in the
   entry-vs-entry difference, so the interval on a *gap* is much tighter than the
   intervals on the two scores separately. Comparing marginal intervals for
   overlap understates the resolving power of the benchmark -- report the paired
   difference instead.

2. SCALE RESAMPLED TOO. The denominator is recomputed on the same bootstrap
   sample, since it is also a mean over the drawn points. Set RESAMPLE_SCALE =
   False to hold it fixed at the full-sample value (gives slightly tighter bands).

Usage
-----
    python bootstrap_points.py
    python bootstrap_points.py --replicates 20000 --seed 1
"""

import argparse
import json
import os
from pathlib import Path

import numpy as np

# --------------------------------------------------------------------------
# Configuration -- edit to match your repo layout
# --------------------------------------------------------------------------

GROUND_TRUTH_NPZ = Path("closure_challenge/data/ground_truth_test.npz")

SUBMISSIONS = {
    "Reissmann, Fang, and Sandberg": {
        "alpha_15_13929_4048": "submissions/reissmann/alpha_15_13929_4048/predictions.csv",
        "alpha_15_13929_2024": "submissions/reissmann/alpha_15_13929_2024/predictions.csv",
        "alpha_05_4071_4048":  "submissions/reissmann/alpha_05_4071_4048/predictions.csv",
        "alpha_05_4071_2024":  "submissions/reissmann/alpha_05_4071_2024/predictions.csv",
        "AR_1_Ret_360":        "submissions/reissmann/AR_1_Ret_360/predictions.csv",
        "AR_3_Ret_360":        "submissions/reissmann/AR_3_Ret_360/predictions.csv",
        "AR_14_Ret_180":       "submissions/reissmann/AR_14_Ret_180/predictions.csv",
        "NASA_2DWMH":          "submissions/reissmann/NASA_2DWMH/predictions.csv",
    },
    "Wu and Zhang":              os.path.join("submissions", "wu"),
    "Liu, Wang, Zhao, and Xiao": os.path.join("submissions", "wang"),
    "Montoya, Oulghelou, and Cinnella": os.path.join("submissions", "montoya"),
}

RESAMPLE_SCALE = True
DELIMITER = ","

# --------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------


def load_ground_truth(npz_path):
    """Return {case: {'U': (N,3), 'coords': (N,d)}} preserving key order."""
    raw = np.load(npz_path)
    gt = {}
    for full_key in raw.keys():
        case, field = full_key.split("/", 1)
        gt.setdefault(case, {})[field] = raw[full_key]
    return gt


def _as_velocity_array(obj):
    """Accept a bare (N,3) array, or a dict/npz-like carrying 'U'."""
    if isinstance(obj, np.ndarray) and obj.dtype != object:
        return obj
    try:
        return np.asarray(obj["U"])
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError(f"could not find a velocity array in {type(obj)}") from exc


def load_predictions(spec, cases, delimiter=DELIMITER):
    """spec is either {case: csv_path} or a folder containing {case}.csv."""
    preds = {}
    if isinstance(spec, dict):
        for case, path in spec.items():
            preds[case] = _as_velocity_array(
                np.genfromtxt(path, delimiter=delimiter)
            )
    else:
        folder = Path(spec)
        for case in cases:
            preds[case] = _as_velocity_array(
                np.loadtxt(folder / f"{case}.csv", delimiter=delimiter)
            )
    return preds


# --------------------------------------------------------------------------
# Per-point errors
# --------------------------------------------------------------------------


def per_point_errors(gt, submissions, cases):
    """
    Returns
        err[entry][case]  -> (N,) per-point ||U_pred - U_true||
        true_norm[case]   -> (N,) per-point ||U_true||
    """
    true_norm = {c: np.linalg.norm(gt[c]["U"], axis=-1) for c in cases}

    err = {}
    for name, spec in submissions.items():
        preds = load_predictions(spec, cases)
        err[name] = {}
        for case in cases:
            U_true = gt[case]["U"]
            U_pred = np.asarray(preds[case], dtype=float)
            if U_pred.shape != U_true.shape:
                raise ValueError(
                    f"{name} / {case}: prediction shape {U_pred.shape} "
                    f"!= reference shape {U_true.shape}"
                )
            err[name][case] = np.linalg.norm(U_pred - U_true, axis=-1)
    return err, true_norm


def point_scores(err, true_norm, cases):
    """Full-sample per-case and overall scores, for cross-checking the leaderboard."""
    out = {}
    for name in err:
        per_case = {
            c: err[name][c].mean() / true_norm[c].mean() for c in cases
        }
        out[name] = {
            "cases": per_case,
            "overall": float(np.mean(list(per_case.values()))),
        }
    return out


# --------------------------------------------------------------------------
# Bootstrap
# --------------------------------------------------------------------------


def bootstrap(err, true_norm, cases, n_rep, rng, resample_scale=RESAMPLE_SCALE):
    """
    Returns
        overall[entry] -> (n_rep,)
        by_case[entry][case] -> (n_rep,)

    Indices are drawn once per case per replicate and SHARED across entries.
    """
    names = list(err.keys())
    overall = {n: np.empty(n_rep) for n in names}
    by_case = {n: {c: np.empty(n_rep) for c in cases} for n in names}

    for case in cases:
        N = true_norm[case].shape[0]
        idx_matrix = rng.integers(0, N, size=(n_rep, N))

        tn = true_norm[case]
        scale_rep = (
            tn[idx_matrix].mean(axis=1) if resample_scale
            else np.full(n_rep, tn.mean())
        )

        for name in names:
            e = err[name][case]
            by_case[name][case] = e[idx_matrix].mean(axis=1) / scale_rep

    for name in names:
        overall[name] = np.mean(
            np.stack([by_case[name][c] for c in cases], axis=0), axis=0
        )
    return overall, by_case


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------


def ci(samples, alpha=0.05):
    lo, hi = np.percentile(samples, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return float(lo), float(hi)


def report(full, overall_boot, by_case_boot, cases, alpha=0.05):
    order = sorted(full, key=lambda n: full[n]["overall"])

    print("\n=== Overall score with point-sampling CI ===")
    print(f"{'Rank':<5} {'Entry':<38} {'Score':>8} "
          f"{'CI low':>9} {'CI high':>9} {'half-width':>11}")
    for rank, name in enumerate(order, 1):
        lo, hi = ci(overall_boot[name], alpha)
        print(f"{rank:<5} {name:<38} {full[name]['overall']:>8.4f} "
              f"{lo:>9.4f} {hi:>9.4f} {(hi - lo) / 2:>11.4f}")

    print("\n=== Paired adjacent-rank differences (the number that matters) ===")
    print("Positive difference = the higher-ranked entry is genuinely ahead.\n")
    print(f"{'Comparison':<52} {'Gap':>8} {'CI low':>9} "
          f"{'CI high':>9} {'P(better)':>10}")
    for a, b in zip(order[:-1], order[1:]):
        diff = overall_boot[b] - overall_boot[a]  # b is worse => positive
        lo, hi = ci(diff, alpha)
        p_better = float((diff > 0).mean())
        gap = full[b]["overall"] - full[a]["overall"]
        label = f"{a.split(',')[0]} vs {b.split(',')[0]}"
        print(f"{label:<52} {gap:>8.4f} {lo:>9.4f} {hi:>9.4f} "
              f"{p_better:>10.3f}")

    print("\n=== Smallest detectable difference ===")
    halfwidths = []
    for a, b in zip(order[:-1], order[1:]):
        lo, hi = ci(overall_boot[b] - overall_boot[a], alpha)
        halfwidths.append((hi - lo) / 2)
    sdd = float(np.max(halfwidths))
    print(f"Largest adjacent-pair CI half-width: {sdd:.4f}")
    print(f"=> Overall-score differences below ~{sdd:.4f} are not resolved "
          f"by the current point sample.")

    print("\n=== Per-case CI half-widths ===")
    header = f"{'Entry':<38}" + "".join(f"{c[:14]:>16}" for c in cases)
    print(header)
    for name in order:
        row = f"{name:<38}"
        for c in cases:
            lo, hi = ci(by_case_boot[name][c], alpha)
            row += f"{(hi - lo) / 2:>16.4f}"
        print(row)

    return {
        "order": order,
        "smallest_detectable_difference": sdd,
        "overall": {
            n: {
                "score": full[n]["overall"],
                "ci": ci(overall_boot[n], alpha),
            }
            for n in order
        },
        "adjacent_pairs": [
            {
                "better": a,
                "worse": b,
                "gap": full[b]["overall"] - full[a]["overall"],
                "ci": ci(overall_boot[b] - overall_boot[a], alpha),
                "p_better": float((overall_boot[b] - overall_boot[a] > 0).mean()),
            }
            for a, b in zip(order[:-1], order[1:])
        ],
    }


# --------------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--replicates", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--out", type=str, default="bootstrap_results.json")
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)

    gt = load_ground_truth(GROUND_TRUTH_NPZ)
    cases = list(gt.keys())
    print(f"Loaded {len(cases)} cases: {', '.join(cases)}")
    for c in cases:
        print(f"  {c:<24} N = {gt[c]['U'].shape[0]}")

    err, true_norm = per_point_errors(gt, SUBMISSIONS, cases)

    full = point_scores(err, true_norm, cases)
    print("\n=== Cross-check against published leaderboard ===")
    print("These must match your table to 4 dp before the CIs mean anything.")
    for name in sorted(full, key=lambda n: full[n]["overall"]):
        print(f"  {name:<38} {full[name]['overall']:.4f}")

    overall_boot, by_case_boot = bootstrap(
        err, true_norm, cases, args.replicates, rng
    )

    summary = report(full, overall_boot, by_case_boot, cases, args.alpha)
    summary["settings"] = {
        "replicates": args.replicates,
        "seed": args.seed,
        "alpha": args.alpha,
        "resample_scale": RESAMPLE_SCALE,
    }
    Path(args.out).write_text(json.dumps(summary, indent=2))
    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()