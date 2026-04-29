"""Wing-body junction validation plots — academic publication style.

Source: ERCOFTAC kbwiki DNS 1-6 (Bassi, Colombo, Massa, Leschziner, Chapelier 2023).
    Re_T = 115 000, T = 71.7 mm, M = 0.078, U_ref = 27 m/s.
    Wing: 3:2 semi-elliptic nose + NACA0020 tail. Origin at root LE.
    DNS data is non-dimensional (U/u_ref, Rij/u_ref^2, k/u_ref^2).

Plots:
    1) U/u_ref profiles at the 10 streamwise stations (2x5 grid, Exp + Baseline overlaid)
    2) k/u_ref^2 profiles at the same 10 stations
    3) R_xx/u_ref^2 profile comparison (Reynolds normal stress)
    4) Bottom-wall centerline Cp(x/T) — line plot, Exp + Baseline
    5) Wing root chord Cp(x/T) — line plot, Exp + Baseline

Run:    python plot_profiles.py
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.rcParams.update({'font.size': 13})
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
BASELINE = os.path.join(HERE, '..', 'baseline_komegasst')
EXPERIMENT = os.path.join(HERE, '..', 'highfidelity')
MODEL_DIR = os.environ.get('MODEL_DIR')

STATIONS = ['-0.45', '-0.40', '-0.35', '-0.30', '-0.25',
            '-0.20', '-0.15', '-0.10', '-0.05', '-0.01']

EXP_KW   = dict(color='k',     marker='o', mfc='none', ms=4, ls='', label='DNS 1-6')
BASE_KW  = dict(color='grey',  ls='-',  lw=1.8, label=r'Baseline k-ω SST')
MODEL_KW = dict(color='deeppink', ls='--', lw=1.8, label='Submitted model')


def _safe_csv(path):
    return pd.read_csv(path) if os.path.isfile(path) else None


def grid_2x5(metric_exp, metric_base, ylim, xlabel, fname, title):
    fig, axes = plt.subplots(2, 5, figsize=(18, 7), sharey=True)
    axes = axes.flatten()
    handles, labels = None, None
    for i, st in enumerate(STATIONS):
        exp = _safe_csv(os.path.join(EXPERIMENT, f'profile_midplane_{st}.csv'))
        base = _safe_csv(os.path.join(BASELINE,  f'profile_midplane_{st}.csv'))
        ax = axes[i]
        if exp is not None and metric_exp in exp.columns:
            ax.plot(exp[metric_exp], exp['y'], **EXP_KW)
        if base is not None and metric_base in base.columns:
            ax.plot(base[metric_base], base['y'], **BASE_KW)
        if MODEL_DIR:
            m = _safe_csv(os.path.join(MODEL_DIR, f'profile_midplane_{st}.csv'))
            if m is not None and metric_base in m.columns:
                ax.plot(m[metric_base], m['y'], **MODEL_KW)
        ax.set_title(f'x/T = {st}', fontsize=12)
        ax.set_xlim(*ylim)
        ax.set_ylim(0, 0.2)
        ax.grid(alpha=0.3)
        if i % 5 == 0:
            ax.set_ylabel('y/T', fontsize=14)
        if i >= 5:
            ax.set_xlabel(xlabel, fontsize=14)
        if i == 0:
            handles, labels = ax.get_legend_handles_labels()

    if handles:
        fig.legend(handles, labels, loc='upper center', ncol=len(handles),
                   fontsize=12, bbox_to_anchor=(0.5, 1.0), frameon=False)
    fig.suptitle(title, fontsize=14, weight='bold', y=0.94)
    plt.tight_layout(rect=[0, 0, 1, 0.92])
    plt.savefig(os.path.join(HERE, fname), dpi=200)
    plt.savefig(os.path.join(HERE, fname.replace('.pdf', '.png')), dpi=200)
    plt.close()


# (1) U / u_ref profiles
grid_2x5('u', 'u', ylim=(-0.7, 1.0), xlabel=r'$U / u_\mathrm{ref}$',
         fname='WingBody_profile_U.pdf',
         title='Symmetry-plane streamwise velocity (horseshoe-vortex region)')

# (2) k / u_ref^2 profiles
grid_2x5('k', 'k', ylim=(0, 0.10), xlabel=r'$k / u_\mathrm{ref}^2$',
         fname='WingBody_profile_k.pdf',
         title='Symmetry-plane TKE')

# (3) R_xx / u_ref^2 profiles  — exp uses 'Re_xx', baseline uses 'R_xx'
fig, axes = plt.subplots(2, 5, figsize=(18, 7), sharey=True)
axes = axes.flatten()
handles, labels = None, None
for i, st in enumerate(STATIONS):
    exp = _safe_csv(os.path.join(EXPERIMENT, f'profile_midplane_{st}.csv'))
    base = _safe_csv(os.path.join(BASELINE,  f'profile_midplane_{st}.csv'))
    ax = axes[i]
    if exp is not None and 'Re_xx' in exp.columns:
        ax.plot(exp['Re_xx'], exp['y'], **EXP_KW)
    if base is not None and 'R_xx' in base.columns:
        ax.plot(base['R_xx'], base['y'], **BASE_KW)
    ax.set_title(f'x/T = {st}', fontsize=12)
    ax.set_xlim(0, 0.15); ax.set_ylim(0, 0.2)
    ax.grid(alpha=0.3)
    if i % 5 == 0: ax.set_ylabel('y/T', fontsize=14)
    if i >= 5: ax.set_xlabel(r'$R_{xx} / u_\mathrm{ref}^2$', fontsize=14)
    if i == 0: handles, labels = ax.get_legend_handles_labels()
if handles:
    fig.legend(handles, labels, loc='upper center', ncol=len(handles),
               fontsize=12, bbox_to_anchor=(0.5, 1.0), frameon=False)
fig.suptitle('Symmetry-plane Reynolds normal stress R_xx', fontsize=14, weight='bold', y=0.94)
plt.tight_layout(rect=[0, 0, 1, 0.92])
plt.savefig(os.path.join(HERE, 'WingBody_profile_Rxx.pdf'), dpi=200)
plt.savefig(os.path.join(HERE, 'WingBody_profile_Rxx.png'), dpi=200)
plt.close()


# (4) Bottom-wall centerline Cp(x/T)
fig, ax = plt.subplots(figsize=(11, 4.5))
exp = _safe_csv(os.path.join(EXPERIMENT, 'bottom_wall_centerline.csv'))
base = _safe_csv(os.path.join(BASELINE,  'bottom_wall_centerline.csv'))
if exp is not None:
    e = exp.sort_values('x_over_T')
    ax.plot(e['x_over_T'], e['Cp'], 'o', mfc='none', ms=2, color='k', alpha=0.4,
            label='DNS 1-6')
if base is not None and 'Cp' in base.columns:
    b = base.sort_values('x_over_T')
    ax.plot(b['x_over_T'], b['Cp'], **BASE_KW)
if MODEL_DIR:
    m = _safe_csv(os.path.join(MODEL_DIR, 'bottom_wall_centerline.csv'))
    if m is not None and 'Cp' in m.columns:
        ax.plot(m['x_over_T'], m['Cp'], **MODEL_KW)
ax.set_xlim(-3, 8); ax.set_ylim(-0.4, 1.1)
ax.set_xlabel('x/T', fontsize=14); ax.set_ylabel(r'$C_p$', fontsize=14)
ax.set_title('Bottom-wall centerline pressure (z/T = 0)', fontsize=14)
ax.grid(alpha=0.3); ax.legend(fontsize=11)
plt.tight_layout()
plt.savefig(os.path.join(HERE, 'WingBody_bottom_wall_Cp.pdf'), dpi=200)
plt.savefig(os.path.join(HERE, 'WingBody_bottom_wall_Cp.png'), dpi=200)
plt.close()


# (5) Wing root chord Cp(x/T)
# Use airfoil surface cells in a thin band near the root (y/T -> 0). For each
# unique x position there are two surface cells (upper z>0, lower z<0); the
# airfoil is symmetric so the two should fall on top of each other. Sort by
# x_over_T inside each side so the line is monotonic.
fig, ax = plt.subplots(figsize=(9, 4.5))
exp = _safe_csv(os.path.join(EXPERIMENT, 'wing_root_chord_surface.csv'))
base = _safe_csv(os.path.join(BASELINE,  'wing_root_chord_surface.csv'))


def _binned_mean(df, nbins=120):
    """Bin Cp(x_over_T) into nbins along chord and return mean per bin so
    the symmetric upper/lower sides collapse onto a single smooth curve."""
    bins = np.linspace(df['x_over_T'].min(), df['x_over_T'].max(), nbins + 1)
    df = df.copy()
    df['_bin'] = pd.cut(df['x_over_T'], bins, include_lowest=True)
    grp = df.groupby('_bin', observed=True).agg(x=('x_over_T', 'mean'),
                                                Cp=('Cp', 'mean')).dropna()
    return grp.sort_values('x')


if exp is not None:
    # DNS proxy: lowest-y volume probe per (x, z). Plot as faint scatter.
    ax.plot(exp['x_over_T'], exp['Cp'], 'o', mfc='none', ms=2, color='k', alpha=0.35,
            label='DNS 1-6 (vol probe at root)')
if base is not None and 'Cp' in base.columns:
    g = _binned_mean(base)
    ax.plot(g['x'], g['Cp'], **BASE_KW)
if MODEL_DIR:
    m = _safe_csv(os.path.join(MODEL_DIR, 'wing_root_chord_surface.csv'))
    if m is not None and 'Cp' in m.columns:
        gm = _binned_mean(m)
        ax.plot(gm['x'], gm['Cp'], **MODEL_KW)
ax.set_xlim(0, 4.3); ax.invert_yaxis()
ax.set_xlabel('x/T', fontsize=14); ax.set_ylabel(r'$C_p$', fontsize=14)
ax.set_title('Wing root chord pressure (airfoil surface, y/T → 0)', fontsize=14)
ax.grid(alpha=0.3); ax.legend(fontsize=11)
plt.tight_layout()
plt.savefig(os.path.join(HERE, 'WingBody_wing_root_Cp.pdf'), dpi=200)
plt.savefig(os.path.join(HERE, 'WingBody_wing_root_Cp.png'), dpi=200)
plt.close()

print(f'Wrote plots to {HERE}')
