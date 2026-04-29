#!/usr/bin/env python3
"""Post-processing plots for 01Frozen beta11.

Requested outputs:
1. Diagonal Ux profile
2. Diagonal Up profile, where Up = sqrt(Uy^2 + Uz^2)
3. Residual of omega
4. Convergence probes of omega
"""

from __future__ import annotations

import os
import re
from pathlib import Path

# Avoid Matplotlib cache warnings when ~/.config/matplotlib is not writable.
if "MPLCONFIGDIR" not in os.environ:
    default_mpl_dir = Path.home() / ".config" / "matplotlib"
    if not (default_mpl_dir.exists() and os.access(default_mpl_dir, os.W_OK)):
        os.environ["MPLCONFIGDIR"] = f"/tmp/matplotlib-{os.getuid()}"

import matplotlib.pyplot as plt
import numpy as np

PROBE_HEADER_PATTERN = re.compile(r"^Probe\s+(\d+)\s+\(([^)]+)\)")


def read_case_def(case_def_path: Path) -> dict[str, float]:
    """Read scalar values from OpenFOAM-style caseDef file."""
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

            key = match.group(1)
            val_str = match.group(2).strip()
            try:
                values[key] = float(val_str)
            except ValueError:
                continue

    return values


def sorted_time_dirs(base_dir: Path) -> list[Path]:
    """Return time directories sorted numerically when possible."""
    if not base_dir.exists():
        return []

    def key_fn(path: Path) -> tuple[int, float | str]:
        try:
            return (0, float(path.name))
        except ValueError:
            return (1, path.name)

    return sorted([p for p in base_dir.iterdir() if p.is_dir()], key=key_fn)


def parse_float(value: str) -> float:
    """Parse float safely; returns NaN if parsing fails."""
    try:
        return float(value)
    except ValueError:
        return float("nan")


def find_latest_file(base_dir: Path, filename_candidates: list[str]) -> tuple[Path, str]:
    """Find the latest available file among time directories."""
    latest_path: Path | None = None
    latest_time: str = ""

    for time_dir in sorted_time_dirs(base_dir):
        for filename in filename_candidates:
            candidate = time_dir / filename
            if candidate.exists():
                latest_path = candidate
                latest_time = time_dir.name

    if latest_path is None:
        raise FileNotFoundError(f"Could not find {filename_candidates} under {base_dir}")

    return latest_path, latest_time


def load_diag_u_profiles(post_dir: Path) -> tuple[str, np.ndarray, np.ndarray, np.ndarray, Path]:
    """Load latest line_U_LES.xy and return distance, Ux, Up."""
    base_dir = post_dir / "singleGraphDiag"
    line_file, time_label = find_latest_file(base_dir, ["line_U_LES.xy", "line_U.xy"])

    data = np.loadtxt(line_file)
    if data.ndim == 1:
        data = data[np.newaxis, :]
    if data.shape[1] < 6:
        raise ValueError(f"Expected >= 6 columns in {line_file}, got {data.shape[1]}")

    coords = data[:, :3]
    ux = data[:, 3]
    uy = data[:, 4]
    uz = data[:, 5]
    up = np.sqrt(uy**2 + uz**2)

    distance = np.linalg.norm(coords - coords[0], axis=1)
    order = np.argsort(distance)
    return time_label, distance[order], ux[order], up[order], line_file


