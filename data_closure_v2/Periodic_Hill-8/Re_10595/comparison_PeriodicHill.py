"""Compare Periodic Hill Re_10595 00Baseline (SST) against LES data."""

import csv
import os
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

matplotlib.rcParams.update({"font.size": 15})


def write_csv(file_name: str, field_names: list[str], rows: list[dict]) -> None:
    """Write a tab-delimited CSV file."""
    with open(file_name, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=field_names, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def interp_with_nan(x_new: np.ndarray, x_old: np.ndarray, y_old: np.ndarray) -> np.ndarray:
    """Interpolate y_old(x_old) to x_new and use NaN outside the source range."""
    x_new = np.asarray(x_new, dtype=float)
    x_old = np.asarray(x_old, dtype=float)
    y_old = np.asarray(y_old, dtype=float)

    sort_inds = np.argsort(x_old)
    x_old = x_old[sort_inds]
    y_old = y_old[sort_inds]

    y_new = np.interp(x_new, x_old, y_old)
    y_new[(x_new < x_old[0]) | (x_new > x_old[-1])] = np.nan
    return y_new


def latest_numeric_dir(base_dir: Path) -> Path:
    """Return latest numeric time directory."""
    time_dirs = []
    for item in base_dir.iterdir():
        if not item.is_dir():
            continue
        try:
            time_dirs.append((float(item.name), item))
        except ValueError:
            continue
    if not time_dirs:
        raise RuntimeError(f"No numeric time directories found in {base_dir}")
    return sorted(time_dirs, key=lambda item: item[0])[-1][1]


def read_xy_file(file_path: Path) -> dict[str, np.ndarray]:
    """Read an OpenFOAM line_*.xy or *.raw file into named columns."""
    data = np.loadtxt(file_path, comments="#")
    data = data.reshape((-1, data.shape[-1]))

    variables = ["x", "y", "z"]
    payload = file_path.stem
    if payload.startswith("line_"):
        file_vars = payload.replace("line_", "", 1).split("_")
    elif file_path.suffix == ".raw":
        file_vars = payload.split("_")[:-1]
    else:
        file_vars = payload.split("_")

    for var in file_vars:
        if var == "U":
            variables.extend(["Ux", "Uy", "Uz"])
        elif var == "gradU":
            variables.extend(
                [
                    "dUx/dx",
                    "dUx/dy",
                    "dUx/dz",
                    "dUy/dx",
                    "dUy/dy",
                    "dUy/dz",
                    "dUz/dx",
                    "dUz/dy",
                    "dUz/dz",
                ]
            )
        elif var == "wallShearStress":
            variables.extend(["wallShearStressx", "wallShearStressy", "wallShearStressz"])
        elif var:
            variables.append(var)

    if len(variables) != data.shape[1]:
        raise RuntimeError(
            f"Column mismatch in {file_path}: parsed {len(variables)} names "
            f"for {data.shape[1]} columns"
        )

    return {name: data[:, i] for i, name in enumerate(variables)}


def read_single_graph_dir(graph_dir: Path) -> dict[str, np.ndarray]:
    """Read the latest singleGraph output directory."""
    latest_dir = latest_numeric_dir(graph_dir)
    profile: dict[str, np.ndarray] = {}
    for file_path in sorted(latest_dir.glob("*.xy")):
        profile.update(read_xy_file(file_path))
    return profile


def read_wall_scalar(file_path: Path, value_name: str) -> dict[str, np.ndarray]:
    """Read p_*Wall.raw."""
    data = np.loadtxt(file_path, comments="#")
    data = data.reshape((-1, data.shape[-1]))
    return {
        "x": data[:, 0],
        "y": data[:, 1],
        "z": data[:, 2],
        value_name: data[:, 3],
    }


def read_wall_vector(file_path: Path, value_name: str) -> dict[str, np.ndarray]:
    """Read wallShearStress_*Wall.raw."""
    data = np.loadtxt(file_path, comments="#")
    data = data.reshape((-1, data.shape[-1]))
    return {
        "x": data[:, 0],
        "y": data[:, 1],
        "z": data[:, 2],
        f"{value_name}x": data[:, 3],
        f"{value_name}y": data[:, 4],
        f"{value_name}z": data[:, 5],
    }


def compute_tangent_vectors(coords: np.ndarray) -> np.ndarray:
    """Compute local unit tangents from ordered wall coordinates."""
    n = coords.shape[0]
    if n == 1:
        return np.array([[1.0, 0.0, 0.0]], dtype=float)

    seg = coords[1:] - coords[:-1]
    seg_norm = np.linalg.norm(seg, axis=1)
    seg_u = seg / seg_norm[:, None]

    tangent = np.zeros_like(coords)
    tangent[0] = seg_u[0]
    tangent[-1] = seg_u[-1]
    for i in range(1, n - 1):
        vec = seg_u[i - 1] + seg_u[i]
        norm = np.linalg.norm(vec)
        tangent[i] = vec / norm if norm > 0.0 else seg_u[i]

    return tangent / np.linalg.norm(tangent, axis=1)[:, None]


def read_baseline_wall(case_dir: str, patch: str, u_ref: float, p_ref: float) -> dict[str, np.ndarray]:
    """Read baseline wall p and wallShearStress and compute Cp/Cf."""
    wall_dir = Path(case_dir) / "postProcessing" / "wallProfiles"
    latest_dir = latest_numeric_dir(wall_dir)
    p_data = read_wall_scalar(latest_dir / f"p_{patch}.raw", "p")
    tau_data = read_wall_vector(latest_dir / f"wallShearStress_{patch}.raw", "wallShearStress")

    order = np.argsort(p_data["x"])
    x = p_data["x"][order]
    y = p_data["y"][order]
    z = p_data["z"][order]
    p = p_data["p"][order]
    tau = np.column_stack(
        (
            tau_data["wallShearStressx"][order],
            tau_data["wallShearStressy"][order],
            tau_data["wallShearStressz"][order],
        )
    )

    coords = np.column_stack((x, y, z))
    tangent = compute_tangent_vectors(coords)
    tau_tangent = np.einsum("ij,ij->i", tau, tangent)

    return {
        "x": x,
        "y": y,
        "Cp": (p - p_ref) / (0.5 * u_ref**2),
        "Cf": -tau_tangent / (0.5 * u_ref**2),
    }


def read_les_grid(file_name: str) -> dict[str, np.ndarray]:
    """Read LES CSV and reshape to the structured grid."""
    raw = np.genfromtxt(file_name, delimiter=",", names=True, autostrip=True)
    n_cols = 281
    n_rows = raw.shape[0] // n_cols
    if n_rows * n_cols != raw.shape[0]:
        raise RuntimeError(f"Unexpected LES grid size in {file_name}")

    return {
        key: np.asarray(raw[key], dtype=float).reshape((n_rows, n_cols))
        for key in ("x", "y", "um", "vm", "pm", "uv")
    }


def interpolate_les_profile(
    les_grid: dict[str, np.ndarray], x_loc: float, field_name: str
) -> tuple[np.ndarray, np.ndarray]:
    """Interpolate a LES profile at x/h = x_loc from each grid layer."""
    y_values = []
    field_values = []

    for i in range(les_grid["x"].shape[0]):
        x_row = les_grid["x"][i]
        sort_inds = np.argsort(x_row)
        x_sorted = x_row[sort_inds]
        if x_loc < x_sorted[0] or x_loc > x_sorted[-1]:
            continue
        y_values.append(np.interp(x_loc, x_sorted, les_grid["y"][i][sort_inds]))
        field_values.append(np.interp(x_loc, x_sorted, les_grid[field_name][i][sort_inds]))

    y_values = np.asarray(y_values)
    field_values = np.asarray(field_values)
    order = np.argsort(y_values)
    return y_values[order], field_values[order]


def les_wall_data(
    les_grid: dict[str, np.ndarray],
    patch: str,
    nu: float,
    u_ref: float,
) -> dict[str, np.ndarray]:
    """Compute LES wall Cp and Cf from the wall row and first interior row."""
    if patch == "bottomWall":
        wall_i, inner_i = 0, 1
    elif patch == "topWall":
        wall_i, inner_i = -1, -2
    else:
        raise ValueError(f"Unsupported wall patch {patch}")

    x = les_grid["x"][wall_i]
    y = les_grid["y"][wall_i]
    p = les_grid["pm"][wall_i]
    u_inner = les_grid["um"][inner_i]
    v_inner = les_grid["vm"][inner_i]

    coords = np.column_stack((x, y, np.zeros_like(x)))
    tangent_3d = compute_tangent_vectors(coords)
    tangent = tangent_3d[:, :2]

    inner_vec = np.column_stack((les_grid["x"][inner_i] - x, les_grid["y"][inner_i] - y))
    normal = np.column_stack((-tangent[:, 1], tangent[:, 0]))
    sign = np.sign(np.nanmean(np.einsum("ij,ij->i", inner_vec, normal)))
    if sign == 0.0:
        sign = 1.0
    normal *= sign

    dn = np.einsum("ij,ij->i", inner_vec, normal)
    u_tangent = u_inner * tangent[:, 0] + v_inner * tangent[:, 1]
    d_ut_dn = np.divide(u_tangent, dn, out=np.full_like(u_tangent, np.nan), where=dn != 0.0)

    order = np.argsort(x)
    return {
        "x": x[order],
        "y": y[order],
        "Cp": (p[order]) / (0.5 * u_ref**2),
        "Cf": (nu * d_ut_dn[order]) / (0.5 * u_ref**2),
    }


def modeled_reynolds_shear(profile: dict[str, np.ndarray], u_ref: float) -> np.ndarray:
    """Compute SST modeled uv/Uref^2 from sampled nut and gradU."""
    required = ("nut", "dUx/dy", "dUy/dx")
    if not all(key in profile for key in required):
        missing = ", ".join(key for key in required if key not in profile)
        raise RuntimeError(f"Missing sampled fields for shear stress: {missing}")
    return -profile["nut"] * (profile["dUx/dy"] + profile["dUy/dx"]) / u_ref**2


def main() -> None:
    baseline_dir = "00Baseline"
    figures_dir = "Figures"
    os.makedirs(figures_dir, exist_ok=True)

    u_ref = 1.0
    p_ref = 1.0
    nu = 9.438414346389807e-5

    labels = ["RANS(SST)", "LES"]
    colors = ["gray", "black"]
    linestyles = ["--", "None"]
    markers = ["none", "."]
    ms = 4

    les_grid = read_les_grid("RefData/Hill_Breuer.csv")
    bottom_sst = read_baseline_wall(baseline_dir, "bottomWall", u_ref, p_ref)
    top_sst = read_baseline_wall(baseline_dir, "topWall", u_ref, p_ref)
    bottom_les = les_wall_data(les_grid, "bottomWall", nu, u_ref)
    top_les = les_wall_data(les_grid, "topWall", nu, u_ref)

    wall_rows = []
    for patch, sst, les in (
        ("bottomWall", bottom_sst, bottom_les),
        ("topWall", top_sst, top_les),
    ):
        cp_les = interp_with_nan(sst["x"], les["x"], les["Cp"])
        cf_les = interp_with_nan(sst["x"], les["x"], les["Cf"])
        for x_val, cp0, cp1, cf0, cf1 in zip(sst["x"], sst["Cp"], cp_les, sst["Cf"], cf_les):
            if np.isnan(cp1) or np.isnan(cf1):
                continue
            wall_rows.append(
                {
                    "wall": patch,
                    "x_over_h": x_val,
                    "Cp_RANS_SST": cp0,
                    "Cp_LES": cp1,
                    "Cf_RANS_SST": cf0,
                    "Cf_LES": cf1,
                }
            )

    write_csv(
        f"{figures_dir}/wall_Cp_Cf_PeriodicHill_Re10595.csv",
        ["wall", "x_over_h", "Cp_RANS_SST", "Cp_LES", "Cf_RANS_SST", "Cf_LES"],
        wall_rows,
    )

    # Wall Cp/Cf plots, separated by wall.
    for wall_label, file_label, sst, les in (
        ("Bottom Wall", "bottomWall", bottom_sst, bottom_les),
        ("Upper Wall", "topWall", top_sst, top_les),
    ):
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(sst["x"], sst["Cp"], c=colors[0], lw=2, linestyle="--", label=labels[0])
        ax.plot(les["x"], les["Cp"], c=colors[1], lw=0, marker=".", markersize=ms, label=labels[1])
        ax.set_xlabel("x/h [-]")
        ax.set_ylabel(r"$C_p = (p-p_{ref})/(0.5U_{ref}^2)$ [-]")
        ax.set_title(
            rf"{wall_label} Pressure Coefficient "
            rf"($U_{{ref}}={u_ref:g}$, $p_{{ref}}={p_ref:g}$)"
        )
        ax.grid(True)
        ax.legend(loc="best", fontsize=11)
        fig.tight_layout()
        fig.savefig(f"{figures_dir}/compareCp_{file_label}_PeriodicHill_Re10595.pdf")
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(sst["x"], sst["Cf"], c=colors[0], lw=2, linestyle="--", label=labels[0])
        ax.plot(les["x"], les["Cf"], c=colors[1], lw=0, marker=".", markersize=ms, label=labels[1])
        ax.set_xlabel("x/h [-]")
        ax.set_ylabel(r"$C_f = -(\tau_w\cdot t)/(0.5U_{ref}^2)$ [-]")
        ax.set_title(
            rf"{wall_label} Skin-Friction Coefficient "
            rf"($U_{{ref}}={u_ref:g}$, $p_{{ref}}={p_ref:g}$)"
        )
        ax.grid(True)
        ax.legend(loc="best", fontsize=11)
        fig.tight_layout()
        fig.savefig(f"{figures_dir}/compareCf_{file_label}_PeriodicHill_Re10595.pdf")
        plt.close(fig)

    single_graph_locs = [f"x{i}" for i in range(9)]
    x_profile_locs = [0.0, 1, 2, 3, 4, 5, 6, 7, 8]
    profile_rows = []

    # Ux profiles
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(bottom_sst["x"], bottom_sst["y"], c="k", lw=1.5)
    ax.plot(top_sst["x"], top_sst["y"], c="k", lw=1.5)
    first_sst = True
    first_les = True
    for loc, x_station in zip(single_graph_locs, x_profile_locs):
        profile = read_single_graph_dir(Path(baseline_dir) / "postProcessing" / f"singleGraph_{loc}")
        order = np.argsort(profile["y"])
        for key in list(profile.keys()):
            profile[key] = np.asarray(profile[key], dtype=float)[order]
        y_sst = profile["y"]
        u_sst = profile["Ux"] / u_ref
        y_les, u_les = interpolate_les_profile(les_grid, x_station, "um")
        ax.plot([x_station, x_station], [y_sst[0], y_sst[-1]], c="lightgrey", lw=2, zorder=0)
        ax.plot(
            x_station + u_sst,
            y_sst,
            c=colors[0],
            lw=2,
            linestyle="--",
            label=labels[0] if first_sst else "_nolegend_",
        )
        ax.plot(
            x_station + u_les / u_ref,
            y_les,
            c=colors[1],
            lw=0,
            marker=".",
            markersize=ms,
            label=labels[1] if first_les else "_nolegend_",
        )
        first_sst = False
        first_les = False
    ax.set_xlabel(r"$U_x/U_{ref} + x/h$ [-]")
    ax.set_ylabel("y/h [-]")
    ax.set_xlim(-0.2, 9.2)
    ax.set_ylim(-0.1, 3.2)
    ax.grid(True)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(f"{figures_dir}/compareUxProfiles_PeriodicHill_Re10595.pdf")
    plt.close(fig)

    # uv profiles and CSV rows
    fuv = 20.0
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(bottom_sst["x"], bottom_sst["y"], c="k", lw=1.5)
    ax.plot(top_sst["x"], top_sst["y"], c="k", lw=1.5)
    first_sst = True
    first_les = True
    for loc, x_station in zip(single_graph_locs, x_profile_locs):
        profile = read_single_graph_dir(Path(baseline_dir) / "postProcessing" / f"singleGraph_{loc}")
        order = np.argsort(profile["y"])
        for key in list(profile.keys()):
            profile[key] = np.asarray(profile[key], dtype=float)[order]
        y_sst = profile["y"]
        u_sst = profile["Ux"] / u_ref
        uv_sst = modeled_reynolds_shear(profile, u_ref)
        y_les_u, u_les = interpolate_les_profile(les_grid, x_station, "um")
        y_les_uv, uv_les = interpolate_les_profile(les_grid, x_station, "uv")
        u_les_on_sst = interp_with_nan(y_sst, y_les_u, u_les / u_ref)
        uv_les_on_sst = interp_with_nan(y_sst, y_les_uv, uv_les / u_ref**2)

        for y_val, u0, u1, uv0, uv1 in zip(y_sst, u_sst, u_les_on_sst, uv_sst, uv_les_on_sst):
            if np.isnan(u1) or np.isnan(uv1):
                continue
            profile_rows.append(
                {
                    "station_x_over_h": x_station,
                    "y_over_h": y_val,
                    "Ux_over_Uref_RANS_SST": u0,
                    "Ux_over_Uref_LES": u1,
                    "uv_over_Uref2_RANS_SST": uv0,
                    "uv_over_Uref2_LES": uv1,
                }
            )

        ax.plot([x_station, x_station], [y_sst[0], y_sst[-1]], c="lightgrey", lw=2, zorder=0)
        ax.plot(
            x_station + fuv * uv_sst,
            y_sst,
            c=colors[0],
            lw=2,
            linestyle="--",
            label=labels[0] if first_sst else "_nolegend_",
        )
        ax.plot(
            x_station + fuv * uv_les / u_ref**2,
            y_les_uv,
            c=colors[1],
            lw=0,
            marker=".",
            markersize=ms,
            label=labels[1] if first_les else "_nolegend_",
        )
        first_sst = False
        first_les = False

    ax.set_xlabel(r"$20uv/U_{ref}^2 + x/h$ [-]")
    ax.set_ylabel("y/h [-]")
    ax.set_xlim(-0.2, 9.2)
    ax.set_ylim(-0.1, 3.2)
    ax.grid(True)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(f"{figures_dir}/compareuvProfiles_PeriodicHill_Re10595.pdf")
    plt.close(fig)

    write_csv(
        f"{figures_dir}/velocity_shear_profiles_PeriodicHill_Re10595.csv",
        [
            "station_x_over_h",
            "y_over_h",
            "Ux_over_Uref_RANS_SST",
            "Ux_over_Uref_LES",
            "uv_over_Uref2_RANS_SST",
            "uv_over_Uref2_LES",
        ],
        profile_rows,
    )

    print("Generated figures:")
    for file_name in (
        "compareCp_bottomWall_PeriodicHill_Re10595.pdf",
        "compareCf_bottomWall_PeriodicHill_Re10595.pdf",
        "compareCp_topWall_PeriodicHill_Re10595.pdf",
        "compareCf_topWall_PeriodicHill_Re10595.pdf",
        "compareUxProfiles_PeriodicHill_Re10595.pdf",
        "compareuvProfiles_PeriodicHill_Re10595.pdf",
    ):
        print(f" - {figures_dir}/{file_name}")
    print("Reference values:")
    print(f" - Uref = {u_ref}")
    print(f" - Pref = {p_ref}")
    print("Generated CSV files:")
    print(f" - {figures_dir}/wall_Cp_Cf_PeriodicHill_Re10595.csv")
    print(f" - {figures_dir}/velocity_shear_profiles_PeriodicHill_Re10595.csv")


if __name__ == "__main__":
    main()
