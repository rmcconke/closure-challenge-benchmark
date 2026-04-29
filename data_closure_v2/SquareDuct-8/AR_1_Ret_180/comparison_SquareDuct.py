#!/usr/bin/env python3
"""Compare Square Duct AR=1 diagonal velocity profiles.

Outputs are written to Figures/:
  - compareUxProfiles_SquareDuct_AR1_ReTau180.pdf
  - compareUpProfiles_SquareDuct_AR1_ReTau180.pdf
  - velocity_diagonal_profiles_SquareDuct_AR1_ReTau180.csv

The CSV is tab-delimited and keeps RANS(SST) and LES values side by side.
"""

from __future__ import annotations

import csv
import os
import re
from pathlib import Path

if "MPLCONFIGDIR" not in os.environ:
    mpl_dir = Path.home() / ".config" / "matplotlib"
    if not (mpl_dir.exists() and os.access(mpl_dir, os.W_OK)):
        os.environ["MPLCONFIGDIR"] = f"/tmp/matplotlib-{os.getuid()}"

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter


CASE_TAG = "SquareDuct_AR1_ReTau180"
RANS_LABEL = "RANS(SST)"
LES_LABEL = "LES"


def read_case_def(case_def_path: Path) -> dict[str, float]:
    """Read scalar entries from the local OpenFOAM-style caseDef file."""
    values: dict[str, float] = {}
    pattern = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s+([^;]+);")

    with case_def_path.open("r", encoding="utf-8", errors="ignore") as handle:
        for raw_line in handle:
            line = raw_line.split("//", 1)[0].strip()
            if not line:
                continue
            match = pattern.match(line)
            if not match:
                continue
            try:
                values[match.group(1)] = float(match.group(2).strip())
            except ValueError:
                continue

    return values


def find_latest_diag_file(case_dir: Path, filename_candidates: list[str]) -> Path | None:
    """Find the latest diagonal line file below postProcessing/singleGraphDiag."""
    graph_dir = case_dir / "postProcessing" / "singleGraphDiag"
    if not graph_dir.exists():
        return None

    latest_file: Path | None = None
    latest_time = float("-inf")
    for time_dir in graph_dir.iterdir():
        if not time_dir.is_dir():
            continue
        try:
            time_value = float(time_dir.name)
        except ValueError:
            continue

        for filename in filename_candidates:
            candidate = time_dir / filename
            if candidate.exists() and time_value >= latest_time:
                latest_time = time_value
                latest_file = candidate

    return latest_file


def load_velocity_file(path: Path) -> np.ndarray:
    """Load a line profile with columns [x, y, z, Ux, Uy, Uz]."""
    data = np.loadtxt(path)
    if data.ndim == 1:
        data = data[np.newaxis, :]
    if data.shape[1] < 6:
        raise ValueError(f"Expected at least 6 columns in {path}, got {data.shape[1]}.")
    return np.asarray(data[:, :6], dtype=float)


def make_profile(data: np.ndarray, h: float, u_b: float) -> dict[str, np.ndarray]:
    """Return raw and normalized diagonal profile quantities sorted by r/h."""
    x = data[:, 0]
    y = data[:, 1]
    z = data[:, 2]
    ux = data[:, 3]
    uy = data[:, 4]
    uz = data[:, 5]

    finite = (
        np.isfinite(x)
        & np.isfinite(y)
        & np.isfinite(z)
        & np.isfinite(ux)
        & np.isfinite(uy)
        & np.isfinite(uz)
    )
    x = x[finite]
    y = y[finite]
    z = z[finite]
    ux = ux[finite]
    uy = uy[finite]
    uz = uz[finite]

    r_over_h = np.sqrt(y**2 + z**2) / h
    up = np.sqrt(uy**2 + uz**2)
    order = np.argsort(r_over_h)

    return {
        "x": x[order],
        "y": y[order],
        "z": z[order],
        "r_over_h": r_over_h[order],
        "Ux": ux[order],
        "Uy": uy[order],
        "Uz": uz[order],
        "Up": up[order],
        "Ux_over_Ub": ux[order] / u_b,
        "Up_over_Ub": up[order] / u_b,
    }


def interp_with_nan(x_new: np.ndarray, x_old: np.ndarray, y_old: np.ndarray) -> np.ndarray:
    """Interpolate one profile and keep values outside the source range as NaN."""
    order = np.argsort(x_old)
    x_sorted = x_old[order]
    y_sorted = y_old[order]
    unique_x, unique_idx = np.unique(x_sorted, return_index=True)
    unique_y = y_sorted[unique_idx]
    return np.interp(x_new, unique_x, unique_y, left=np.nan, right=np.nan)


