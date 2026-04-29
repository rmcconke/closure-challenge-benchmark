"""Axisymmetric Subsonic Jet (ASJ) validation plots — NASA TMR turb-prs2022.

Required metrics (turb-prs2022 challenge):
    (1) u/Ujet vs. x/Djet                              (centerline)
    (2) u/Ujet vs. y/Djet at 5 specified stations
    (3) u'v'/Ujet^2 vs. y/Djet at 5 specified stations

Compare with experiment: Bridges & Wernet ARN consensus PIV dataset (Mjet ~ 0.5).

Run:
    python plot_profiles.py
Output:
    PDFs in this directory (./plots/).
"""

import os, sys
import matplotlib
matplotlib.rcParams.update({'font.size': 14})
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from dat_to_csv import read_nasa_zone_file as _read

HERE = os.path.dirname(os.path.abspath(__file__))
BASELINE = os.path.join(HERE, '..', 'baseline_komegasst')
EXPERIMENT = os.path.join(HERE, '..', 'highfidelity')
MODEL_DIR = os.environ.get('MODEL_DIR')

BASELINE_LABEL = r'$k$-$\omega$ SST (baseline)'
MODEL_LABEL = 'Submitted model'

STATION_COLORS = ['r', 'k', 'b', 'g', 'purple']
STATION_MARKERS = ['s', '^', 'v', '>', '<']


def _safe_read(path):
    if not os.path.isfile(path):
        return None
    return _read(path)


# (1) u/Uj vs x/Dj along centerline ----------------------------------------
plt.figure(figsize=(7, 4.5))
d = _safe_read(os.path.join(BASELINE, 'ASJ_u_vs_x.dat'))
if d:
    for k, v in d.items():
        plt.plot(v['x/Dj'], v['u/Uj'], '-', lw=2, color='grey', label=BASELINE_LABEL, zorder=5)

if MODEL_DIR:
    d = _safe_read(os.path.join(MODEL_DIR, 'ASJ_u_vs_x.dat'))
    if d:
        for k, v in d.items():
            plt.plot(v['x/Dj'], v['u/Uj'], '--', lw=2, color='deeppink', label=MODEL_LABEL, zorder=10)

d = _safe_read(os.path.join(EXPERIMENT, 'ARN-jet-lines-expt.dat'))
if d and 'y/Dj=0' in d:
    v = d['y/Dj=0']
    plt.plot(v['x/Dj'], v['u/Uj'], 'k:', lw=2, label='ARN PIV (exp)')

plt.xlabel(r'$x/D_{jet}$')
plt.ylabel(r'$u/U_{jet}$')
plt.ylim(0, 1.1); plt.xlim(0, 22)
plt.grid(); plt.legend(); plt.tight_layout(pad=0.3)
plt.savefig(os.path.join(HERE, 'ASJ_u_vs_x.pdf'))

# (2) u/Uj profiles at 5 stations -------------------------------------------
plt.figure(figsize=(7, 5.5))
d = _safe_read(os.path.join(BASELINE, 'ASJ_u_at5stations.dat'))
if d:
    for i, (k, v) in enumerate(d.items()):
        label = BASELINE_LABEL if i == 0 else None
        plt.plot(v['u/Uj'], v['y/Dj'], '-', lw=2, color=STATION_COLORS[i % 5],
                 label=label, zorder=5)

if MODEL_DIR:
    d = _safe_read(os.path.join(MODEL_DIR, 'ASJ_u_at5stations.dat'))
    if d:
        for i, (k, v) in enumerate(d.items()):
            label = MODEL_LABEL if i == 0 else None
            plt.plot(v['u/Uj'], v['y/Dj'], '--', lw=2, color=STATION_COLORS[i % 5],
                     label=label, zorder=10)

d = _safe_read(os.path.join(EXPERIMENT, 'ARN-jet-lines-expt.dat'))
if d:
    keys = [k for k in d.keys() if 'y/Dj' not in k]  # x/Dj=N stations
    for i, k in enumerate(keys[:5]):
        v = d[k]
        plt.scatter(v['u/Uj'], v['y/Dj'], ec=STATION_COLORS[i], fc='none',
                    marker=STATION_MARKERS[i], label=k)

plt.xlabel(r'$u/U_{jet}$')
plt.ylabel(r'$y/D_{jet}$')
plt.ylim(0, 1.5); plt.xlim(0, 1.2)
plt.grid(); plt.legend(loc='upper right', fontsize=10)
plt.tight_layout(pad=0.3)
plt.savefig(os.path.join(HERE, 'ASJ_u_at5stations.pdf'))

# (3) u'v'/Uj^2 profiles at 5 stations --------------------------------------
plt.figure(figsize=(7, 5.5))
d = _safe_read(os.path.join(BASELINE, 'ASJ_uv_at5stations.dat'))
if d:
    for i, (k, v) in enumerate(d.items()):
        label = BASELINE_LABEL if i == 0 else None
        plt.plot(v["u'v'/Uj^2"], v['y/Dj'], '-', lw=2, color=STATION_COLORS[i % 5],
                 label=label, zorder=5)

if MODEL_DIR:
    d = _safe_read(os.path.join(MODEL_DIR, 'ASJ_uv_at5stations.dat'))
    if d:
        for i, (k, v) in enumerate(d.items()):
            label = MODEL_LABEL if i == 0 else None
            plt.plot(v["u'v'/Uj^2"], v['y/Dj'], '--', lw=2, color=STATION_COLORS[i % 5],
                     label=label, zorder=10)

d = _safe_read(os.path.join(EXPERIMENT, 'ARN-jet-lines-expt.dat'))
if d:
    keys = [k for k in d.keys() if 'y/Dj' not in k]
    for i, k in enumerate(keys[:5]):
        v = d[k]
        plt.scatter(v["u'v'/Uj^2"], v['y/Dj'], ec=STATION_COLORS[i], fc='none',
                    marker=STATION_MARKERS[i], label=k)

plt.xlabel(r"$u'v'/U_{jet}^2$")
plt.ylabel(r'$y/D_{jet}$')
plt.ylim(0, 1.5); plt.xlim(0, 0.02)
plt.grid(); plt.legend(loc='upper right', fontsize=10)
plt.gca().xaxis.set_ticks([0, 0.005, 0.01, 0.015, 0.02])
plt.tight_layout(pad=0.3)
plt.savefig(os.path.join(HERE, 'ASJ_uv_at5stations.pdf'))

print(f'Wrote plots to {HERE}')
