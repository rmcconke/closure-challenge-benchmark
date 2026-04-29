"""Compare CBFS-8 bottom-wall Cp and Cf for 00Baseline (SST) against LES."""

import csv
import os
import re

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

from readExpData import readNasaZoneFile, readSingleGraphDir

# Increase default plot fontsize
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


def finite_pair_mask(*arrays: np.ndarray) -> np.ndarray:
    """Return mask for locations where every supplied array is finite."""
    if not arrays:
        return np.array([], dtype=bool)

    mask = np.ones_like(np.asarray(arrays[0], dtype=float), dtype=bool)
    for array in arrays:
        mask &= np.isfinite(np.asarray(array, dtype=float))

    return mask


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


def read_ordered_les_grid(file_name: str) -> dict[str, np.ndarray]:
    """Read the ordered LES profile/stress data and reshape variables to grids."""
    with open(file_name) as f:
        header = f.read(2000)

    i_match = re.search(r"\bI\s*=\s*(\d+)", header)
    j_match = re.search(r"\bJ\s*=\s*(\d+)", header)
    if i_match is None or j_match is None:
        raise RuntimeError(f"Could not find I/J dimensions in {file_name}")

    i_size = int(i_match.group(1))
    j_size = int(j_match.group(1))

    zone_dict = readNasaZoneFile(file_name)
    zone = next(iter(zone_dict.values()))

    return {
        key: np.asarray(value, dtype=float).reshape((j_size, i_size))
        for key, value in zone.items()
    }


def interpolate_les_profile(
    les_grid: dict[str, np.ndarray], x_loc: float, field_name: str
) -> tuple[np.ndarray, np.ndarray]:
    """Interpolate a LES field profile at x/H = x_loc."""
    y_values = []
    field_values = []

    x_grid = les_grid["x/H"]
    y_grid = les_grid["y/H"]
    field_grid = les_grid[field_name]

    for i in range(x_grid.shape[0]):
        x_row = x_grid[i]
        sort_inds = np.argsort(x_row)
        x_sorted = x_row[sort_inds]

        if x_loc < x_sorted[0] or x_loc > x_sorted[-1]:
            continue

        y_values.append(np.interp(x_loc, x_sorted, y_grid[i][sort_inds]))
        field_values.append(np.interp(x_loc, x_sorted, field_grid[i][sort_inds]))

    y_values = np.asarray(y_values)
    field_values = np.asarray(field_values)
    sort_inds = np.argsort(y_values)

    return y_values[sort_inds], field_values[sort_inds]


def modeled_reynolds_shear(profile: dict[str, np.ndarray], u_ref: float) -> np.ndarray:
    """Compute SST modeled uv/Uref^2 from sampled nut and gradU fields."""
    if all(key in profile for key in ("nut", "dUx/dy", "dUy/dx")):
        return -profile["nut"] * (profile["dUx/dy"] + profile["dUy/dx"]) / u_ref**2

    # Fallback for old post-processing output that did not sample gradU/nut.
    # The current 00Baseline setup writes nut and gradU, so this path should
    # not be used for regenerated metrics.
    if not all(key in profile for key in ("k", "omega", "Ux", "y")):
        raise RuntimeError(
            "Cannot compute SST shear stress profile. Need either "
            "(nut, gradU) or (k, omega, Ux, y) in sampled profile output."
        )

    y = np.asarray(profile["y"], dtype=float)
    ux = np.asarray(profile["Ux"], dtype=float)
    k = np.asarray(profile["k"], dtype=float)
    omega = np.asarray(profile["omega"], dtype=float)

    nut = np.divide(k, omega, out=np.full_like(k, np.nan), where=omega != 0.0)
    return -nut * np.gradient(ux, y) / u_ref**2