def write_profiles_csv(
    csv_path: Path,
    rans: dict[str, np.ndarray],
    les: dict[str, np.ndarray],
) -> int:
    """Write tab-delimited side-by-side RANS(SST)/LES profile data."""
    r = rans["r_over_h"]
    les_interp = {
        key: interp_with_nan(r, les["r_over_h"], les[key])
        for key in ("Ux", "Uy", "Uz", "Up", "Ux_over_Ub", "Up_over_Ub")
    }

    header = [
        "r_over_h",
        "x",
        "y",
        "z",
        "Ux_RANS_SST",
        "Uy_RANS_SST",
        "Uz_RANS_SST",
        "Up_RANS_SST",
        "Ux_LES",
        "Uy_LES",
        "Uz_LES",
        "Up_LES",
        "Ux_over_Ub_RANS_SST",
        "Ux_over_Ub_LES",
        "Up_over_Ub_RANS_SST",
        "Up_over_Ub_LES",
    ]

    rows: list[list[float]] = []
    for i in range(len(r)):
        if not np.isfinite(les_interp["Ux_over_Ub"][i]) or not np.isfinite(
            les_interp["Up_over_Ub"][i]
        ):
            continue

        rows.append(
            [
                rans["r_over_h"][i],
                rans["x"][i],
                rans["y"][i],
                rans["z"][i],
                rans["Ux"][i],
                rans["Uy"][i],
                rans["Uz"][i],
                rans["Up"][i],
                les_interp["Ux"][i],
                les_interp["Uy"][i],
                les_interp["Uz"][i],
                les_interp["Up"][i],
                rans["Ux_over_Ub"][i],
                les_interp["Ux_over_Ub"][i],
                rans["Up_over_Ub"][i],
                les_interp["Up_over_Ub"][i],
            ]
        )

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(header)
        writer.writerows(rows)

    return len(rows)


def plot_profile(
    out_path: Path,
    rans: dict[str, np.ndarray],
    les: dict[str, np.ndarray],
    key: str,
    ylabel: str,
    title: str,
) -> None:
    """Plot one normalized diagonal profile."""
    trim_zeros = FuncFormatter(lambda value, _: f"{value:g}")

    fig, ax = plt.subplots(figsize=(7.4, 5.2))
    ax.plot(
        les["r_over_h"],
        les[key],
        color="black",
        marker="o",
        markersize=4.0,
        linewidth=1.3,
        label=LES_LABEL,
    )
    ax.plot(
        rans["r_over_h"],
        rans[key],
        color="#1f77b4",
        linestyle="--",
        linewidth=2.0,
        label=RANS_LABEL,
    )
    ax.set_xlabel(r"$r/h$")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.xaxis.set_major_formatter(trim_zeros)
    ax.yaxis.set_major_formatter(trim_zeros)
    ax.grid(True, alpha=0.3)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def run_comparison(root_dir: Path | str | None = None) -> dict[str, Path]:
    """Generate Square Duct diagonal plots and profile CSV."""
    root = Path(root_dir) if root_dir is not None else Path(__file__).resolve().parent
    root = root.resolve()

    case_def = read_case_def(root / "caseDef")
    h = case_def["h"]
    re_b = case_def["Re_b"]
    nu = case_def["nu"]
    u_b = re_b * nu / h

    rans_file = find_latest_diag_file(
        root / "00Baseline" / "beta11", ["line_U.xy", "line_U_LES.xy"]
    )
    les_file = find_latest_diag_file(
        root / "01Frozen" / "beta11", ["line_U_LES.xy", "line_U.xy"]
    )
    if rans_file is None:
        raise FileNotFoundError("Could not find baseline diagonal velocity file.")
    if les_file is None:
        raise FileNotFoundError("Could not find LES diagonal velocity file.")

    rans = make_profile(load_velocity_file(rans_file), h, u_b)
    les = make_profile(load_velocity_file(les_file), h, u_b)

    out_dir = root / "Figures"
    out_dir.mkdir(parents=True, exist_ok=True)

    ux_pdf = out_dir / f"compareUxProfiles_{CASE_TAG}.pdf"
    up_pdf = out_dir / f"compareUpProfiles_{CASE_TAG}.pdf"
    csv_path = out_dir / f"velocity_diagonal_profiles_{CASE_TAG}.csv"

    title = f"Square duct AR=1, Re_tau={case_def.get('Re_tau', 180):g}, Ub={u_b:g}"
    plot_profile(
        ux_pdf,
        rans,
        les,
        "Ux_over_Ub",
        r"$U_x/U_b$",
        title,
    )
    plot_profile(
        up_pdf,
        rans,
        les,
        "Up_over_Ub",
        r"$\sqrt{U_y^2 + U_z^2}/U_b$",
        title,
    )
    row_count = write_profiles_csv(csv_path, rans, les)

    print(f"RANS(SST) source: {rans_file}")
    print(f"LES source: {les_file}")
    print(f"Ub = {u_b:g}")
    print(f"Wrote: {ux_pdf}")
    print(f"Wrote: {up_pdf}")
    print(f"Wrote: {csv_path} ({row_count} rows)")

    return {"Ux": ux_pdf, "Up": up_pdf, "csv": csv_path}


def main() -> None:
    run_comparison()


if __name__ == "__main__":
    main()
