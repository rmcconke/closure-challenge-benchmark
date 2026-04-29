# 2DN00 — High-fidelity reference

## Files
| File | Description | Source |
|------|-------------|--------|
| `CLCD_Ladson_expdata.dat` / `.csv` | NACA 0012 polar (CL, CD vs α). Three zones: 80 grit / 120 grit / 180 grit (transition trip configurations) | Ladson, *Effects of Independent Variation of Mach and Reynolds Numbers on the Low-Speed Aerodynamic Characteristics of the NACA 0012 Airfoil Section*, NASA TM 4074, 1988. Re = 6×10⁶, M = 0.15, transition tripped. |
| `CP_Gregory_expdata.dat` / `.csv`  | Cp vs x/c, upper surface only. Multiple zones for different α | Gregory & O'Reilly, NASA R&M 3726, January 1970. Re = 2.88×10⁶. Note: data digitized from a photocopy — only approximate. |
| `n0012cp_cfl3d_sst.dat` / `.csv`   | NASA CFL3D code Cp reference (SST model) on 897×257 grid. Multiple α zones for cross-checking baseline. Includes point-vortex farfield correction | NASA TMR. Note: results very near T.E. have high numerical error (Swanson & Turkel, AIAA 87-1107, 1987) |

`.dat` files are NASA Tecplot zone format. `.csv` versions are flat tables with a `zone` column.

For the challenge, scoring against experiment uses **Ladson** for CL/CD and **Gregory** for Cp. CFL3D is a CFD-vs-CFD cross-check (does our k-ω SST agree with NASA's reference SST implementation?), not a primary scoring reference.