def main() -> None:
    baseline_dir = "00Baseline"
    frozen_dir = "01Frozen"
    figures_dir = "Figures"
    os.makedirs(figures_dir, exist_ok=True)

    # Reference scales
    u_ref = 1.0
    p_ref = 0.0
    x_ref = 1.0  # x/H

    # LES reference data (same convention used previously in this repo)
    # columns: x, ..., Cp, Cf/2
    les_data = np.genfromtxt("RefData/LES_walldata.txt", delimiter="")
    x_les = les_data[:, 0]
    cp_les = les_data[:, 2]
    cf_les = les_data[:, 3] * 2.0

    # Baseline bottom-wall data from postProcessing/bottomValues
    wall = readSingleGraphDir(f"{baseline_dir}/postProcessing/bottomValues/")
    required = {"x", "y", "z", "p", "wallShearStressx", "wallShearStressy", "wallShearStressz"}
    missing = required.difference(wall.keys())
    if missing:
        raise RuntimeError(
            "Missing required fields in bottomValues output: "
            + ", ".join(sorted(missing))
            + ". Ensure wallShearStress and bottomValues post-processing were run."
        )

    x = np.array(wall["x"], dtype=float)
    y = np.array(wall["y"], dtype=float)
    z = np.array(wall["z"], dtype=float)
    p = np.array(wall["p"], dtype=float)
    tau = np.column_stack(
        (
            np.array(wall["wallShearStressx"], dtype=float),
            np.array(wall["wallShearStressy"], dtype=float),
            np.array(wall["wallShearStressz"], dtype=float),
        )
    )

    # Sort along streamwise direction for clean plotting and local tangents
    order = np.argsort(x)
    x = x[order]
    y = y[order]
    z = z[order]
    p = p[order]
    tau = tau[order]

    coords = np.column_stack((x, y, z))
    tangent = compute_tangent_vectors(coords)
    tau_t = np.einsum("ij,ij->i", tau, tangent)

    cp_baseline = (p - p_ref) / (0.5 * u_ref * u_ref)
    cf_baseline = -tau_t / (0.5 * u_ref * u_ref)
    x_baseline = x / x_ref

    cp_les_on_baseline = interp_with_nan(x_baseline, x_les, cp_les)
    cf_les_on_baseline = interp_with_nan(x_baseline, x_les, cf_les)
    wall_pair_mask = finite_pair_mask(
        x_baseline,
        cp_baseline,
        cp_les_on_baseline,
        cf_baseline,
        cf_les_on_baseline,
    )
    x_wall_paired = x_baseline[wall_pair_mask]
    cp_baseline_paired = cp_baseline[wall_pair_mask]
    cp_les_paired = cp_les_on_baseline[wall_pair_mask]
    cf_baseline_paired = cf_baseline[wall_pair_mask]
    cf_les_paired = cf_les_on_baseline[wall_pair_mask]

    wall_rows = []
    for x_val, cp_sst, cp_ref, cf_sst, cf_ref in zip(
        x_wall_paired,
        cp_baseline_paired,
        cp_les_paired,
        cf_baseline_paired,
        cf_les_paired,
    ):
        wall_rows.append(
            {
                "x_over_h": x_val,
                "Cp_RANS_SST": cp_sst,
                "Cp_LES": cp_ref,
                "Cf_RANS_SST": cf_sst,
                "Cf_LES": cf_ref,
            }
        )

    write_csv(
        f"{figures_dir}/wall_Cp_Cf_CBFS.csv",
        ["x_over_h", "Cp_RANS_SST", "Cp_LES", "Cf_RANS_SST", "Cf_LES"],
        wall_rows,
    )

    labels = ["SST", "LES"]
    linestyles = ["--", "None"]
    colors = ["gray", "black"]
    markers = ["none", "."]
    ms = 4

    # Ux profile comparison settings (template-style shifted profiles)
    single_graph_locs = ["x0", "x1", "x2", "x3", "x4", "x5", "x6", "x7", "x8"]
    x_profile_locs = [1e-6, 1, 2, 3, 4, 5, 6, 7, 8]
    les_profile_grid = read_ordered_les_grid("RefData/curvedbackstep_vel_stress.dat")
    profile_rows = []

    # Cp plot
    plt.figure(figsize=(10, 5))
    plt.plot(
        x_wall_paired,
        cp_baseline_paired,
        c=colors[0],
        lw=2,
        linestyle=linestyles[0],
        zorder=5,
        label=labels[0],
        marker=markers[0],
        markersize=ms,
    )
    plt.plot(
        x_wall_paired,
        cp_les_paired,
        c=colors[1],
        lw=0,
        linestyle=linestyles[1],
        zorder=2,
        label=labels[1],
        marker=markers[1],
        markersize=ms,
    )
    plt.grid()
    plt.xlim(-5, 15)
    plt.xlabel("x/h [-]", fontsize=18)
    plt.ylabel(r"$C_p = (p - p_{ref})/(0.5U_{ref}^2)$ [-]", fontsize=18)
    plt.title(rf"Bottom-Wall $C_p$ Comparison ($U_{{ref}}(SST)={u_ref:.2f}$)")
    leg = plt.legend(loc="best", fontsize=15)
    leg.set_zorder(100)
    plt.tight_layout(rect=[0, 0, 1, 1])
    plt.savefig(f"{figures_dir}/compareCpWall-CBFS.pdf")
    plt.close()

    # Cf plot
    plt.figure(figsize=(10, 5))
    plt.plot(
        x_wall_paired,
        cf_baseline_paired,
        c=colors[0],
        lw=2,
        linestyle=linestyles[0],
        zorder=5,
        label=labels[0],
        marker=markers[0],
        markersize=ms,
    )
    plt.plot(
        x_wall_paired,
        cf_les_paired,
        c=colors[1],
        lw=0,
        linestyle=linestyles[1],
        zorder=2,
        label=labels[1],
        marker=markers[1],
        markersize=ms,
    )
    plt.grid()
    plt.xlim(-5, 15)
    plt.xlabel("x/h [-]", fontsize=18)
    plt.ylabel(r"$C_f = -(\tau_w\cdot t)/(0.5U_{ref}^2)$ [-]", fontsize=18)
    plt.title(rf"Bottom-Wall $C_f$ Comparison ($U_{{ref}}(SST)={u_ref:.2f}$)")
    leg = plt.legend(loc="best", fontsize=15.5)
    leg.set_zorder(100)
    plt.tight_layout(rect=[0, 0, 1, 1])
    plt.savefig(f"{figures_dir}/compareCfWall-CBFS.pdf")
    plt.close()

    # Ux profile comparison (00Baseline vs LES from 01Frozen Ux_LES)
    fig = plt.figure(figsize=(14, 6))

    # Draw wall line in plotting window if available
    xw = x_baseline
    yw = y / x_ref
    wall_mask = (xw > -1.0) & (xw < 11.0)
    if np.any(wall_mask):
        plt.plot(xw[wall_mask], yw[wall_mask], c="k")
    else:
        plt.plot(xw, yw, c="k")

    first_baseline = True
    first_les = True
    for loc, x_shift in zip(single_graph_locs, x_profile_locs):
        baseline_dict = readSingleGraphDir(f"{baseline_dir}/postProcessing/singleGraph_{loc}/")
        frozen_dict = readSingleGraphDir(f"{frozen_dir}/postProcessing/singleGraph_{loc}/")

        yb = np.array(baseline_dict["y"], dtype=float) / x_ref
        ub = np.array(baseline_dict["Ux"], dtype=float) / u_ref
        ules_key = "Ux_LES" if "Ux_LES" in frozen_dict else "Ux"
        frozen_order = np.argsort(np.asarray(frozen_dict["y"], dtype=float))
        yl = np.asarray(frozen_dict["y"], dtype=float)[frozen_order] / x_ref
        ul = np.asarray(frozen_dict[ules_key], dtype=float)[frozen_order] / u_ref
        ul_on_baseline = interp_with_nan(yb, yl, ul)
        u_pair_mask = finite_pair_mask(yb, ub, ul_on_baseline)
        yb_paired = yb[u_pair_mask]
        ub_paired = ub[u_pair_mask]
        ul_paired = ul_on_baseline[u_pair_mask]

        if yb_paired.size == 0:
            continue

        plt.plot([x_shift, x_shift], [yb[0], yb[-1]], c="lightgrey", lw=2, zorder=0)

        plt.plot(
            x_shift + np.array([0.0, *ub_paired]),
            np.array([yb_paired[0], *yb_paired]),
            c=colors[0],
            lw=2,
            linestyle=linestyles[0],
            label=labels[0] if first_baseline else "_nolegend_",
            marker=markers[0],
            markersize=ms,
            zorder=5,
        )
        first_baseline = False

        # LES overlay from frozen singleGraph output, paired to the SST y-grid.
        plt.plot(
            x_shift + np.array([0.0, *ul_paired]),
            np.array([yb_paired[0], *yb_paired]),
            c=colors[1],
            lw=0,
            linestyle="None",
            label=labels[1] if first_les else "_nolegend_",
            marker=markers[1],
            markersize=ms,
            zorder=5,
        )
        first_les = False

    plt.xlabel(r"$U_x/U_{ref} + x/h$ [-]", fontsize=23)
    plt.ylabel("y/h [-]", fontsize=23)
    plt.title(rf"Bottom-Wall Profiles Comparison ($U_{{ref}}(SST)={u_ref:.2f}$)")
    plt.legend(loc="best", fontsize=16)
    plt.ylim(0, 1.5)
    plt.xlim(0, 9)
    plt.yticks([0.00, 0.50, 1.00, 1.50])
    plt.xticks([1.00, 2.00, 3.00, 4.00, 5.00, 6.00, 7.00, 8.00])
    plt.tight_layout(rect=[0, 0, 1, 1])
    plt.savefig(f"{figures_dir}/compareUxProfiles_CBFS.pdf")
    plt.close(fig)

    # Reynolds shear stress profile comparison. For SST, uv is reconstructed
    # from sampled nut and gradU as -nut*(dUx/dy + dUy/dx). LES uses the
    # reference uv column.
    fig = plt.figure(figsize=(14, 6))
    if np.any(wall_mask):
        plt.plot(xw[wall_mask], yw[wall_mask], c="k")
    else:
        plt.plot(xw, yw, c="k")

    first_baseline = True
    first_les = True
    fuv = 50.0
    for loc, x_shift in zip(single_graph_locs, x_profile_locs):
        baseline_dict = readSingleGraphDir(f"{baseline_dir}/postProcessing/singleGraph_{loc}/")
        order_profile = np.argsort(np.asarray(baseline_dict["y"], dtype=float))
        for key in list(baseline_dict.keys()):
            baseline_dict[key] = np.asarray(baseline_dict[key], dtype=float)[order_profile]

        yb = baseline_dict["y"] / x_ref
        uvb = modeled_reynolds_shear(baseline_dict, u_ref)
        plt.plot([x_shift, x_shift], [yb[0], yb[-1]], c="lightgrey", lw=2, zorder=0)

        x_station = 0.0 if x_shift == 1e-6 else x_shift
        yl, uv_les = interpolate_les_profile(les_profile_grid, x_station, "uv/U_in^2")
        uv_les_on_sst = interp_with_nan(yb, yl, uv_les)
        uv_pair_mask = finite_pair_mask(yb, uvb, uv_les_on_sst)
        yb_paired = yb[uv_pair_mask]
        uvb_paired = uvb[uv_pair_mask]
        uv_les_paired = uv_les_on_sst[uv_pair_mask]

        if yb_paired.size == 0:
            continue

        plt.plot(
            x_shift + np.array([0.0, *fuv * uvb_paired]),
            np.array([yb_paired[0], *yb_paired]),
            c=colors[0],
            lw=2,
            linestyle=linestyles[0],
            label=labels[0] if first_baseline else "_nolegend_",
            marker=markers[0],
            markersize=ms,
            zorder=5,
        )
        first_baseline = False

        plt.plot(
            x_shift + fuv * uv_les_paired,
            yb_paired,
            c=colors[1],
            lw=0,
            linestyle="None",
            label=labels[1] if first_les else "_nolegend_",
            marker=markers[1],
            markersize=ms,
            zorder=5,
        )
        first_les = False

        frozen_dict = readSingleGraphDir(f"{frozen_dir}/postProcessing/singleGraph_{loc}/")
        ules_key = "Ux_LES" if "Ux_LES" in frozen_dict else "Ux"
        frozen_order = np.argsort(np.asarray(frozen_dict["y"], dtype=float))
        y_frozen = np.asarray(frozen_dict["y"], dtype=float)[frozen_order] / x_ref
        u_les = np.asarray(frozen_dict[ules_key], dtype=float)[frozen_order] / u_ref
        u_les_on_sst = interp_with_nan(yb, y_frozen, u_les)
        u_sst = baseline_dict["Ux"] / u_ref
        profile_pair_mask = finite_pair_mask(yb, u_sst, u_les_on_sst, uvb, uv_les_on_sst)

        for y_val, u0, u1, uv0, uv1 in zip(
            yb[profile_pair_mask],
            u_sst[profile_pair_mask],
            u_les_on_sst[profile_pair_mask],
            uvb[profile_pair_mask],
            uv_les_on_sst[profile_pair_mask],
        ):
            profile_rows.append(
                {
                    "station_x_over_h": x_station,
                    "wall_normal_over_h": y_val,
                    "Ux_over_Uref_RANS_SST": u0,
                    "Ux_over_Uref_LES": u1,
                    "uv_over_Uref2_RANS_SST": uv0,
                    "uv_over_Uref2_LES": uv1,
                }
            )

    plt.xlabel(r"$50uv/U_{ref}^2 + x/h$ [-]", fontsize=23)
    plt.ylabel("y/h [-]", fontsize=23)
    plt.title(rf"Reynolds Shear Stress Profiles ($U_{{ref}}(SST)={u_ref:.2f}$)")
    plt.legend(loc="best", fontsize=16)
    plt.ylim(0, 1.5)
    plt.xlim(0, 9)
    plt.yticks([0.00, 0.50, 1.00, 1.50])
    plt.xticks([1.00, 2.00, 3.00, 4.00, 5.00, 6.00, 7.00, 8.00])
    plt.tight_layout(rect=[0, 0, 1, 1])
    plt.savefig(f"{figures_dir}/compareuvProfiles_CBFS.pdf")
    plt.close(fig)

    write_csv(
        f"{figures_dir}/velocity_shear_profiles_CBFS.csv",
        [
            "station_x_over_h",
            "wall_normal_over_h",
            "Ux_over_Uref_RANS_SST",
            "Ux_over_Uref_LES",
            "uv_over_Uref2_RANS_SST",
            "uv_over_Uref2_LES",
        ],
        profile_rows,
    )

    print("Generated figures:")
    print(f" - {figures_dir}/compareCpWall-CBFS.pdf")
    print(f" - {figures_dir}/compareCfWall-CBFS.pdf")
    print(f" - {figures_dir}/compareUxProfiles_CBFS.pdf")
    print(f" - {figures_dir}/compareuvProfiles_CBFS.pdf")
    print("Generated CSV files:")
    print(f" - {figures_dir}/wall_Cp_Cf_CBFS.csv")
    print(f" - {figures_dir}/velocity_shear_profiles_CBFS.csv")


if __name__ == "__main__":
    main()
