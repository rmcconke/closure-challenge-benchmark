#!/usr/bin/env python3
"""Plot postProcessing outputs for residuals, convergence probes, wall shear stress,
and Ux profile along the diagonal.

This script reads OpenFOAM postProcessing files from the local case folder and writes
figures into a sibling folder named ``figures``.
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

TOKEN_PATTERN = re.compile(r"\([^)]+\)|\S+")
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
    """Return sorted time directories by numeric name if possible."""
    if not base_dir.exists():
        return []

    def key_fn(path: Path) -> tuple[int, float | str]:
        try:
            return (0, float(path.name))
        except ValueError:
            return (1, path.name)

    return sorted([p for p in base_dir.iterdir() if p.is_dir()], key=key_fn)


def parse_float(value: str) -> float:
    """Parse a float safely; returns NaN for non-numeric entries."""
    try:
        return float(value)
    except ValueError:
        return float("nan")


def parse_vector(token: str) -> np.ndarray:
    """Parse an OpenFOAM vector like '(1 2 3)'."""
    token = token.strip()
    if not (token.startswith("(") and token.endswith(")")):
        raise ValueError(f"Not a vector token: {token}")
    return np.array([float(x) for x in token[1:-1].split()], dtype=float)


def tokenize_line(line: str) -> list[str]:
    """Split a line while keeping parenthesized vectors as one token."""
    return TOKEN_PATTERN.findall(line.strip())


def parse_residual_file(file_path: Path) -> tuple[list[str], np.ndarray, np.ndarray]:
    """Parse one residuals.dat file."""
    column_names: list[str] = []
    times: list[float] = []
    rows: list[list[float]] = []

    with file_path.open("r", encoding="utf-8", errors="ignore") as f:
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
            if not tokens:
                continue

            time_val = parse_float(tokens[0])
            values = [parse_float(v) for v in tokens[1:]]

            if not column_names:
                column_names = [f"col_{i + 1}" for i in range(len(values))]

            if len(values) < len(column_names):
                values.extend([float("nan")] * (len(column_names) - len(values)))
            elif len(values) > len(column_names):
                values = values[: len(column_names)]

            times.append(time_val)
            rows.append(values)

    if not rows:
        return column_names, np.array([]), np.empty((0, 0))

    return column_names, np.array(times, dtype=float), np.array(rows, dtype=float)


def load_residuals(post_dir: Path) -> tuple[list[str], np.ndarray, np.ndarray]:
    """Load residual data across all residual directories."""
    residual_bases = [post_dir / "residuals", post_dir / "residules"]
    column_names: list[str] | None = None
    all_times: list[np.ndarray] = []
    all_values: list[np.ndarray] = []

    for base in residual_bases:
        for time_dir in sorted_time_dirs(base):
            file_path = time_dir / "residuals.dat"
            if not file_path.exists():
                continue

            names, times, values = parse_residual_file(file_path)
            if times.size == 0:
                continue

            if column_names is None:
                column_names = names
            if values.shape[1] != len(column_names):
                continue

            all_times.append(times)
            all_values.append(values)

    if not all_times:
        return [], np.array([]), np.empty((0, 0))

    times = np.concatenate(all_times)
    values = np.concatenate(all_values, axis=0)
    order = np.argsort(times)
    times = times[order]
    values = values[order]

    unique_times, unique_indices = np.unique(times[::-1], return_index=True)
    keep = np.sort(times.size - 1 - unique_indices)
    _ = unique_times
    return column_names or [], times[keep], values[keep]


def build_probe_labels(
    probe_ids: list[str],
    probe_coords: dict[int, tuple[float, float, float]],
    h: float,
) -> list[str]:
    """Build readable probe labels with coordinates when available."""
    labels: list[str] = []
    for idx, probe_id in enumerate(probe_ids):
        probe_index = idx
        try:
            probe_index = int(probe_id)
        except ValueError:
            pass

        coords = probe_coords.get(probe_index)
        if coords is None:
            labels.append(f"Probe {probe_id}")
        else:
            x, y, z = coords
            labels.append(f"Probe {probe_id} ({x / h:.4g}, {y / h:.4g}, {z / h:.4g})")
    return labels


def parse_probe_file(
    file_path: Path, h: float
) -> tuple[list[str], list[str], np.ndarray, np.ndarray, bool]:
    """Parse one convergenceProbes file.

    Returns:
        probe_ids, probe_labels, times, data, is_vector
    where data shape is:
        - scalar: (n_time, n_probe)
        - vector: (n_time, n_probe, n_comp)
    """
    probe_ids: list[str] = []
    probe_coords: dict[int, tuple[float, float, float]] = {}
    times: list[float] = []
    rows: list[np.ndarray] = []
    is_vector: bool | None = None
    n_components = 1

    with file_path.open("r", encoding="utf-8", errors="ignore") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue

            if line.startswith("#"):
                header = line.lstrip("#").strip()
                probe_match = PROBE_HEADER_PATTERN.match(header)
                if probe_match:
                    try:
                        probe_idx = int(probe_match.group(1))
                        coord_vals = [float(v) for v in probe_match.group(2).split()]
                        if len(coord_vals) >= 3:
                            probe_coords[probe_idx] = (
                                coord_vals[0],
                                coord_vals[1],
                                coord_vals[2],
                            )
                    except ValueError:
                        pass
                if header.startswith("Time"):
                    tokens = header.split()
                    probe_ids = tokens[1:]
                continue

            tokens = tokenize_line(line)
            if len(tokens) < 2:
                continue

            time_val = parse_float(tokens[0])
            value_tokens = tokens[1:]

            if not probe_ids:
                probe_ids = [str(i) for i in range(len(value_tokens))]

            if len(value_tokens) < len(probe_ids):
                value_tokens.extend(["nan"] * (len(probe_ids) - len(value_tokens)))
            elif len(value_tokens) > len(probe_ids):
                value_tokens = value_tokens[: len(probe_ids)]

            row_values: list[np.ndarray | float] = []
            row_is_vector = False
            for tok in value_tokens:
                tok = tok.strip()
                if tok.startswith("(") and tok.endswith(")"):
                    row_values.append(parse_vector(tok))
                    row_is_vector = True
                else:
                    row_values.append(parse_float(tok))

            if is_vector is None:
                is_vector = row_is_vector
                if is_vector:
                    for item in row_values:
                        if isinstance(item, np.ndarray):
                            n_components = item.size
                            break

            if is_vector:
                vec_row = np.full((len(probe_ids), n_components), np.nan, dtype=float)
                for i, item in enumerate(row_values):
                    if isinstance(item, np.ndarray):
                        vec_row[i, : min(n_components, item.size)] = item[:n_components]
                    else:
                        vec_row[i, :] = float("nan")
                rows.append(vec_row)
            else:
                scalar_row = np.full(len(probe_ids), np.nan, dtype=float)
                for i, item in enumerate(row_values):
                    if not isinstance(item, np.ndarray):
                        scalar_row[i] = item
                rows.append(scalar_row)

            times.append(time_val)

    if not rows:
        return (
            probe_ids,
            build_probe_labels(probe_ids, probe_coords, h),
            np.array([]),
            np.empty((0, 0)),
            False,
        )

    data = np.array(rows, dtype=float)
    return (
        probe_ids,
        build_probe_labels(probe_ids, probe_coords, h),
        np.array(times, dtype=float),
        data,
        bool(is_vector),
    )


def load_convergence_probes(
    post_dir: Path,
    h: float,
) -> dict[str, tuple[list[str], list[str], np.ndarray, np.ndarray, bool]]:
    """Load and merge all convergence probe files by field name."""
    base_dir = post_dir / "convergenceProbes"
    if not base_dir.exists():
        return {}

    grouped_files: dict[str, list[Path]] = {}
    for time_dir in sorted_time_dirs(base_dir):
        for file_path in sorted(time_dir.iterdir()):
            if file_path.is_file():
                grouped_files.setdefault(file_path.name, []).append(file_path)

    merged: dict[str, tuple[list[str], list[str], np.ndarray, np.ndarray, bool]] = {}
    for field, files in grouped_files.items():
        field_probe_ids: list[str] = []
        field_probe_labels: list[str] = []
        field_times: list[np.ndarray] = []
        field_data: list[np.ndarray] = []
        field_is_vector: bool | None = None

        for file_path in files:
            probe_ids, probe_labels, times, data, is_vector = parse_probe_file(file_path, h)
            if times.size == 0:
                continue

            if not field_probe_ids:
                field_probe_ids = probe_ids
                field_probe_labels = probe_labels
                field_is_vector = is_vector

            if is_vector != field_is_vector:
                continue

            if len(probe_ids) != len(field_probe_ids):
                continue

            field_times.append(times)
            field_data.append(data)

        if not field_times:
            continue

        times = np.concatenate(field_times)
        data = np.concatenate(field_data, axis=0)
        order = np.argsort(times)
        times = times[order]
        data = data[order]

        _, unique_indices = np.unique(times[::-1], return_index=True)
        keep = np.sort(times.size - 1 - unique_indices)
        merged[field] = (
            field_probe_ids,
            field_probe_labels,
            times[keep],
            data[keep],
            bool(field_is_vector),
        )

    return merged


def get_probe_label(probe_idx: int, probe_ids: list[str], probe_labels: list[str]) -> str:
    """Return preferred probe label, falling back to probe ID."""
    if probe_idx < len(probe_labels):
        return probe_labels[probe_idx]
    if probe_idx < len(probe_ids):
        return f"Probe {probe_ids[probe_idx]}"
    return f"Probe {probe_idx}"


def parse_wall_shear_file(
    file_path: Path,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Parse one wallShearStress.dat file."""
    times: list[float] = []
    patches: list[str] = []
    mins: list[np.ndarray] = []
    maxs: list[np.ndarray] = []

    with file_path.open("r", encoding="utf-8", errors="ignore") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            tokens = tokenize_line(line)
            if len(tokens) < 4:
                continue

            try:
                min_vec = parse_vector(tokens[2])
                max_vec = parse_vector(tokens[3])
            except ValueError:
                continue

            times.append(parse_float(tokens[0]))
            patches.append(tokens[1])
            mins.append(min_vec)
            maxs.append(max_vec)

    if not times:
        return np.array([]), np.array([]), np.empty((0, 0)), np.empty((0, 0))

    return (
        np.array(times, dtype=float),
        np.array(patches, dtype=object),
        np.array(mins, dtype=float),
        np.array(maxs, dtype=float),
    )


