"""Faith Hill validation plots — academic publication style.

Source: NASA TMR Faith Hill — Bell, Heineck, Zilliac, Mehta, Long. AIAA 2012-0704.
    Re_h = 500 000, U_inf = 50.3 m/s (M=0.143), h = 152.4 mm = 6 in.
    Bump shape h(r) = 3 cos(pi r/9) + 3 [in], axisymmetric, ground-mounted.

Plots:
    1) PIV centerline contour (Exp | Baseline) U_x/U_inf
    2) PIV centerline contour (Exp | Baseline) k/U_inf^2
    3) Stagger-line velocity profiles at multiple downstream x/h stations
    4) Stagger-line TKE profiles at the same stations
    5) PSP centerline 1D Cp(x) — Exp + Baseline overlay (with upstream-Cp offset
       subtracted so curves are referenced to undisturbed-flow upstream)
    6) FISF surface Cf — top-down (Exp + Baseline if available)

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

H_MM = 152.4   # hill height
H_IN = 6.0
U_REF = 50.3   # m/s

DATA_TYPES = ['Experimental', 'Baseline k-ω SST']
if MODEL_DIR:
    DATA_TYPES.append('Submitted model')

EXP_KW   = dict(color='k',     marker='o', ms=4.5, ls='', label='Exp.')
BASE_KW  = dict(color='grey',  ls='--', lw=1.8, label='Baseline')
MODEL_KW = dict(color='green', ls='-',  lw=2.0, label='SL-Model')


def _safe_csv(path):
    return pd.read_csv(path) if os.path.isfile(path) else None


def hill_profile_in():
    """h(r) = 3 cos(pi r/9) + 3 inches, |r|<=9 in."""
    x = np.linspace(-9, 9, 200)
    y = np.where(np.abs(x) <= 9, 3.0 * np.cos(np.pi * x / 9.0) + 3.0, 0.0)
    return x, y


def interp_xy(df, val_col, ny=300, nx=300, x_lim=(-150, 600), y_lim=(0, 400)):
    """Interpolate onto regular (X,Y) grid. Drop rows where the field is NaN
    (probe failures) so the interpolant doesn't fill missing regions with
    spurious zeros via nearest-neighbor."""
    sub = df[['x_mm', 'y_mm', val_col]].dropna(subset=[val_col])
    pts = np.column_stack([sub['x_mm'].values, sub['y_mm'].values])
    vals = sub[val_col].values
    X, Y = np.meshgrid(np.linspace(*x_lim, nx), np.linspace(*y_lim, ny))
    # Use linear only — leave outside-convex-hull points as NaN so they show as
    # masked (no data) instead of being filled with bleeding nearest values.
    lin = griddata(pts, vals, (X, Y), method='linear')
    return X / H_MM, Y / H_MM, lin


def _wall_y_over_h(x_over_h):
    """Wall y/h at any x/h on the centerline. h(r)=3 cos(pi r/9)+3 in for |r|<=9."""
    r_in = np.abs(x_over_h * H_IN)
    yw_in = np.where(r_in <= 9.0, 3.0 * np.cos(np.pi * r_in / 9.0) + 3.0, 0.0)
    return yw_in / H_IN


def panel_piv(ax, df, val_col, scale, levels, norm, cmap, mark_zero=True):
    if df is None or val_col not in df.columns:
        ax.text(0.5, 0.5, 'no data', ha='center', va='center', transform=ax.transAxes)
        return None
    Xh, Yh, F = interp_xy(df, val_col)
    F = F / scale
    # Mask everything at or below the wall surface so the contour does not
    # bleed into the body or appear in regions that have no fluid data.
    yw = _wall_y_over_h(Xh)
    F = np.where(Yh < yw, np.nan, F)
    cf = ax.contourf(Xh, Yh, F, levels=levels, cmap=cmap, norm=norm, extend='both')
    if mark_zero:
        ax.contour(Xh, Yh, F, levels=[0.0], colors='k', linewidths=0.6)
    xh, yh = hill_profile_in()
    ax.fill_between(xh / H_IN, 0, yh / H_IN, color='white', alpha=1.0, zorder=4)
    ax.plot(xh / H_IN, yh / H_IN, 'k-', lw=1.5, zorder=5)
    return cf


def extract_profile_at_x(df, x_in_h, var, scale, dx_h=0.05, ny_bins=40,
                         y_min=0.0, y_max=1.4, min_per_bin=1):
    """Vertical profile of `var/scale` at x/h ~= x_in_h, averaged into y/h bins.

    Drops samples below the local wall y_wall(x)/h since those PIV pixels are
    inside the bump body. Bins along y/h so the cloud collapses to a clean
    ~ny_bins-long profile matching the Ahmed style."""
    x_target_mm = x_in_h * H_MM
    band = df[(df['x_mm'] >= x_target_mm - dx_h * H_MM) &
              (df['x_mm'] <= x_target_mm + dx_h * H_MM)].copy()
    if len(band) == 0:
        return None, None
    band = band.dropna(subset=[var])
    if len(band) == 0:
        return None, None
    # Local wall height at this station (centerline -> r = |x|).
    r_in = abs(x_in_h * H_IN)
    y_wall_h = (3.0 * np.cos(np.pi * r_in / 9.0) + 3.0) / H_IN if r_in <= 9.0 else 0.0
    band['_yh'] = band['y_mm'] / H_MM
    band = band[band['_yh'] >= y_wall_h]
    if len(band) == 0:
        return None, None
    bins = np.linspace(max(y_min, y_wall_h), y_max, ny_bins + 1)
    band['_b'] = pd.cut(band['_yh'], bins, include_lowest=True)
    g = (band.groupby('_b', observed=True)
              .agg(yh=('_yh', 'mean'), v=(var, 'mean'), n=(var, 'count'))
              .dropna())
    g = g[g['n'] >= min_per_bin].sort_values('yh')
    if len(g) == 0:
        return None, None
    return g['v'].values / scale, g['yh'].values


# =================================================================
# (1) and (2) -- PIV contour panels
# =================================================================
exp = _safe_csv(os.path.join(EXPERIMENT, 'PIV_centerline_2Hz_4000samps.csv'))
base = _safe_csv(os.path.join(BASELINE,  'PIV_centerline_2Hz_4000samps.csv'))

ncols = len(DATA_TYPES)
for fname, var, exp_scale, base_scale, levels, norm, cmap, label, mark_zero in [
    ('FaithHill_PIV_U_contours', 'U_mean', U_REF, 1.0,
        np.linspace(-0.3, 1.3, 33),
        TwoSlopeNorm(vmin=-0.3, vcenter=0.0, vmax=1.3),
        plt.cm.RdBu_r, r'$U_x / U_\infty$', True),
    ('FaithHill_PIV_k_contours', 'k', U_REF**2, 1.0,
        np.linspace(0, 0.04, 21),
        matplotlib.colors.Normalize(vmin=0, vmax=0.04),
        plt.cm.viridis, r'$k / U_\infty^2$', False),
]:
    fig, axes = plt.subplots(1, ncols, figsize=(6 * ncols, 4.5), sharey=True)
    if ncols == 1: axes = np.array([axes])
    cf_last = panel_piv(axes[0], exp,  var, exp_scale, levels, norm, cmap, mark_zero)
    cf_last = panel_piv(axes[1], base, var, base_scale, levels, norm, cmap, mark_zero) or cf_last
    if MODEL_DIR:
        m = _safe_csv(os.path.join(MODEL_DIR, 'PIV_centerline_2Hz_4000samps.csv'))
        cf_last = panel_piv(axes[2], m, var, exp_scale, levels, norm, cmap, mark_zero) or cf_last
    for j, ax in enumerate(axes):
        ax.set_xlim(-1, 4); ax.set_ylim(0, 2.5)
        ax.set_aspect('equal')
        ax.set_xlabel('x/h', fontsize=14)
        if j == 0: ax.set_ylabel('y/h', fontsize=14)
        ax.set_title(DATA_TYPES[j], fontsize=15, weight='bold')
    cbar_ax = fig.add_axes([0.20, 0.06, 0.6, 0.025])
    cbar = fig.colorbar(cf_last, cax=cbar_ax, orientation='horizontal', extend='both')
    cbar.set_label(label, fontsize=14)
    plt.tight_layout(rect=[0, 0.10, 1, 0.98])
    plt.savefig(os.path.join(HERE, f'{fname}.pdf'), dpi=200)
    plt.savefig(os.path.join(HERE, f'{fname}.png'), dpi=200)
    plt.close()


# =================================================================
# (3) Stagger-line VELOCITY profiles at multiple x/h stations
# =================================================================
STATIONS = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0]
SCALE_U = 0.5   # multiplier for offsetting profiles on x-axis

fig, ax = plt.subplots(figsize=(10, 6))
for x_h in STATIONS:
    if exp is not None:
        u, y = extract_profile_at_x(exp, x_h, 'U_mean', U_REF)
        if u is not None and len(u) > 0:
            ax.plot(SCALE_U * u + x_h, y, **{**EXP_KW, 'label': '_nolegend_'})
    if base is not None:
        u, y = extract_profile_at_x(base, x_h, 'U_mean', 1.0)
        if u is not None and len(u) > 0:
            ax.plot(SCALE_U * u + x_h, y, **{**BASE_KW, 'label': '_nolegend_'})
    if MODEL_DIR:
        m = _safe_csv(os.path.join(MODEL_DIR, 'PIV_centerline_2Hz_4000samps.csv'))
        if m is not None:
            u, y = extract_profile_at_x(m, x_h, 'U_mean', U_REF)
            if u is not None and len(u) > 0:
                ax.plot(SCALE_U * u + x_h, y, **{**MODEL_KW, 'label': '_nolegend_'})
    # vertical reference line at x_h
    ax.axvline(x_h, ymin=0, ymax=1, color='lightgray', lw=0.5, zorder=0)

# bump outline
xh, yh = hill_profile_in()
ax.plot(xh / H_IN, yh / H_IN, 'k-', lw=1.5, zorder=5)

# legend handles (manual, only one entry per data source)
custom_lines = []
if exp is not None: custom_lines.append(plt.Line2D([], [], **EXP_KW))
if base is not None: custom_lines.append(plt.Line2D([], [], **BASE_KW))
if MODEL_DIR: custom_lines.append(plt.Line2D([], [], **MODEL_KW))
ax.legend(handles=custom_lines, loc='upper left', fontsize=11)

ax.set_xlim(-0.5, 3.5); ax.set_ylim(0, 1.4)
ax.set_xlabel(rf'${SCALE_U:g}\,U_x/U_\infty + x/h$  [-]', fontsize=14)
ax.set_ylabel(r'$y/h$  [-]', fontsize=14)
ax.set_title('Faith Hill — axial velocity profiles along centerline', fontsize=14)
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(HERE, 'FaithHill_profile_U.pdf'), dpi=200)
plt.savefig(os.path.join(HERE, 'FaithHill_profile_U.png'), dpi=200)
plt.close()


# =================================================================
# (4) Stagger-line TKE profiles
# =================================================================
SCALE_K = 2.0

fig, ax = plt.subplots(figsize=(10, 6))
for x_h in STATIONS:
    if exp is not None and 'k' in exp.columns:
        k, y = extract_profile_at_x(exp, x_h, 'k', U_REF**2)
        if k is not None and len(k) > 0:
            ax.plot(SCALE_K * k + x_h, y, **{**EXP_KW, 'label': '_nolegend_'})
    if base is not None and 'k' in base.columns:
        k, y = extract_profile_at_x(base, x_h, 'k', 1.0)
        if k is not None and len(k) > 0:
            ax.plot(SCALE_K * k + x_h, y, **{**BASE_KW, 'label': '_nolegend_'})
    if MODEL_DIR:
        m = _safe_csv(os.path.join(MODEL_DIR, 'PIV_centerline_2Hz_4000samps.csv'))
        if m is not None and 'k' in m.columns:
            k, y = extract_profile_at_x(m, x_h, 'k', U_REF**2)
            if k is not None and len(k) > 0:
                ax.plot(SCALE_K * k + x_h, y, **{**MODEL_KW, 'label': '_nolegend_'})
    ax.axvline(x_h, ymin=0, ymax=1, color='lightgray', lw=0.5, zorder=0)

ax.plot(xh / H_IN, yh / H_IN, 'k-', lw=1.5, zorder=5)
ax.legend(handles=custom_lines, loc='upper left', fontsize=11)
ax.set_xlim(-0.5, 3.5); ax.set_ylim(0, 1.4)
ax.set_xlabel(rf'${SCALE_K:g}\,k/U_\infty^2 + x/h$  [-]', fontsize=14)
ax.set_ylabel(r'$y/h$  [-]', fontsize=14)
ax.set_title('Faith Hill — TKE profiles along centerline', fontsize=14)
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(HERE, 'FaithHill_profile_k.pdf'), dpi=200)
plt.savefig(os.path.join(HERE, 'FaithHill_profile_k.png'), dpi=200)
plt.close()


# =================================================================
# (5) PSP Cp(x) — referenced to upstream value
# =================================================================
def _ref_upstream(df, col='Cp', x_col='x_in', x_thresh=-7.0):
    if df is None or col not in df.columns:
        return df, 0.0
    upstream = df[df[x_col] < x_thresh]
    ref = upstream[col].mean() if len(upstream) else 0.0
    df = df.copy()
    df[col] = df[col] - ref
    return df, ref


def _smooth_cp(df, x_col='x_in', y_col='Cp', x_lim=(-9, 9), nbins=80):
    """Bin the PSP samples along x and return the mean Cp per bin so the
    raw-PSP optical noise is averaged out. Returns the bin centres and means.
    Drops bins that contain fewer than 2 samples or whose mean exceeds an
    obvious clipping threshold (already handled upstream)."""
    if df is None or y_col not in df.columns:
        return None, None
    bins = np.linspace(*x_lim, nbins + 1)
    d = df.copy()
    d['_b'] = pd.cut(d[x_col], bins, include_lowest=True)
    g = d.groupby('_b', observed=True).agg(x=(x_col, 'mean'), Cp=(y_col, 'mean'),
                                           n=(y_col, 'count')).dropna()
    g = g[g['n'] >= 2].sort_values('x')
    return g['x'].values, g['Cp'].values


fig, ax = plt.subplots(figsize=(8, 4.5))
psp_exp_raw  = _safe_csv(os.path.join(EXPERIMENT, 'PSP_centerline_p150.csv'))
psp_base_raw = _safe_csv(os.path.join(BASELINE,  'PSP_centerline_p150.csv'))
psp_exp,  ref_e = _ref_upstream(psp_exp_raw)
psp_base, ref_b = _ref_upstream(psp_base_raw)

if psp_exp is not None:
    # Show raw PSP samples as a faint scatter, plus a binned-mean curve so the
    # underlying trend is readable through the optical noise.
    ax.plot(psp_exp['x_in'] / H_IN, psp_exp['Cp'], '.', color='k', ms=1.2,
            alpha=0.25, label='PSP raw (exp.)')
    xs, cps = _smooth_cp(psp_exp)
    if xs is not None:
        ax.plot(xs / H_IN, cps, 'k-', lw=1.6, label='PSP binned mean (exp.)')
if psp_base is not None:
    valid = (psp_base['Cp'].abs() < 5)
    ax.plot(psp_base.loc[valid, 'x_in'] / H_IN, psp_base.loc[valid, 'Cp'],
            color='grey', ls='--', lw=1.8, label='Baseline k-ω SST')
if MODEL_DIR:
    m_raw = _safe_csv(os.path.join(MODEL_DIR, 'PSP_centerline_p150.csv'))
    m, ref_m = _ref_upstream(m_raw)
    if m is not None:
        ax.plot(m['x_in'] / H_IN, m['Cp'], color='green', lw=1.8, label='SL-Model')

ax.set_xlabel('x/h', fontsize=14)
ax.set_ylabel(r'$C_p$ (referenced to upstream)', fontsize=14)
ax.set_title(f'Faith Hill centerline wall pressure  '
             f'(upstream refs subtracted: exp={ref_e:.2f}, base={ref_b:.2f})', fontsize=12)
ax.invert_yaxis(); ax.grid(alpha=0.3); ax.legend(fontsize=11)
plt.tight_layout()
plt.savefig(os.path.join(HERE, 'FaithHill_PSP_Cp.pdf'), dpi=200)
plt.savefig(os.path.join(HERE, 'FaithHill_PSP_Cp.png'), dpi=200)
plt.close()


# =================================================================
# (6) FISF surface Cf, top-down. Add baseline panel if available.
# =================================================================
def panel_fisf(ax, df, levels, norm, cmap, x_col='X', y_col='Y', cf_col='Cf'):
    if df is None or cf_col not in df.columns:
        ax.text(0.5, 0.5, 'no baseline\n(re-run foamToVTK with wallShearStress)',
                ha='center', va='center', transform=ax.transAxes, fontsize=11)
        return None
    pts = np.column_stack([df[x_col] / H_IN, df[y_col] / H_IN])
    val = df[cf_col].values
    Xh = np.linspace(-12, 12, 400)
    Yh = np.linspace(-3, 3, 200)
    Xg, Yg = np.meshgrid(Xh, Yh)
    near = griddata(pts, val, (Xg, Yg), method='nearest')
    lin = griddata(pts, val, (Xg, Yg), method='linear')
    mask = np.isnan(lin); lin[mask] = near[mask]
    cf = ax.contourf(Xg, Yg, lin, levels=levels, cmap=cmap, norm=norm, extend='neither')
    th = np.linspace(0, 2*np.pi, 100)
    ax.plot(1.5*np.cos(th), 1.5*np.sin(th), 'k-', lw=1, zorder=5)
    return cf


fisf_exp = _safe_csv(os.path.join(EXPERIMENT, 'FISF_FAITH_surface.csv'))
fisf_base = _safe_csv(os.path.join(BASELINE,  'FISF_FAITH_surface.csv'))

# Levels chosen to span both datasets: exp Cf max ~0.018, baseline max ~0.010.
# Both exp and baseline are normalised as Cf = tau_w / (0.5 rho U_inf^2); the
# baseline panel appears darker because k-omega SST underpredicts the peak
# Cf on this 3D bump — that is physics, not a normalisation mismatch.
fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True,
                         gridspec_kw=dict(bottom=0.18, top=0.94, left=0.10, right=0.98,
                                          hspace=0.30))
levels_cf = np.linspace(0, 0.02, 21)
norm_cf = matplotlib.colors.Normalize(vmin=0, vmax=0.02)
cmap_cf = plt.cm.viridis

cf = panel_fisf(axes[0], fisf_exp, levels_cf, norm_cf, cmap_cf)
cf2 = panel_fisf(axes[1], fisf_base, levels_cf, norm_cf, cmap_cf)
for j, ax in enumerate(axes):
    ax.set_xlim(-12, 12); ax.set_ylim(-3, 3)
    ax.set_aspect('equal')
    ax.set_ylabel('z/h', fontsize=14)
    ax.set_title(['Experimental', 'Baseline k-ω SST'][j], fontsize=14, weight='bold')
axes[1].set_xlabel('x/h', fontsize=14)

cbar_ax = fig.add_axes([0.22, 0.06, 0.58, 0.025])
cf_for_bar = cf or cf2
if cf_for_bar:
    cbar = fig.colorbar(cf_for_bar, cax=cbar_ax, orientation='horizontal',
                        ticks=np.linspace(0, 0.02, 6))
    cbar.set_label(r'$C_f = \tau_w / (\frac{1}{2}\rho U_\infty^2)$', fontsize=14)
    cbar.ax.tick_params(labelsize=12)
plt.savefig(os.path.join(HERE, 'FaithHill_FISF_Cf.pdf'), dpi=200, bbox_inches='tight')
plt.savefig(os.path.join(HERE, 'FaithHill_FISF_Cf.png'), dpi=200, bbox_inches='tight')
plt.close()

print(f'Wrote plots to {HERE}')
