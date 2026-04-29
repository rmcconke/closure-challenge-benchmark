#!/usr/bin/env python3
"""Post-process and plot key 01Frozen diagnostics for Periodic Hill Re_10595.

Outputs are written into ``./figures``:
  - residuals.png
  - profiles_Ux.png
  - profiles_k_omega.png
  - wallShearStress_minmax.png
  - shearStress_profile_bottom_top.png
  - Cf_profile_bottom_top.png
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

# Avoid Matplotlib cache warnings when ~/.config/matplotlib is not writable.
if "MPLCONFIGDIR" not in os.environ:
    default_mpl_dir = Path.home() / ".config" / "matplotlib"
    if not (default_mpl_dir.exists() and os.access(default_mpl_dir, os.W_OK)):
        os.environ["MPLCONFIGDIR"] = f"/tmp/matplotlib-{os.getuid()}"

import matplotlib.pyplot as plt
import numpy as np

TOKEN_PATTERN = re.compile(r"\([^)]+\)|\S+")


def parse_float(value: str) -> float:
    try:
        return float(value)
    except ValueError:
        return float("nan")


def parse_vector(token: str) -> np.ndarray:
    token = token.strip()
    if not (token.startswith("(") and token.endswith(")")):
        raise ValueError(f"Not a vector token: {token}")
    return np.array([float(x) for x in token[1:-1].split()], dtype=float)


def tokenize_line(line: str) -> list[str]:
    return TOKEN_PATTERN.findall(line.strip())


def sorted_time_dirs(base_dir: Path) -> list[Path]:
    if not base_dir.exists():
        return []

    def key_fn(path: Path) -> tuple[int, float | str]:
        try:
            return (0, float(path.name))
        except ValueError:
            return (1, path.name)

    return sorted([p for p in base_dir.iterdir() if p.is_dir()], key=key_fn)


def invocation_case_dir() -> Path:
    """Return directory of the script path used at invocation time.

    Keeps symlink semantics by avoiding resolve(), so running a symlinked
    script behaves relative to the symlink location.
    """
    argv0 = sys.argv[0] if sys.argv else ""
    if not argv0 or argv0 in {"-c", "-m"}:
        return Path(__file__).parent
    return Path(argv0).expanduser().absolute().parent


def read_case_def(case_dir: Path) -> dict[str, float]:
    """Read OpenFOAM-style scalar definitions from caseDef."""
    possible_paths = [case_dir / "caseDef", case_dir.parent / "caseDef"]
    case_def_path = next((p for p in possible_paths if p.exists()), None)
    if case_def_path is None:
        return {}

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


def read_ubar(case_dir: Path) -> float | None:
    """Read target bulk velocity Ubar from fvOptions, if available."""
    possible_paths = [
        case_dir / "constant" / "fvOptions",
        case_dir / "system" / "fvOptions",
        case_dir.parent / "Common" / "constant" / "fvOptions",
        case_dir.parent / "Common" / "system" / "fvOptions",
    ]
    fv_path = next((p for p in possible_paths if p.exists()), None)
    if fv_path is None:
        return None

    # Example line: Ubar        (0.72 0 0);
    pattern = re.compile(r"^\s*Ubar\s*\(\s*([^)]+)\)\s*;")
    with fv_path.open("r", encoding="utf-8", errors="ignore") as handle:
        for raw_line in handle:
            line = raw_line.split("//", 1)[0].strip()
            if not line:
                continue
            match = pattern.match(line)
            if not match:
                continue
            vals = [parse_float(tok) for tok in match.group(1).split()]
            if not vals:
                return None
            # Streamwise bulk velocity target
            return float(vals[0])

    return None


def parse_residual_file(file_path: Path) -> tuple[list[str], np.ndarray, np.ndarray]:
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
            if not values:
                continue

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
    base_dir = post_dir / "residuals"
    all_times: list[np.ndarray] = []
    all_values: list[np.ndarray] = []
    colnames: list[str] | None = None

    for time_dir in sorted_time_dirs(base_dir):
        file_path = time_dir / "residuals.dat"
        if not file_path.exists():
            continue

        names, times, values = parse_residual_file(file_path)
        if times.size == 0:
            continue

        if colnames is None:
            colnames = names
        if values.shape[1] != len(colnames):
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

    # keep last occurrence for duplicate iteration entries
    _, unique_indices = np.unique(times[::-1], return_index=True)
    keep = np.sort(times.size - 1 - unique_indices)
    return colnames or [], times[keep], values[keep]


def parse_line_xy(file_path: Path) -> tuple[list[str], np.ndarray]:
    """Parse line_*.xy.

    Returns variable names and data array.
    The first 3 columns are assumed x/y/z.
    """
    stem = file_path.stem
    payload = stem.replace("line_", "", 1)
    parts = [p for p in payload.split("_") if p]

    variables = ["x", "y", "z"]
    for p in parts:
        if p == "U":
            variables.extend(["Ux", "Uy", "Uz"])
        else:
            variables.append(p)

    rows: list[list[float]] = []
    with file_path.open("r", encoding="utf-8", errors="ignore") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            vals = [parse_float(tok) for tok in line.split()]
            if len(vals) < 4:
                continue
            rows.append(vals)

    if not rows:
        return variables, np.empty((0, 0))

    data = np.array(rows, dtype=float)
    # trim names if parser over-expanded due to naming mismatch
    if data.shape[1] < len(variables):
        variables = variables[: data.shape[1]]
    return variables, data


def latest_numeric_dir(base_dir: Path) -> Path | None:
    dirs = sorted_time_dirs(base_dir)
    if not dirs:
        return None
    return dirs[-1]


def load_single_graph_profiles(
    post_dir: Path,
) -> list[dict[str, float | str | np.ndarray]]:
    """Load latest profiles from singleGraph_x* directories."""
    profiles: list[dict[str, float | str | np.ndarray]] = []
    graph_dirs = sorted(
        [p for p in post_dir.glob("singleGraph_x*") if p.is_dir()],
        key=lambda p: int(p.name.replace("singleGraph_x", "")),
    )

    for graph_dir in graph_dirs:
        tdir = latest_numeric_dir(graph_dir)
        if tdir is None:
            continue

        line_u_files = sorted(tdir.glob("line_U*.xy"))
        line_pk_files: list[Path] = []
        for pattern in ("line_p_k_omega*.xy", "line_p_omega*.xy", "line_p*.xy"):
            matches = sorted(tdir.glob(pattern))
            if matches:
                line_pk_files = matches
                break
        if not line_u_files:
            continue

        names_u, data_u = parse_line_xy(line_u_files[0])
        if data_u.size == 0:
            continue

        x = data_u[:, names_u.index("x")] if "x" in names_u else data_u[:, 0]
        y = data_u[:, names_u.index("y")] if "y" in names_u else data_u[:, 1]
        ux = data_u[:, names_u.index("Ux")] if "Ux" in names_u else np.full_like(y, np.nan)

        p = np.full_like(y, np.nan)
        k = np.full_like(y, np.nan)
        omega = np.full_like(y, np.nan)
        if line_pk_files:
            names_pk, data_pk = parse_line_xy(line_pk_files[0])
            if data_pk.size:
                if data_pk.shape[0] == y.shape[0]:
                    if "p" in names_pk:
                        p = data_pk[:, names_pk.index("p")]
                    if "k" in names_pk:
                        k = data_pk[:, names_pk.index("k")]
                    elif "k_LES" in names_pk and "kDeficit" in names_pk:
                        k = (
                            data_pk[:, names_pk.index("k_LES")]
                            + data_pk[:, names_pk.index("kDeficit")]
                        )
                    elif "k_LES" in names_pk:
                        k = data_pk[:, names_pk.index("k_LES")]
                    elif "kDeficit" in names_pk:
                        k = data_pk[:, names_pk.index("kDeficit")]
                    if "omega" in names_pk:
                        omega = data_pk[:, names_pk.index("omega")]

        order = np.argsort(y)
        xloc = float(np.nanmedian(x))
        profiles.append(
            {
                "graph": graph_dir.name,
                "xloc": xloc,
                "y": y[order],
                "ux": ux[order],
                "p": p[order],
                "k": k[order],
                "omega": omega[order],
            }
        )

    return profiles


def parse_wall_shear_dat(
    file_path: Path,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
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
                vmin = parse_vector(tokens[2])
                vmax = parse_vector(tokens[3])
            except ValueError:
                continue
            times.append(parse_float(tokens[0]))
            patches.append(tokens[1])
            mins.append(vmin)
            maxs.append(vmax)

    if not times:
        return np.array([]), np.array([]), np.empty((0, 0)), np.empty((0, 0))

    return (
        np.array(times, dtype=float),
        np.array(patches, dtype=object),
        np.array(mins, dtype=float),
        np.array(maxs, dtype=float),
    )


def load_wall_shear(post_dir: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    base_dir = post_dir / "wallShearStress"
    all_times: list[np.ndarray] = []
    all_patches: list[np.ndarray] = []
    all_mins: list[np.ndarray] = []
    all_maxs: list[np.ndarray] = []

    for time_dir in sorted_time_dirs(base_dir):
        file_path = time_dir / "wallShearStress.dat"
        if not file_path.exists():
            continue
        t, p, mn, mx = parse_wall_shear_dat(file_path)
        if t.size == 0:
            continue
        all_times.append(t)
        all_patches.append(p)
        all_mins.append(mn)
        all_maxs.append(mx)

    if not all_times:
        return np.array([]), np.array([]), np.empty((0, 0)), np.empty((0, 0))

    times = np.concatenate(all_times)
    patches = np.concatenate(all_patches)
    mins = np.concatenate(all_mins, axis=0)
    maxs = np.concatenate(all_maxs, axis=0)
    order = np.argsort(times)
    return times[order], patches[order], mins[order], maxs[order]


def parse_wall_profile_raw(file_path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return x, coordinates, and wall-shear vector from wallProfiles raw file."""
    rows: list[list[float]] = []
    with file_path.open("r", encoding="utf-8", errors="ignore") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            vals = [parse_float(tok) for tok in line.split()]
            if len(vals) < 6:
                continue
            rows.append(vals)

    if not rows:
        return np.array([]), np.empty((0, 3)), np.empty((0, 3))

    data = np.array(rows, dtype=float)
    coords = data[:, :3]
    tau = data[:, 3:6]
    order = np.argsort(coords[:, 0])
    return coords[order, 0], coords[order], tau[order]