def load_wall_shear(
    post_dir: Path,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Load and merge wallShearStress data across time folders."""
    base_dir = post_dir / "wallShearStress"
    all_times: list[np.ndarray] = []
    all_patches: list[np.ndarray] = []
    all_mins: list[np.ndarray] = []
    all_maxs: list[np.ndarray] = []

    for time_dir in sorted_time_dirs(base_dir):
        file_path = time_dir / "wallShearStress.dat"
        if not file_path.exists():
            continue

        times, patches, mins, maxs = parse_wall_shear_file(file_path)
        if times.size == 0:
            continue

        all_times.append(times)
        all_patches.append(patches)
        all_mins.append(mins)
        all_maxs.append(maxs)

    if not all_times:
        return np.array([]), np.array([]), np.empty((0, 0)), np.empty((0, 0))

    times = np.concatenate(all_times)
    patches = np.concatenate(all_patches)
    mins = np.concatenate(all_mins, axis=0)
    maxs = np.concatenate(all_maxs, axis=0)

    order = np.argsort(times)
    return times[order], patches[order], mins[order], maxs[order]


def parse_line_u_file(file_path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Parse line_U.xy and return diagonal distance and Ux."""
    coords: list[np.ndarray] = []
    ux_values: list[float] = []

    with file_path.open("r", encoding="utf-8", errors="ignore") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            tokens = line.split()
            if len(tokens) < 6:
                continue

            values = [parse_float(tok) for tok in tokens[:6]]
            if any(np.isnan(v) for v in values):
                continue

            coords.append(np.array(values[:3], dtype=float))
            ux_values.append(values[3])

    if not coords:
        return np.array([]), np.array([])

    coord_arr = np.array(coords, dtype=float)
    ux_arr = np.array(ux_values, dtype=float)
    diagonal_distance = np.linalg.norm(coord_arr - coord_arr[0], axis=1)

    order = np.argsort(diagonal_distance)
    return diagonal_distance[order], ux_arr[order]


def load_diag_ux_profiles(post_dir: Path) -> list[tuple[str, float, np.ndarray, np.ndarray]]:
    """Load Ux profiles from all singleGraphDiag time folders."""
    base_dir = post_dir / "singleGraphDiag"
    profiles: list[tuple[str, float, np.ndarray, np.ndarray]] = []

    for time_dir in sorted_time_dirs(base_dir):
        file_path = time_dir / "line_U.xy"
        if not file_path.exists():
            continue

        distance, ux = parse_line_u_file(file_path)
        if distance.size == 0:
            continue

        try:
            time_value = float(time_dir.name)
        except ValueError:
            time_value = float("nan")
        profiles.append((time_dir.name, time_value, distance, ux))

    profiles.sort(key=lambda item: (np.isnan(item[1]), item[1], item[0]))
    return profiles


def plot_residuals(post_dir: Path, figures_dir: Path) -> list[Path]:
    """Create residual plots."""
    column_names, times, values = load_residuals(post_dir)
    if times.size == 0 or values.size == 0:
        return []

    fig, ax = plt.subplots(figsize=(10, 6))
    plotted_any = False

    for i, name in enumerate(column_names):
        y = values[:, i]
        mask = np.isfinite(y) & (y > 0.0)
        if mask.any():
            ax.semilogy(times[mask], y[mask], label=name)
            plotted_any = True

    if not plotted_any:
        plt.close(fig)
        return []

    ax.set_title("Residuals")
    ax.set_xlabel("Time / Iteration")
    ax.set_ylabel("Residual")
    ax.grid(True, which="both", linestyle="--", alpha=0.35)
    ax.legend(loc="best")
    fig.tight_layout()

    out_file = figures_dir / "residuals.png"
    fig.savefig(out_file, dpi=200)
    plt.close(fig)
    return [out_file]


def plot_convergence_probes(post_dir: Path, figures_dir: Path, h: float) -> list[Path]:
    """Create plots for all convergenceProbes fields."""
    all_fields = load_convergence_probes(post_dir, h)
    saved_files: list[Path] = []

    for field_name in sorted(all_fields):
        probe_ids, probe_labels, times, data, is_vector = all_fields[field_name]
        if times.size == 0 or data.size == 0:
            continue

        if is_vector:
            n_comp = data.shape[2]
            comp_names = ["x", "y", "z"][:n_comp]
            magnitudes = np.linalg.norm(data, axis=2)

            fig, axes = plt.subplots(2, 2, figsize=(13, 8), sharex=True)
            flat_axes = axes.flatten()

            for comp_idx in range(min(3, n_comp)):
                ax = flat_axes[comp_idx]
                for probe_idx in range(len(probe_ids)):
                    ax.plot(
                        times,
                        data[:, probe_idx, comp_idx],
                        label=get_probe_label(probe_idx, probe_ids, probe_labels),
                    )
                ax.set_title(f"{field_name} ({comp_names[comp_idx]})")
                ax.grid(True, linestyle="--", alpha=0.35)
                ax.set_ylabel(field_name)

            ax_mag = flat_axes[3]
            for probe_idx in range(len(probe_ids)):
                ax_mag.plot(
                    times,
                    magnitudes[:, probe_idx],
                    label=get_probe_label(probe_idx, probe_ids, probe_labels),
                )
            ax_mag.set_title(f"{field_name} (magnitude)")
            ax_mag.grid(True, linestyle="--", alpha=0.35)
            ax_mag.set_ylabel(f"|{field_name}|")

            for ax in flat_axes:
                ax.set_xlabel("Time / Iteration")

            flat_axes[0].legend(loc="best", fontsize=8)
            fig.suptitle(f"convergenceProbes: {field_name}", fontsize=13)
            fig.tight_layout(rect=(0, 0, 1, 0.97))
        else:
            fig, ax = plt.subplots(figsize=(10, 6))
            for probe_idx in range(len(probe_ids)):
                ax.plot(
                    times,
                    data[:, probe_idx],
                    label=get_probe_label(probe_idx, probe_ids, probe_labels),
                )
            ax.set_title(f"convergenceProbes: {field_name}")
            ax.set_xlabel("Time / Iteration")
            ax.set_ylabel(field_name)
            ax.grid(True, linestyle="--", alpha=0.35)
            ax.legend(loc="best")
            fig.tight_layout()

        out_file = figures_dir / f"convergenceProbes_{field_name}.png"
        fig.savefig(out_file, dpi=200)
        plt.close(fig)
        saved_files.append(out_file)

    return saved_files


def plot_wall_shear(post_dir: Path, figures_dir: Path) -> list[Path]:
    """Create wall shear stress min/max magnitude plot by patch."""
    times, patches, mins, maxs = load_wall_shear(post_dir)
    if times.size == 0 or mins.size == 0 or maxs.size == 0:
        return []

    min_mag = np.linalg.norm(mins, axis=1)
    max_mag = np.linalg.norm(maxs, axis=1)

    fig, ax = plt.subplots(figsize=(10, 6))
    for patch in sorted(set(patches.tolist())):
        patch_mask = patches == patch
        patch_times = times[patch_mask]
        patch_min = min_mag[patch_mask]
        patch_max = max_mag[patch_mask]

        order = np.argsort(patch_times)
        patch_times = patch_times[order]
        patch_min = patch_min[order]
        patch_max = patch_max[order]

        linestyle_min = "-" if patch_times.size > 1 else "None"
        linestyle_max = "--" if patch_times.size > 1 else "None"
        ax.plot(
            patch_times,
            patch_min,
            marker="o",
            linestyle=linestyle_min,
            label=f"{patch} |min|",
        )
        ax.plot(
            patch_times,
            patch_max,
            marker="s",
            linestyle=linestyle_max,
            label=f"{patch} |max|",
        )

    ax.set_title("Wall Shear Stress Magnitude")
    ax.set_xlabel("Time / Iteration")
    ax.set_ylabel("|tau_w|")
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.legend(loc="best")
    fig.tight_layout()

    out_file = figures_dir / "wallShearStress_minmax.png"
    fig.savefig(out_file, dpi=200)
    plt.close(fig)
    return [out_file]


def plot_ux_diagonal_profile(
    post_dir: Path,
    figures_dir: Path,
    h: float,
    u_b: float,
) -> list[Path]:
    """Create Ux profile plot along diagonal from singleGraphDiag."""
    profiles = load_diag_ux_profiles(post_dir)
    if not profiles:
        return []

    fig, ax = plt.subplots(figsize=(10, 6))
    last_idx = len(profiles) - 1
    for idx, (time_label, _, distance, ux) in enumerate(profiles):
        distance_over_h = distance / h
        ux_over_ub = ux / u_b
        if idx == last_idx:
            ax.plot(
                distance_over_h,
                ux_over_ub,
                linewidth=2.4,
                label=f"time {time_label} (latest)",
            )
        else:
            ax.plot(
                distance_over_h,
                ux_over_ub,
                alpha=0.65,
                linewidth=1.2,
                label=f"time {time_label}",
            )

    ax.set_title("Ux Profile Along Diagonal")
    ax.set_xlabel("r/h")
    ax.set_ylabel(r"$U_x/U_b$")
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.legend(loc="best")
    fig.tight_layout()

    out_file = figures_dir / "Ux_profile_diagonal.png"
    fig.savefig(out_file, dpi=200)
    plt.close(fig)
    return [out_file]


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
    generated.extend(plot_residuals(post_dir, figures_dir))
    generated.extend(plot_convergence_probes(post_dir, figures_dir, h))
    generated.extend(plot_wall_shear(post_dir, figures_dir))
    generated.extend(plot_ux_diagonal_profile(post_dir, figures_dir, h, u_b))

    if generated:
        print("Generated figures:")
        for file_path in generated:
            print(f" - {file_path}")
    else:
        print(f"No valid postProcessing data found under: {post_dir}")


if __name__ == "__main__":
    main()
