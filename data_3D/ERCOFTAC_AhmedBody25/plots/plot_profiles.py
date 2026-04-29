"""Ahmed Body 25-deg validation plots — academic publication style.

4 wake-development y-z stations × 2 columns (Experimental | Baseline k-omega SST)
Filled-contour panels of U_x/U_ref with TwoSlopeNorm + Ahmed body outline.
Set MODEL_DIR env to add a 3rd column (submitted ML model overlay).

Source: ERCOFTAC case082, Lienhart-Becker-Stoots (LSTM Erlangen 2003).
    Re_h = 768 000, U_b = 40 m/s, h = 288 mm, slant = 222 mm @ 25 deg.
    Coordinates: x = 0 at body rear, y = 0 symmetry, z = 0 ground (mm units).

Run:    python plot_profiles.py
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.rcParams.update({'font.size': 13})
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from scipy.interpolate import griddata

HERE = os.path.dirname(os.path.abspath(__file__))
BASELINE = os.path.join(HERE, '..', 'baseline_komegasst')
EXPERIMENT = os.path.join(HERE, '..', 'highfidelity')
MODEL_DIR = os.environ.get('MODEL_DIR')

U_REF = 40.0  # bulk velocity m/s
H_MM = 288.0  # body height mm

# Ahmed body cross-section in y-z plane (mm)
BODY_Y = (-195, 195)
BODY_Z = (50, 50 + H_MM)  # 50 mm ground clearance + 288 mm height = top at 338 mm

# Wake-development stations: (filename_stem, x_label, has_body_at_x0)
STATIONS = [
    ('ahmed-25-xp000-yz', 'x/H = 0',     True),
    ('ahmed-25-xp080-yz', 'x/H = 0.28',  False),
    ('ahmed-25-xp200-yz', 'x/H = 0.69',  False),
    ('ahmed-25-xp500-yz', 'x/H = 1.74',  False),
]

DATA_TYPES = ['Experimental', 'Baseline k-ω SST']
if MODEL_DIR:
    DATA_TYPES.append('Submitted model')


def _safe_csv(path):
    return pd.read_csv(path) if os.path.isfile(path) else None


def interp_yz(df, val_col, ny=300, nz=300, y_lim=(-250, 250), z_lim=(0, 550)):
    """Interpolate (y_mm, z_mm, val) onto a regular grid."""
    pts = np.column_stack([df['y_mm'].values, df['z_mm'].values])
    vals = df[val_col].values
    Y, Z = np.meshgrid(np.linspace(*y_lim, ny), np.linspace(*z_lim, nz))
    near = griddata(pts, vals, (Y, Z), method='nearest')
    lin = griddata(pts, vals, (Y, Z), method='linear')
    mask = np.isnan(lin)
    lin[mask] = near[mask]
    return Y, Z, lin


def draw_body(ax):
    y0, y1 = BODY_Y
    z0, z1 = BODY_Z
    rect_x = [y0, y1, y1, y0, y0]
    rect_y = [z0, z0, z1, z1, z0]
    ax.fill(rect_x, rect_y, color='white', alpha=0.85, zorder=4)
    ax.plot(rect_x, rect_y, 'k-', lw=1.5, zorder=5)


def panel(ax, df, val_col, scale_factor, has_body, levels, norm, cmap):
    if df is None:
        ax.text(0.5, 0.5, 'no data', ha='center', va='center',
                transform=ax.transAxes, fontsize=12)
        return None
    Y, Z, F = interp_yz(df, val_col)
    F = F / scale_factor
    if has_body:
        # mask the field where the body sits
        body_mask = ((Y >= BODY_Y[0]) & (Y <= BODY_Y[1])
                     & (Z >= BODY_Z[0]) & (Z <= BODY_Z[1]))
        F = np.where(body_mask, np.nan, F)
    cf = ax.contourf(Y, Z, F, levels=levels, cmap=cmap, norm=norm, extend='both')
    ax.contour(Y, Z, F, levels=[0.0], colors='k', linewidths=0.75)
    if has_body:
        draw_body(ax)
    return cf


# ----- Streamwise wake-station U/U_ref grid -----
nrows, ncols = len(STATIONS), len(DATA_TYPES)
fig, axes = plt.subplots(nrows, ncols, figsize=(5*ncols, 4.5*nrows))
if nrows == 1: axes = axes[np.newaxis, :]
if ncols == 1: axes = axes[:, np.newaxis]

levels = np.linspace(-0.5, 1.25, 36)
norm = TwoSlopeNorm(vmin=-0.5, vcenter=0.0, vmax=1.25)
cmap = plt.cm.RdBu_r

cf_last = None
for i, (stem, _, has_body) in enumerate(STATIONS):
    exp = _safe_csv(os.path.join(EXPERIMENT, f'{stem}.csv'))
    base = _safe_csv(os.path.join(BASELINE,  f'{stem}.csv'))
    model = _safe_csv(os.path.join(MODEL_DIR, f'{stem}.csv')) if MODEL_DIR else None

    cf_last = panel(axes[i, 0], exp,  'U', U_REF, has_body, levels, norm, cmap) or cf_last
    cf_last = panel(axes[i, 1], base, 'U', U_REF, has_body, levels, norm, cmap) or cf_last
    if MODEL_DIR:
        cf_last = panel(axes[i, 2], model, 'U', U_REF, has_body, levels, norm, cmap) or cf_last

    for j in range(ncols):
        ax = axes[i, j]
        ax.set_xlim(-250, 250)
        ax.set_ylim(0, 550)
        ax.set_aspect('equal')
        ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
        if j == 0:
            ax.set_ylabel('z [mm]', fontsize=14)
        if i == nrows - 1:
            ax.set_xlabel('y [mm]', fontsize=14)
        if i == 0:
            ax.set_title(DATA_TYPES[j], fontsize=15, weight='bold')

# row labels with x station
for i, (_, lbl, _) in enumerate(STATIONS):
    fig.text(0.005, axes[i, 0].get_position().y0 + 0.5*axes[i, 0].get_position().height,
             lbl, rotation=90, fontsize=14, weight='bold', va='center')

# bottom horizontal colorbar
cbar_ax = fig.add_axes([0.18, 0.04, 0.65, 0.013])
cbar = fig.colorbar(cf_last, cax=cbar_ax, orientation='horizontal', extend='both')
cbar.set_label(r'$U_x / U_\mathrm{ref}$', fontsize=15)
cbar.set_ticks(np.arange(-0.5, 1.251, 0.25))

plt.tight_layout(rect=[0.04, 0.07, 0.99, 0.98])
plt.savefig(os.path.join(HERE, 'Ahmed25_wake_U_contours.pdf'), dpi=200)
plt.savefig(os.path.join(HERE, 'Ahmed25_wake_U_contours.png'), dpi=200)
plt.close()


# ----- Same grid for u'w'/U_ref^2 (Reynolds shear stress) -----
fig, axes = plt.subplots(nrows, ncols, figsize=(5*ncols, 4.5*nrows))
if nrows == 1: axes = axes[np.newaxis, :]
if ncols == 1: axes = axes[:, np.newaxis]

levels_uw = np.linspace(-0.025, 0.025, 36)
norm_uw = TwoSlopeNorm(vmin=-0.025, vcenter=0.0, vmax=0.025)

cf_last = None
for i, (stem, _, has_body) in enumerate(STATIONS):
    exp = _safe_csv(os.path.join(EXPERIMENT, f'{stem}.csv'))
    base = _safe_csv(os.path.join(BASELINE,  f'{stem}.csv'))
    model = _safe_csv(os.path.join(MODEL_DIR, f'{stem}.csv')) if MODEL_DIR else None

    if exp is not None and 'uw' in exp.columns:
        cf_last = panel(axes[i, 0], exp, 'uw', U_REF**2, has_body, levels_uw, norm_uw, cmap) or cf_last
    if base is not None and 'R_xz' in base.columns:
        cf_last = panel(axes[i, 1], base, 'R_xz', U_REF**2, has_body, levels_uw, norm_uw, cmap) or cf_last
    if MODEL_DIR and model is not None:
        col = 'R_xz' if 'R_xz' in model.columns else ('uw' if 'uw' in model.columns else None)
        if col:
            cf_last = panel(axes[i, 2], model, col, U_REF**2, has_body, levels_uw, norm_uw, cmap) or cf_last

    for j in range(ncols):
        ax = axes[i, j]
        ax.set_xlim(-250, 250); ax.set_ylim(0, 550)
        ax.set_aspect('equal')
        ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
        if j == 0: ax.set_ylabel('z [mm]', fontsize=14)
        if i == nrows - 1: ax.set_xlabel('y [mm]', fontsize=14)
        if i == 0: ax.set_title(DATA_TYPES[j], fontsize=15, weight='bold')

for i, (_, lbl, _) in enumerate(STATIONS):
    fig.text(0.005, axes[i, 0].get_position().y0 + 0.5*axes[i, 0].get_position().height,
             lbl, rotation=90, fontsize=14, weight='bold', va='center')

if cf_last is not None:
    cbar_ax = fig.add_axes([0.18, 0.04, 0.65, 0.013])
    cbar = fig.colorbar(cf_last, cax=cbar_ax, orientation='horizontal', extend='both')
    cbar.set_label(r"$\overline{u'w'} / U_\mathrm{ref}^2$", fontsize=15)
    cbar.set_ticks(np.linspace(-0.025, 0.025, 6))

plt.tight_layout(rect=[0.04, 0.07, 0.99, 0.98])
plt.savefig(os.path.join(HERE, 'Ahmed25_wake_uw_contours.pdf'), dpi=200)
plt.savefig(os.path.join(HERE, 'Ahmed25_wake_uw_contours.png'), dpi=200)
plt.close()


# ----- Same grid for TKE k/U_ref^2 -----
fig, axes = plt.subplots(nrows, ncols, figsize=(5*ncols, 4.5*nrows))
if nrows == 1: axes = axes[np.newaxis, :]
if ncols == 1: axes = axes[:, np.newaxis]

levels_k = np.linspace(0.0, 0.06, 31)
from matplotlib.colors import Normalize as _Normalize
norm_k = _Normalize(vmin=0.0, vmax=0.06)
cmap_k = plt.cm.viridis

cf_last = None
for i, (stem, _, has_body) in enumerate(STATIONS):
    exp = _safe_csv(os.path.join(EXPERIMENT, f'{stem}.csv'))
    base = _safe_csv(os.path.join(BASELINE,  f'{stem}.csv'))
    model = _safe_csv(os.path.join(MODEL_DIR, f'{stem}.csv')) if MODEL_DIR else None

    # exp k = 0.5*(urms^2 + vrms^2 + wrms^2); baseline has k directly
    if exp is not None and {'urms', 'vrms', 'wrms'}.issubset(exp.columns):
        exp = exp.copy(); exp['k'] = 0.5 * (exp['urms']**2 + exp['vrms']**2 + exp['wrms']**2)
        cf_last = panel(axes[i, 0], exp, 'k', U_REF**2, has_body, levels_k, norm_k, cmap_k) or cf_last
    if base is not None and 'k' in base.columns:
        cf_last = panel(axes[i, 1], base, 'k', U_REF**2, has_body, levels_k, norm_k, cmap_k) or cf_last
    if MODEL_DIR and model is not None and 'k' in model.columns:
        cf_last = panel(axes[i, 2], model, 'k', U_REF**2, has_body, levels_k, norm_k, cmap_k) or cf_last

    for j in range(ncols):
        ax = axes[i, j]
        ax.set_xlim(-250, 250); ax.set_ylim(0, 550)
        ax.set_aspect('equal')
        ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
        if j == 0: ax.set_ylabel('z [mm]', fontsize=14)
        if i == nrows - 1: ax.set_xlabel('y [mm]', fontsize=14)
        if i == 0: ax.set_title(DATA_TYPES[j], fontsize=15, weight='bold')

for i, (_, lbl, _) in enumerate(STATIONS):
    fig.text(0.005, axes[i, 0].get_position().y0 + 0.5*axes[i, 0].get_position().height,
             lbl, rotation=90, fontsize=14, weight='bold', va='center')

if cf_last is not None:
    cbar_ax = fig.add_axes([0.18, 0.04, 0.65, 0.013])
    cbar = fig.colorbar(cf_last, cax=cbar_ax, orientation='horizontal', extend='max')
    cbar.set_label(r'$k / U_\mathrm{ref}^2$', fontsize=15)
    cbar.set_ticks(np.linspace(0.0, 0.06, 7))

plt.tight_layout(rect=[0.04, 0.07, 0.99, 0.98])
plt.savefig(os.path.join(HERE, 'Ahmed25_wake_k_contours.pdf'), dpi=200)
plt.savefig(os.path.join(HERE, 'Ahmed25_wake_k_contours.png'), dpi=200)
plt.close()

# =================================================================
# (3) Stagger-line wake profiles: U(z) at multiple x downstream stations.
#     Source: ahmed-25-y000-whole.csv (dense y=0 plane, 10 wake stations
#     from x=38..638 mm); both exp and baseline have matching x stations.
# =================================================================
WAKE_X_STATIONS_MM = [38, 88, 138, 188, 238, 288, 338, 438, 538, 638]
SCALE_U_WAKE = 0.15  # 50 mm = 0.174 H spacing → 0.15 keeps profiles legible

EXP_KW2  = dict(color='k',     marker='o', ms=4.5, ls='', label='Exp.')
BASE_KW2 = dict(color='grey',  ls='--', lw=1.8, label='Baseline')
MODEL_KW2 = dict(color='green', ls='-',  lw=2.0, label='SL-Model')

custom_lines = [plt.Line2D([], [], **EXP_KW2), plt.Line2D([], [], **BASE_KW2)]
if MODEL_DIR: custom_lines.append(plt.Line2D([], [], **MODEL_KW2))


def slice_at_x(df, x_mm, x_tol=2.0):
    """Take constant-x slice from a y=0 streamwise plane, sorted by z."""
    if df is None: return None
    sub = df[np.abs(df['x_mm'] - x_mm) < x_tol].copy()
    if len(sub) == 0: return None
    return sub.sort_values('z_mm')


# --- wake station U profile stagger (symmetry plane) ---
exp_y0 = _safe_csv(os.path.join(EXPERIMENT, 'ahmed-25-y000-whole.csv'))
base_y0 = _safe_csv(os.path.join(BASELINE,  'ahmed-25-y000-whole.csv'))
model_y0 = _safe_csv(os.path.join(MODEL_DIR, 'ahmed-25-y000-whole.csv')) if MODEL_DIR else None

fig, ax = plt.subplots(figsize=(13, 6))
for x_mm in WAKE_X_STATIONS_MM:
    x_h = x_mm / H_MM
    exp = slice_at_x(exp_y0, x_mm)
    base = slice_at_x(base_y0, x_mm)
    if exp is not None:
        ax.plot(SCALE_U_WAKE * exp['U'].values / U_REF + x_h, exp['z_mm'].values / H_MM, **{**EXP_KW2, 'label': '_nolegend_'})
    if base is not None:
        ax.plot(SCALE_U_WAKE * base['U'].values / U_REF + x_h, base['z_mm'].values / H_MM, **{**BASE_KW2, 'label': '_nolegend_'})
    if model_y0 is not None:
        m = slice_at_x(model_y0, x_mm)
        if m is not None:
            ax.plot(SCALE_U_WAKE * m['U'].values / U_REF + x_h, m['z_mm'].values / H_MM, **{**MODEL_KW2, 'label': '_nolegend_'})
    ax.axvline(x_h, color='lightgray', lw=0.4, zorder=0)
    ax.text(x_h, 1.46, f'{x_mm:d}', ha='center', fontsize=9, color='dimgray')

# body underside (z=50 mm) and roof (z=338 mm) — useful eye-guides for wake structure
ax.axhline(50/H_MM, color='lightgray', ls=':', lw=0.6)
ax.axhline((50+H_MM)/H_MM, color='lightgray', ls=':', lw=0.6)
ax.text(0.02, 1.51, 'x [mm]:', fontsize=9, color='dimgray')

ax.legend(handles=custom_lines, loc='upper right', fontsize=11)
ax.set_xlim(0.0, 2.45); ax.set_ylim(0.0, 1.55)
ax.set_xlabel(rf'${SCALE_U_WAKE:g}\,U_x/U_\mathrm{{ref}} + x/H$  [-]', fontsize=14)
ax.set_ylabel(r'$z/H$  [-]', fontsize=14)
ax.set_title('Ahmed 25° — symmetry-plane (y=0) wake velocity profiles', fontsize=14)
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(HERE, 'Ahmed25_wake_profile_U.pdf'), dpi=200)
plt.savefig(os.path.join(HERE, 'Ahmed25_wake_profile_U.png'), dpi=200)
plt.close()


# --- wake station u'w' Reynolds shear-stress profile stagger ---
SCALE_UW_WAKE = 4.0   # uw/U_ref^2 is small; scale up to be visible

fig, ax = plt.subplots(figsize=(13, 6))
for x_mm in WAKE_X_STATIONS_MM:
    x_h = x_mm / H_MM
    exp = slice_at_x(exp_y0, x_mm)
    base = slice_at_x(base_y0, x_mm)
    if exp is not None and 'uw' in exp.columns:
        ax.plot(SCALE_UW_WAKE * exp['uw'].values / U_REF**2 + x_h, exp['z_mm'].values / H_MM, **{**EXP_KW2, 'label': '_nolegend_'})
    if base is not None and 'R_xz' in base.columns:
        ax.plot(SCALE_UW_WAKE * base['R_xz'].values / U_REF**2 + x_h, base['z_mm'].values / H_MM, **{**BASE_KW2, 'label': '_nolegend_'})
    if model_y0 is not None:
        m = slice_at_x(model_y0, x_mm)
        col = 'R_xz' if (m is not None and 'R_xz' in m.columns) else ('uw' if (m is not None and 'uw' in m.columns) else None)
        if col:
            ax.plot(SCALE_UW_WAKE * m[col].values / U_REF**2 + x_h, m['z_mm'].values / H_MM, **{**MODEL_KW2, 'label': '_nolegend_'})
    ax.axvline(x_h, color='lightgray', lw=0.4, zorder=0)
    ax.text(x_h, 1.46, f'{x_mm:d}', ha='center', fontsize=9, color='dimgray')

ax.axhline(50/H_MM, color='lightgray', ls=':', lw=0.6)
ax.axhline((50+H_MM)/H_MM, color='lightgray', ls=':', lw=0.6)
ax.text(0.02, 1.51, 'x [mm]:', fontsize=9, color='dimgray')

ax.legend(handles=custom_lines, loc='upper right', fontsize=11)
ax.set_xlim(0.0, 2.45); ax.set_ylim(0.0, 1.55)
ax.set_xlabel(rf"${SCALE_UW_WAKE:g}\,\overline{{u'w'}}/U_\mathrm{{ref}}^2 + x/H$  [-]", fontsize=14)
ax.set_ylabel(r'$z/H$  [-]', fontsize=14)
ax.set_title("Ahmed 25° — symmetry-plane wake Reynolds shear stress", fontsize=14)
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(HERE, 'Ahmed25_wake_profile_uw.pdf'), dpi=200)
plt.savefig(os.path.join(HERE, 'Ahmed25_wake_profile_uw.png'), dpi=200)
plt.close()


# =================================================================
# (4) Stagger-line slant-region profiles: U(z) along the body side
#     Uses x-z planes at y=0, 100, 180 mm (over slant)
# =================================================================
SLANT_STATIONS = [
    ('ahmed-25-yp000-xz', 'y=0'),
    ('ahmed-25-yp100-xz', 'y=100'),
    ('ahmed-25-yp180-xz', 'y=180'),
]

# Stations match the LSTM Erlangen y=0 x-z plane sampling (every 20 mm from -243 to -3).
SLANT_X_STATIONS_MM = [-243, -203, -183, -163, -143, -123, -103, -83, -63, -43, -23, -3]
SCALE_U_SLANT = 0.05  # tight scaling so 12 profiles fit side-by-side without overlap

# Ahmed body 25-deg slant geometry. Slant LENGTH (along the slant) = 222 mm.
SLANT_LEN_MM   = 222.0
SLANT_ANGLE    = np.deg2rad(25.0)
SLANT_DX_MM    = SLANT_LEN_MM * np.cos(SLANT_ANGLE)   # ~201 mm horizontal extent
SLANT_DZ_MM    = SLANT_LEN_MM * np.sin(SLANT_ANGLE)   # ~93.8 mm vertical drop
TOP_Z_H        = (50 + H_MM) / H_MM                   # ~1.174 (top of body / slant top)
REAR_Z_H       = (50 + H_MM - SLANT_DZ_MM) / H_MM     # ~0.848 (slant base / rear top)
SLANT_TOP_X_H  = -SLANT_DX_MM / H_MM                  # ~-0.698 (where slant begins)

fig, ax = plt.subplots(figsize=(10, 6))
exp_xz = _safe_csv(os.path.join(EXPERIMENT, 'ahmed-25-yp000-xz.csv'))
base_xz = _safe_csv(os.path.join(BASELINE,  'ahmed-25-yp000-xz.csv'))

for x_mm in SLANT_X_STATIONS_MM:
    x_h = x_mm / H_MM
    band_exp = exp_xz[np.abs(exp_xz['x_mm'] - x_mm) < 2] if exp_xz is not None else None
    band_base = base_xz[np.abs(base_xz['x_mm'] - x_mm) < 2] if base_xz is not None else None
    if band_exp is not None and len(band_exp) > 0:
        b = band_exp.sort_values('z_mm')
        ax.plot(SCALE_U_SLANT * b['U'].values / U_REF + x_h, b['z_mm'].values / H_MM, **{**EXP_KW2, 'label': '_nolegend_'})
    if band_base is not None and len(band_base) > 0:
        b = band_base.sort_values('z_mm')
        ax.plot(SCALE_U_SLANT * b['U'].values / U_REF + x_h, b['z_mm'].values / H_MM, **{**BASE_KW2, 'label': '_nolegend_'})
    ax.axvline(x_h, color='lightgray', lw=0.4, zorder=0)

# Body profile: horizontal roof up to slant edge, then 25-deg slant down to rear top.
ax.plot([-1.05, SLANT_TOP_X_H], [TOP_Z_H, TOP_Z_H], 'k-', lw=1.5, zorder=5)
ax.plot([SLANT_TOP_X_H, 0.0],   [TOP_Z_H, REAR_Z_H], 'k-', lw=1.5, zorder=5)

ax.legend(handles=custom_lines, loc='lower left', fontsize=12)
ax.set_xlim(-0.95, 0.10); ax.set_ylim(0.83, 1.40)
ax.set_xlabel(rf'${SCALE_U_SLANT:g}\,U_x/U_\mathrm{{ref}} + x/H$  [-]', fontsize=14)
ax.set_ylabel(r'$z/H$  [-]', fontsize=14)
ax.set_title('Ahmed 25° — slant-region (y=0) velocity profiles', fontsize=14)
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(HERE, 'Ahmed25_slant_profile_U.pdf'), dpi=200)
plt.savefig(os.path.join(HERE, 'Ahmed25_slant_profile_U.png'), dpi=200)
plt.close()


# =================================================================
# (5) TKE profile stagger — slant + wake.
#     Experimental k = 0.5 (urms^2 + vrms^2 + wrms^2); baseline reads k directly.
# =================================================================
def k_exp(df):
    if df is None or not {'urms', 'vrms', 'wrms'}.issubset(df.columns):
        return None
    return 0.5 * (df['urms']**2 + df['vrms']**2 + df['wrms']**2)

# --- slant TKE ---
SCALE_K_SLANT = 0.5  # k/U_ref^2 ~ 0.05 typical, scale up for visibility
fig, ax = plt.subplots(figsize=(10, 6))
exp_xz = _safe_csv(os.path.join(EXPERIMENT, 'ahmed-25-yp000-xz.csv'))
base_xz = _safe_csv(os.path.join(BASELINE,  'ahmed-25-yp000-xz.csv'))
for x_mm in SLANT_X_STATIONS_MM:
    x_h = x_mm / H_MM
    be = exp_xz[np.abs(exp_xz['x_mm'] - x_mm) < 2] if exp_xz is not None else None
    bb = base_xz[np.abs(base_xz['x_mm'] - x_mm) < 2] if base_xz is not None else None
    if be is not None and len(be) > 0:
        s = be.sort_values('z_mm'); ke = k_exp(s)
        ax.plot(SCALE_K_SLANT * ke.values / U_REF**2 + x_h, s['z_mm'].values / H_MM, **{**EXP_KW2, 'label': '_nolegend_'})
    if bb is not None and len(bb) > 0 and 'k' in bb.columns:
        s = bb.sort_values('z_mm')
        ax.plot(SCALE_K_SLANT * s['k'].values / U_REF**2 + x_h, s['z_mm'].values / H_MM, **{**BASE_KW2, 'label': '_nolegend_'})
    ax.axvline(x_h, color='lightgray', lw=0.4, zorder=0)
ax.plot([-1.05, SLANT_TOP_X_H], [TOP_Z_H, TOP_Z_H], 'k-', lw=1.5, zorder=5)
ax.plot([SLANT_TOP_X_H, 0.0],   [TOP_Z_H, REAR_Z_H], 'k-', lw=1.5, zorder=5)
ax.legend(handles=custom_lines, loc='lower left', fontsize=12)
ax.set_xlim(-0.95, 0.10); ax.set_ylim(0.83, 1.40)
ax.set_xlabel(rf'${SCALE_K_SLANT:g}\,k/U_\mathrm{{ref}}^2 + x/H$  [-]', fontsize=14)
ax.set_ylabel(r'$z/H$  [-]', fontsize=14)
ax.set_title('Ahmed 25° — slant-region (y=0) TKE profiles', fontsize=14)
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(HERE, 'Ahmed25_slant_profile_k.pdf'), dpi=200)
plt.savefig(os.path.join(HERE, 'Ahmed25_slant_profile_k.png'), dpi=200)
plt.close()

# --- wake TKE ---
SCALE_K_WAKE = 1.0
fig, ax = plt.subplots(figsize=(13, 6))
for x_mm in WAKE_X_STATIONS_MM:
    x_h = x_mm / H_MM
    e = slice_at_x(exp_y0, x_mm)
    b = slice_at_x(base_y0, x_mm)
    if e is not None:
        ke = k_exp(e)
        if ke is not None:
            ax.plot(SCALE_K_WAKE * ke.values / U_REF**2 + x_h, e['z_mm'].values / H_MM, **{**EXP_KW2, 'label': '_nolegend_'})
    if b is not None and 'k' in b.columns:
        ax.plot(SCALE_K_WAKE * b['k'].values / U_REF**2 + x_h, b['z_mm'].values / H_MM, **{**BASE_KW2, 'label': '_nolegend_'})
    ax.axvline(x_h, color='lightgray', lw=0.4, zorder=0)
    ax.text(x_h, 1.46, f'{x_mm:d}', ha='center', fontsize=9, color='dimgray')
ax.axhline(50/H_MM, color='lightgray', ls=':', lw=0.6)
ax.axhline((50+H_MM)/H_MM, color='lightgray', ls=':', lw=0.6)
ax.text(0.02, 1.51, 'x [mm]:', fontsize=9, color='dimgray')
ax.legend(handles=custom_lines, loc='upper right', fontsize=11)
ax.set_xlim(0.0, 2.45); ax.set_ylim(0.0, 1.55)
ax.set_xlabel(rf'${SCALE_K_WAKE:g}\,k/U_\mathrm{{ref}}^2 + x/H$  [-]', fontsize=14)
ax.set_ylabel(r'$z/H$  [-]', fontsize=14)
ax.set_title('Ahmed 25° — symmetry-plane wake TKE profiles', fontsize=14)
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(HERE, 'Ahmed25_wake_profile_k.pdf'), dpi=200)
plt.savefig(os.path.join(HERE, 'Ahmed25_wake_profile_k.png'), dpi=200)
plt.close()


# =================================================================
# (6) Surface Cp on rear of body — slant centerline + base centerline.
# =================================================================
exp_cp = _safe_csv(os.path.join(EXPERIMENT, 'ahmed-25-press.csv'))
base_cp = _safe_csv(os.path.join(BASELINE, 'ahmed-25-press.csv'))

if exp_cp is not None and base_cp is not None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    # --- slant: Cp vs x/H along centerline (z > 244 mm = above slant base) ---
    ax = axes[0]
    e_sl = exp_cp[(np.abs(exp_cp.y_mm) < 1) & (exp_cp.z_mm > 244)].sort_values('x_mm')
    b_sl = base_cp[(np.abs(base_cp.y_mm) < 1) & (base_cp.z_mm > 244)].sort_values('x_mm')
    if len(e_sl):
        ax.plot(e_sl.x_mm / H_MM, e_sl.Cp, **{**EXP_KW2, 'label': 'Exp.'})
    if len(b_sl):
        ax.plot(b_sl.x_mm / H_MM, b_sl.Cp, **{**BASE_KW2, 'label': 'Baseline'})
    ax.axhline(0, color='lightgray', lw=0.5)
    ax.set_xlabel(r'$x/H$  [-]', fontsize=13)
    ax.set_ylabel(r'$C_p$  [-]', fontsize=13)
    ax.set_title('Slant centerline (y=0)', fontsize=13)
    ax.grid(alpha=0.3); ax.legend(fontsize=11)
    ax.invert_yaxis()  # Cp convention: negative up

    # --- base: Cp vs z/H along x=0 ---
    ax = axes[1]
    e_b = exp_cp[(np.abs(exp_cp.y_mm) < 1) & (np.abs(exp_cp.x_mm) < 1)].sort_values('z_mm')
    b_b = base_cp[(np.abs(base_cp.y_mm) < 1) & (np.abs(base_cp.x_mm) < 1)].sort_values('z_mm')
    if len(e_b):
        ax.plot(e_b.Cp, e_b.z_mm / H_MM, **{**EXP_KW2, 'label': 'Exp.'})
    if len(b_b):
        ax.plot(b_b.Cp, b_b.z_mm / H_MM, **{**BASE_KW2, 'label': 'Baseline'})
    ax.axvline(0, color='lightgray', lw=0.5)
    ax.set_xlabel(r'$C_p$  [-]', fontsize=13)
    ax.set_ylabel(r'$z/H$  [-]', fontsize=13)
    ax.set_title('Base centerline (x=0)', fontsize=13)
    ax.grid(alpha=0.3); ax.legend(fontsize=11)

    fig.suptitle('Ahmed 25° — surface pressure (rear of body)', fontsize=14)
    plt.tight_layout()
    plt.savefig(os.path.join(HERE, 'Ahmed25_Cp_rear.pdf'), dpi=200)
    plt.savefig(os.path.join(HERE, 'Ahmed25_Cp_rear.png'), dpi=200)
    plt.close()

print(f'Wrote contour + profile plots to {HERE}')