def compute_tangent_vectors(coords: np.ndarray) -> np.ndarray:
    """Compute local unit tangents from ordered wall coordinates."""
    n = coords.shape[0]
    if n == 0:
        return np.empty((0, 3), dtype=float)
    if n == 1:
        return np.array([[1.0, 0.0, 0.0]], dtype=float)

    seg = coords[1:] - coords[:-1]
    seg_norm = np.linalg.norm(seg, axis=1)
    seg_u = np.zeros_like(seg)
    nz = seg_norm > 0.0
    seg_u[nz] = seg[nz] / seg_norm[nz, None]

    t = np.zeros_like(coords)
    if nz.any():
        first_nz = int(np.where(nz)[0][0])
        last_nz = int(np.where(nz)[0][-1])
        t[0] = seg_u[first_nz]
        t[-1] = seg_u[last_nz]
    else:
        t[:] = np.array([1.0, 0.0, 0.0])
        return t

    for i in range(1, n - 1):
        vec = seg_u[i - 1] + seg_u[i]
        norm = np.linalg.norm(vec)
        if norm > 0.0:
            t[i] = vec / norm
        elif np.linalg.norm(seg_u[i]) > 0.0:
            t[i] = seg_u[i]
        elif np.linalg.norm(seg_u[i - 1]) > 0.0:
            t[i] = seg_u[i - 1]
        else:
            t[i] = t[i - 1]

    norm_t = np.linalg.norm(t, axis=1)
    bad = norm_t <= 0.0
    if bad.any():
        t[bad] = np.array([1.0, 0.0, 0.0])
        norm_t = np.linalg.norm(t, axis=1)
    return t / norm_t[:, None]