def load_omega_residual(post_dir: Path) -> tuple[np.ndarray, np.ndarray, Path]:
    """Load omega residual from residuals.dat."""
    base_dir = post_dir / "residuals"
    residual_file, _ = find_latest_file(base_dir, ["residuals.dat"])

    column_names: list[str] = []
    times: list[float] = []
    omega_values: list[float] = []

    with residual_file.open("r", encoding="utf-8", errors="ignore") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue

            if line.startswith("#"):
                header = line.lstrip("#").strip()
                tokens = header.split()
                if tokens and tokens[0] == "Time":
                    column_names = tokens[1:]
                continue

            tokens = line.split()
            if len(tokens) < 2:
                continue

            time_val = parse_float(tokens[0])
            values = [parse_float(v) for v in tokens[1:]]
            if np.isnan(time_val):
                continue

            omega_idx = 0
            if column_names and "omega" in column_names:
                omega_idx = column_names.index("omega")

            if omega_idx >= len(values):
                continue

            omega_val = values[omega_idx]
            times.append(time_val)
            omega_values.append(omega_val)

    if not times:
        return np.array([]), np.array([]), residual_file

    return np.array(times, dtype=float), np.array(omega_values, dtype=float), residual_file


def load_omega_probe(post_dir: Path, h: float) -> tuple[np.ndarray, np.ndarray, list[str], Path]:
    """Load omega convergence probe file."""
    base_dir = post_dir / "convergenceProbes"
    probe_file, _ = find_latest_file(base_dir, ["omega"])

    probe_ids: list[str] = []
    probe_coords: dict[int, tuple[float, float, float]] = {}
    times: list[float] = []
    rows: list[list[float]] = []

    with probe_file.open("r", encoding="utf-8", errors="ignore") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue

            if line.startswith("#"):
                header = line.lstrip("#").strip()
                match = PROBE_HEADER_PATTERN.match(header)
                if match:
                    idx = int(match.group(1))
                    parts = [float(v) for v in match.group(2).split()]
                    if len(parts) >= 3:
                        probe_coords[idx] = (parts[0], parts[1], parts[2])
                elif header.startswith("Time"):
                    tokens = header.split()
                    probe_ids = tokens[1:]
                continue

            tokens = line.split()
            if len(tokens) < 2:
                continue

            time_val = parse_float(tokens[0])
            value_tokens = tokens[1:]
            values = [parse_float(v) for v in value_tokens]

            if not probe_ids:
                probe_ids = [str(i) for i in range(len(values))]

            if len(values) < len(probe_ids):
                values.extend([float("nan")] * (len(probe_ids) - len(values)))
            elif len(values) > len(probe_ids):
                values = values[: len(probe_ids)]

            if np.isnan(time_val):
                continue
            times.append(time_val)
            rows.append(values)

    if not times:
        return np.array([]), np.empty((0, 0)), [], probe_file

    labels: list[str] = []
    for i, probe_id in enumerate(probe_ids):
        try:
            probe_index = int(probe_id)
        except ValueError:
            probe_index = i
        coords = probe_coords.get(probe_index)
        if coords is None:
            labels.append(f"Probe {probe_id}")
        else:
            x, y, z = coords
            labels.append(
                f"Probe {probe_id} ({x / h:.4g}, {y / h:.4g}, {z / h:.4g})"
            )

    return (
        np.array(times, dtype=float),
        np.array(rows, dtype=float),
        labels,
        probe_file,
    )


def plot_diag_ux(
    figures_dir: Path,
    time_label: str,
    distance_over_h: np.ndarray,
    ux_over_ub: np.ndarray,
) -> Path | None:
    """Plot diagonal Ux profile."""
    if distance_over_h.size == 0 or ux_over_ub.size == 0:
        return None

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(
        distance_over_h,
        ux_over_ub,
        color="tab:blue",
        linewidth=2.0,
        label=f"time {time_label}",
    )
    ax.set_title("Diagonal Ux Profile (01Frozen)")
    ax.set_xlabel("r/h")
    ax.set_ylabel(r"$U_x/U_b$")
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.legend(loc="best")
    fig.tight_layout()

    out_file = figures_dir / "Ux_profile_diagonal.png"
    fig.savefig(out_file, dpi=200)
    plt.close(fig)
    return out_file


