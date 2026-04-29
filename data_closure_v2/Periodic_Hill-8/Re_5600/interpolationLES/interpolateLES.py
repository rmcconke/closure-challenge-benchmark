#!/usr/bin/env python3
"""Interpolate LES reference data onto the Re_10595 frozen-case mesh.

This mirrors the SquareDuct interpolation workflow (scipy.griddata + OpenFOAM
include-style field snippets) but uses the periodic-hill reference file:
  Re_10595/RefData/Hill_Breuer.csv

Outputs are written to:
  interpolationLES/interpolatedFields/U_LES
  interpolationLES/interpolatedFields/tauij_LES
  interpolationLES/interpolatedFields/k_LES
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy.interpolate import griddata

from readOFInternalField import readOFInternalField
from writeOFFieldFile import writeOFFieldFile


def _required_columns(arr: np.ndarray, required: list[str]) -> None:
    names = set(arr.dtype.names or ())
    missing = [col for col in required if col not in names]
    if missing:
        raise ValueError(f"Missing required CSV columns: {missing}")


def load_reference_fields(csv_path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Read Hill_Breuer.csv and build interpolation inputs.

    Returns:
      points: (N, 2) array of (x, y)
      values: (N, 10) array with columns:
          [Ux, Uy, Uz, tau11, tau12, tau13, tau22, tau23, tau33, k]
    """
    raw = np.genfromtxt(csv_path, delimiter=",", names=True)
    required = ["x", "y", "um", "vm", "uu", "vv", "ww", "uv"]
    _required_columns(raw, required)

    x = np.asarray(raw["x"], dtype=float)
    y = np.asarray(raw["y"], dtype=float)
    um = np.asarray(raw["um"], dtype=float)
    vm = np.asarray(raw["vm"], dtype=float)
    uu = np.asarray(raw["uu"], dtype=float)
    vv = np.asarray(raw["vv"], dtype=float)
    ww = np.asarray(raw["ww"], dtype=float)
    uv = np.asarray(raw["uv"], dtype=float)

    # The frozen periodic-hill case is 2D (empty in z), so z-velocity and xz/yz
    # stresses are set to zero consistently with existing case fields.
    zeros = np.zeros_like(um)
    k = 0.5 * (uu + vv + ww)

    points = np.column_stack((x, y))
    values = np.column_stack((um, vm, zeros, uu, uv, zeros, vv, zeros, ww, k))

    finite_mask = np.isfinite(points).all(axis=1) & np.isfinite(values).all(axis=1)
    if not finite_mask.any():
        raise ValueError(f"No finite interpolation data found in: {csv_path}")

    return points[finite_mask], values[finite_mask]


def interpolate_with_nearest_fallback(
    points: np.ndarray,
    values: np.ndarray,
    query_points: np.ndarray,
) -> np.ndarray:
    """Linear interpolation with nearest fallback for out-of-hull points."""
    interp_linear = griddata(points, values, query_points, method="linear")
    if np.isnan(interp_linear).any():
        interp_nearest = griddata(points, values, query_points, method="nearest")
        nan_mask = np.isnan(interp_linear)
        interp_linear[nan_mask] = interp_nearest[nan_mask]
    return interp_linear


def main() -> None:
    here = Path(__file__).resolve().parent
    case_root = here.parent

    ref_csv = case_root / "RefData" / "Hill_Breuer.csv"
    cell_centres_file = case_root / "01Frozen" / "constant" / "C"
    out_dir = here / "interpolatedFields"
    out_dir.mkdir(parents=True, exist_ok=True)

    if not ref_csv.exists():
        raise FileNotFoundError(f"Reference CSV not found: {ref_csv}")
    if not cell_centres_file.exists():
        raise FileNotFoundError(f"Cell-centres file not found: {cell_centres_file}")

    cell_centres = readOFInternalField(str(cell_centres_file))
    if cell_centres.ndim != 2 or cell_centres.shape[1] < 2:
        raise ValueError(f"Unexpected cell-centres shape: {cell_centres.shape}")
    query_xy = cell_centres[:, :2]

    ref_points, ref_values = load_reference_fields(ref_csv)
    interp_values = interpolate_with_nearest_fallback(ref_points, ref_values, query_xy)

    u_interp = interp_values[:, 0:3]
    tau_interp = interp_values[:, 3:9]
    k_interp = interp_values[:, 9:10]

    writeOFFieldFile(u_interp, "vector", str(out_dir / "U_LES"))
    writeOFFieldFile(tau_interp, "symmTensor", str(out_dir / "tauij_LES"))
    writeOFFieldFile(k_interp, "scalar", str(out_dir / "k_LES"))

    print(f"Interpolated {len(query_xy)} mesh points from {len(ref_points)} reference points.")
    print(f"Wrote: {out_dir / 'U_LES'}")
    print(f"Wrote: {out_dir / 'tauij_LES'}")
    print(f"Wrote: {out_dir / 'k_LES'}")


if __name__ == "__main__":
    main()