def parse_surface_field_value(file_path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Parse cfBottom/cfTop surfaceFieldValue.dat.

    Returns times and x-component of vector value.
    """
    times: list[float] = []
    values_x: list[float] = []

    with file_path.open("r", encoding="utf-8", errors="ignore") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            tokens = tokenize_line(line)
            if len(tokens) < 2:
                continue
            try:
                vec = parse_vector(tokens[1])
            except ValueError:
                continue
            times.append(parse_float(tokens[0]))
            values_x.append(vec[0] if vec.size else float("nan"))

    if not times:
        return np.array([]), np.array([])

    t = np.array(times, dtype=float)
    v = np.array(values_x, dtype=float)
    order = np.argsort(t)
    return t[order], v[order]


def autoscale_axes(ax: plt.Axes) -> None:
    """Use plotted data to set x/y ranges (no hard-coded limits)."""
    ax.relim()
    ax.autoscale_view()


def plot_residuals(post_dir: Path, figures_dir: Path) -> list[Path]:
    names, times, values = load_residuals(post_dir)
    if times.size == 0 or values.size == 0:
        return []

    fig, ax = plt.subplots(figsize=(10, 6))
    plotted = False
    for idx, name in enumerate(names):
        y = values[:, idx]
        mask = np.isfinite(y) & (y > 0.0)
        if mask.any():
            ax.semilogy(times[mask], y[mask], label=name)
            plotted = True

    if not plotted:
        plt.close(fig)
        return []

    autoscale_axes(ax)
    ax.set_title("Residuals")
    ax.set_xlabel("Iteration")
    ax.set_ylabel("Residual")
    ax.grid(True, which="both", linestyle="--", alpha=0.35)
    ax.legend(loc="best")
    fig.tight_layout()

    out_file = figures_dir / "residuals.png"
    fig.savefig(out_file, dpi=200)
    plt.close(fig)
    return [out_file]


def plot_profiles(
    profiles: list[dict[str, float | str | np.ndarray]],
    figures_dir: Path,
    u_ref: float,
) -> list[Path]:
    if not profiles:
        return []

    saved: list[Path] = []

    # Ux profiles (benchmark style shift by x/h).
    # For this periodic-hill case, sampled coordinates are already in normalized units.
    fig_u, ax_u = plt.subplots(figsize=(9, 6))
    for prof in profiles:
        xloc = float(prof["xloc"])
        y = np.array(prof["y"], dtype=float)
        ux = np.array(prof["ux"], dtype=float)
        mask = np.isfinite(y) & np.isfinite(ux)
        if not mask.any():
            continue
        ax_u.plot(ux[mask] / u_ref + xloc, y[mask], label=f"x/h={xloc:.2f}")

    autoscale_axes(ax_u)
    ax_u.set_title(r"Velocity Profiles: $U_x/U_{ref} + x/h$")
    ax_u.set_xlabel(r"$U_x/U_{ref} + x/h$")
    ax_u.set_ylabel(r"$y/h$")
    ax_u.grid(True, linestyle="--", alpha=0.35)
    ax_u.legend(loc="best", fontsize=8, ncol=2)
    fig_u.tight_layout()
    out_u = figures_dir / "profiles_Ux.png"
    fig_u.savefig(out_u, dpi=200)
    plt.close(fig_u)
    saved.append(out_u)

    # k profiles
    fig_k, ax_k = plt.subplots(figsize=(9, 5))
    for prof in profiles:
        xloc = float(prof["xloc"])
        y = np.array(prof["y"], dtype=float)
        k = np.array(prof["k"], dtype=float)

        mk = np.isfinite(y) & np.isfinite(k)
        if mk.any():
            ax_k.plot(5.0 * k[mk] / (u_ref * u_ref) + xloc, y[mk], label=f"x/h={xloc:.2f}")

    autoscale_axes(ax_k)
    ax_k.set_title(r"$5k/U_{ref}^2 + x/h$")
    ax_k.set_xlabel(r"$5k/U_{ref}^2 + x/h$")
    ax_k.set_ylabel(r"$y/h$")
    ax_k.grid(True, linestyle="--", alpha=0.35)
    ax_k.legend(loc="best", fontsize=8, ncol=1)

    fig_k.tight_layout()
    out_k = figures_dir / "profiles_k_omega.png"
    fig_k.savefig(out_k, dpi=200)
    plt.close(fig_k)
    saved.append(out_k)

    return saved


def plot_wall_shear(post_dir: Path, figures_dir: Path) -> list[Path]:
    times, patches, mins, maxs = load_wall_shear(post_dir)
    if times.size == 0:
        return []

    min_mag = np.linalg.norm(mins, axis=1)
    max_mag = np.linalg.norm(maxs, axis=1)

    fig, ax = plt.subplots(figsize=(9, 5))
    for patch in sorted(set(patches.tolist())):
        mask = patches == patch
        t = times[mask]
        mn = min_mag[mask]
        mx = max_mag[mask]
        order = np.argsort(t)
        t = t[order]
        mn = mn[order]
        mx = mx[order]
        ax.plot(t, mn, marker="o", linestyle="-", label=f"{patch} |min|")
        ax.plot(t, mx, marker="s", linestyle="--", label=f"{patch} |max|")

    autoscale_axes(ax)
    ax.set_title("Wall Shear Stress Magnitude")
    ax.set_xlabel("Time / Iteration")
    ax.set_ylabel(r"$|\tau_w|$")
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.legend(loc="best")
    fig.tight_layout()

    out_file = figures_dir / "wallShearStress_minmax.png"
    fig.savefig(out_file, dpi=200)
    plt.close(fig)
    return [out_file]


def plot_cf_profiles(post_dir: Path, figures_dir: Path, h: float, u_ref: float) -> list[Path]:
    wall_profiles_dir = post_dir / "wallProfiles"
    tdir = latest_numeric_dir(wall_profiles_dir)
    if tdir is None:
        return []

    bottom_file = tdir / "wallShearStress_bottomWall.raw"
    top_file = tdir / "wallShearStress_topWall.raw"
    if not bottom_file.exists() or not top_file.exists():
        return []

    xb, coords_b, tau_b = parse_wall_profile_raw(bottom_file)
    xt, coords_t, tau_t = parse_wall_profile_raw(top_file)
    if xb.size == 0 or xt.size == 0:
        return []

    # Use wall-tangential shear for Cf: Cf = -(tau_w . t) / (0.5 U_ref^2)
    tangent_b = compute_tangent_vectors(coords_b)
    tangent_t = compute_tangent_vectors(coords_t)
    tau_tan_b = np.einsum("ij,ij->i", tau_b, tangent_b)
    tau_tan_t = np.einsum("ij,ij->i", tau_t, tangent_t)
    cf_bottom = -tau_tan_b / (0.5 * u_ref * u_ref)
    cf_top = -tau_tan_t / (0.5 * u_ref * u_ref)
    # In this periodic-hill setup, wallProfiles x-coordinate is already normalized as x/H.
    xb_over_h = xb
    xt_over_h = xt

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(xb_over_h, cf_bottom, label="bottomWall")
    ax.plot(xt_over_h, cf_top, label="topWall")
    autoscale_axes(ax)
    ax.set_title(r"Skin-Friction Profile (Tangential) $C_f(x)$")
    ax.set_xlabel(r"$x/h$")
    ax.set_ylabel(r"$C_f = -(\tau_w\cdot t)/(0.5U_{ref}^2)$")
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.legend(loc="best")
    fig.tight_layout()

    out_file = figures_dir / "Cf_profile_bottom_top.png"
    fig.savefig(out_file, dpi=200)
    plt.close(fig)
    return [out_file]


def plot_shear_stress_profiles(post_dir: Path, figures_dir: Path) -> list[Path]:
    wall_profiles_dir = post_dir / "wallProfiles"
    tdir = latest_numeric_dir(wall_profiles_dir)
    if tdir is None:
        return []

    bottom_file = tdir / "wallShearStress_bottomWall.raw"
    top_file = tdir / "wallShearStress_topWall.raw"
    if not bottom_file.exists() or not top_file.exists():
        return []

    xb, coords_b, tau_b = parse_wall_profile_raw(bottom_file)
    xt, coords_t, tau_t = parse_wall_profile_raw(top_file)
    if xb.size == 0 or xt.size == 0:
        return []

    # Plot wall-tangential shear with same sign convention as Cf.
    tangent_b = compute_tangent_vectors(coords_b)
    tangent_t = compute_tangent_vectors(coords_t)
    tau_bottom = -np.einsum("ij,ij->i", tau_b, tangent_b)
    tau_top = -np.einsum("ij,ij->i", tau_t, tangent_t)
    # In this periodic-hill setup, wallProfiles x-coordinate is already normalized as x/H.
    xb_over_h = xb
    xt_over_h = xt

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(xb_over_h, tau_bottom, label="bottomWall")
    ax.plot(xt_over_h, tau_top, label="topWall")
    autoscale_axes(ax)
    ax.set_title(r"Wall Shear-Stress Profile (Tangential) $\tau_t(x)$")
    ax.set_xlabel(r"$x/h$")
    ax.set_ylabel(r"$-\tau_w\cdot t$")
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.legend(loc="best")
    fig.tight_layout()

    out_file = figures_dir / "shearStress_profile_bottom_top.png"
    fig.savefig(out_file, dpi=200)
    plt.close(fig)
    return [out_file]


def plot_cf_history(post_dir: Path, figures_dir: Path) -> list[Path]:
    bottom_file = post_dir / "cfBottom" / "0" / "surfaceFieldValue.dat"
    top_file = post_dir / "cfTop" / "0" / "surfaceFieldValue.dat"
    if not bottom_file.exists() or not top_file.exists():
        return []

    tb, cfb = parse_surface_field_value(bottom_file)
    tt, cft = parse_surface_field_value(top_file)
    cfb = -cfb
    cft = -cft
    if tb.size == 0 and tt.size == 0:
        return []

    fig, ax = plt.subplots(figsize=(9, 5))
    if tb.size:
        ax.plot(tb, cfb, marker="o", label="cfBottom (area-avg)")
    if tt.size:
        ax.plot(tt, cft, marker="s", label="cfTop (area-avg)")

    autoscale_axes(ax)
    ax.set_title(r"Area-Averaged $C_{f,x}$ History")
    ax.set_xlabel("Time / Iteration")
    ax.set_ylabel(r"$C_{f,x}$")
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.legend(loc="best")
    fig.tight_layout()

    out_file = figures_dir / "Cf_mean_history.png"
    fig.savefig(out_file, dpi=200)
    plt.close(fig)
    return [out_file]


def main() -> None:
    case_dir = invocation_case_dir()
    case_def = read_case_def(case_dir)

    h = case_def.get("h", 0.028)
    u_ref = 1.0

    post_dir = case_dir / "postProcessing"
    figures_dir = case_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    generated: list[Path] = []
    generated.extend(plot_residuals(post_dir, figures_dir))
    generated.extend(plot_profiles(load_single_graph_profiles(post_dir), figures_dir, u_ref))
    generated.extend(plot_wall_shear(post_dir, figures_dir))
    generated.extend(plot_shear_stress_profiles(post_dir, figures_dir))
    generated.extend(plot_cf_profiles(post_dir, figures_dir, h, u_ref))

    if generated:
        print("Generated figures:")
        for p in generated:
            print(f" - {p}")
    else:
        print(f"No valid postProcessing data found under: {post_dir}")


if __name__ == "__main__":
    main()