def plot_diag_up(
    figures_dir: Path,
    time_label: str,
    distance_over_h: np.ndarray,
    up_over_ub: np.ndarray,
) -> Path | None:
    """Plot diagonal Up profile."""
    if distance_over_h.size == 0 or up_over_ub.size == 0:
        return None

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(
        distance_over_h,
        up_over_ub,
        color="tab:orange",
        linewidth=2.0,
        label=f"time {time_label}",
    )
    ax.set_title("Diagonal Up Profile (01Frozen)")
    ax.set_xlabel("r/h")
    ax.set_ylabel(r"$\sqrt{U_y^2 + U_z^2}/U_b$")
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.legend(loc="best")
    fig.tight_layout()

    out_file = figures_dir / "Up_profile_diagonal.png"
    fig.savefig(out_file, dpi=200)
    plt.close(fig)
    return out_file


def plot_omega_residual(figures_dir: Path, times: np.ndarray, omega: np.ndarray) -> Path | None:
    """Plot omega residual history."""
    if times.size == 0 or omega.size == 0:
        return None

    mask = np.isfinite(omega) & (omega > 0.0)
    if not mask.any():
        return None

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.semilogy(times[mask], omega[mask], color="tab:green", linewidth=2.0)
    ax.set_title("Omega Residual (01Frozen)")
    ax.set_xlabel("Time / Iteration")
    ax.set_ylabel("Residual (omega)")
    ax.grid(True, which="both", linestyle="--", alpha=0.35)
    fig.tight_layout()

    out_file = figures_dir / "residual_omega.png"
    fig.savefig(out_file, dpi=200)
    plt.close(fig)
    return out_file


def plot_omega_probe(
    figures_dir: Path, times: np.ndarray, values: np.ndarray, labels: list[str]
) -> Path | None:
    """Plot omega convergence probes."""
    if times.size == 0 or values.size == 0:
        return None

    fig, ax = plt.subplots(figsize=(11, 7))
    n_probe = values.shape[1]
    for i in range(n_probe):
        label = labels[i] if i < len(labels) else f"Probe {i}"
        ax.plot(times, values[:, i], linewidth=1.8, label=label)

    ax.set_title("Omega Convergence Probes (01Frozen)")
    ax.set_xlabel("Time / Iteration")
    ax.set_ylabel("omega")
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()

    out_file = figures_dir / "convergenceProbes_omega.png"
    fig.savefig(out_file, dpi=200)
    plt.close(fig)
    return out_file


def main() -> None:
    case_dir = Path(__file__).resolve().parent
    case_def = read_case_def(case_dir / "caseDef")
    h = case_def["h"]
    re_b = case_def["Re_b"]
    nu = case_def["nu"]
    u_b = re_b * nu / h

    post_dir = case_dir / "postProcessing"
    figures_dir = case_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    generated: list[Path] = []

    time_label, distance, ux, up, u_source = load_diag_u_profiles(post_dir)
    out = plot_diag_ux(figures_dir, time_label, distance / h, ux / u_b)
    if out is not None:
        generated.append(out)

    out = plot_diag_up(figures_dir, time_label, distance / h, up / u_b)
    if out is not None:
        generated.append(out)

    residual_times, omega_residual, residual_source = load_omega_residual(post_dir)
    out = plot_omega_residual(figures_dir, residual_times, omega_residual)
    if out is not None:
        generated.append(out)

    probe_times, probe_values, probe_labels, probe_source = load_omega_probe(post_dir, h)
    out = plot_omega_probe(figures_dir, probe_times, probe_values, probe_labels)
    if out is not None:
        generated.append(out)

    if generated:
        print("Generated figures:")
        for fig_path in generated:
            print(f" - {fig_path}")
        print(f"Diagonal profile source: {u_source}")
        print(f"Residual source: {residual_source}")
        print(f"Omega probe source: {probe_source}")
        print(f"Normalization constants: h={h:.8g}, U_b={u_b:.8g}")
    else:
        print(f"No requested postProcessing data found under: {post_dir}")


if __name__ == "__main__":
    main()
