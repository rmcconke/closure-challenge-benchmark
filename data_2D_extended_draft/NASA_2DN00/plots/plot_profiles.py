"""NACA 0012 validation plots — NASA TMR turb-prs2022.

AoA = 10, 15, 17, 18 deg.

Required metrics (turb-prs2022 challenge):
    (1) CL vs alpha
    (2) CD vs CL
    (3) Cp vs x/c at each AoA          (compare with experiment)
    (4) Cf vs x/c (upper surface) at each AoA   (no experiment available)

Compare with experiment:
    - Ladson NASA TM 4074, 1988 (CL, CD)  — Re=6e6, M=0.15, transition tripped
    - Gregory & O'Reilly NASA R&M 3726, 1970 (Cp) — Re=2.88e6
    - CFL3D SST reference (Cp) — 897x257 grid, NASA TMR

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

ALPHAS = [10, 15, 17, 18]


def _safe_read(path):
    if not os.path.isfile(path):
        return None
    return _read(path)


# (1) CL vs alpha ----------------------------------------------------------
plt.figure(figsize=(6, 4.5))
d = _safe_read(os.path.join(BASELINE, '2DN00_cl_cd.dat'))
if d:
    for k, v in d.items():
        plt.scatter(v['alpha, deg'], v['cl'], marker='v', c='grey',
                    s=70, label=BASELINE_LABEL, zorder=5)

if MODEL_DIR:
    d = _safe_read(os.path.join(MODEL_DIR, '2DN00_cl_cd.dat'))
    if d:
        for k, v in d.items():
            plt.scatter(v['alpha, deg'], v['cl'], marker='D', c='deeppink',
                        s=70, label=MODEL_LABEL, zorder=10)

d = _safe_read(os.path.join(EXPERIMENT, 'CLCD_Ladson_expdata.dat'))
if d and '180 grit' in d:
    v = d['180 grit']
    plt.scatter(v['alpha, deg'], v['cl'], ec='b', fc='none', marker='s',
                s=60, label='Ladson 1988 (180 grit)')

plt.xlabel(r'$\alpha$ [deg]')
plt.ylabel(r'$C_L$')
plt.xlim(0, 22); plt.ylim(-0.2, 1.8)
plt.grid(); plt.legend(); plt.tight_layout(pad=0.3)
plt.savefig(os.path.join(HERE, '2DN00_cl_alpha.pdf'))

# (2) CD vs CL -------------------------------------------------------------
plt.figure(figsize=(6, 4.5))
d = _safe_read(os.path.join(BASELINE, '2DN00_cl_cd.dat'))
if d:
    for k, v in d.items():
        plt.scatter(v['cl'], v['cd'], marker='v', c='grey',
                    s=70, label=BASELINE_LABEL, zorder=5)

if MODEL_DIR:
    d = _safe_read(os.path.join(MODEL_DIR, '2DN00_cl_cd.dat'))
    if d:
        for k, v in d.items():
            plt.scatter(v['cl'], v['cd'], marker='D', c='deeppink',
                        s=70, label=MODEL_LABEL, zorder=10)

d = _safe_read(os.path.join(EXPERIMENT, 'CLCD_Ladson_expdata.dat'))
if d and '180 grit' in d:
    v = d['180 grit']
    plt.scatter(v['cl'], v['cd'], ec='b', fc='none', marker='s',
                s=60, label='Ladson 1988 (180 grit)')

plt.xlabel(r'$C_L$'); plt.ylabel(r'$C_D$')
plt.xlim(0, 2); plt.ylim(0, 0.08)
plt.grid(); plt.legend(); plt.tight_layout(pad=0.3)
plt.savefig(os.path.join(HERE, '2DN00_cl_cd.pdf'))

# (3) Cp vs x/c at each AoA ------------------------------------------------
d_base = _safe_read(os.path.join(BASELINE, '2DN00_cp_at4alphas.dat'))
d_model = _safe_read(os.path.join(MODEL_DIR, '2DN00_cp_at4alphas.dat')) if MODEL_DIR else None
d_exp = _safe_read(os.path.join(EXPERIMENT, 'CP_Gregory_expdata.dat'))
d_cfl3d = _safe_read(os.path.join(EXPERIMENT, 'n0012cp_cfl3d_sst.dat'))

base_keys = list(d_base.keys()) if d_base else []
model_keys = list(d_model.keys()) if d_model else []
exp_keys = list(d_exp.keys()) if d_exp else []
cfl3d_keys = list(d_cfl3d.keys()) if d_cfl3d else []

ylim_cp = {10: (2, -6), 15: (2, -12), 17: (2, -12), 18: (2, -12)}

for i, alpha in enumerate(ALPHAS):
    plt.figure(figsize=(6, 4.5))
    if i < len(base_keys):
        v = d_base[base_keys[i]]
        plt.plot(v['x/c'], v['cp'], '-', lw=2, color='grey',
                 label=BASELINE_LABEL, zorder=5)
    if d_model and i < len(model_keys):
        v = d_model[model_keys[i]]
        plt.plot(v['x/c'], v['cp'], '--', lw=2, color='deeppink',
                 label=MODEL_LABEL, zorder=10)
    if d_cfl3d:
        match = [k for k in cfl3d_keys if f'alpha={alpha}' in k.replace(' ', '')]
        if match:
            v = d_cfl3d[match[0]]
            plt.plot(v['x'], v['cp'], ':', lw=1.5, color='green',
                     label='CFL3D SST (NASA)')
    if d_exp:
        match = [k for k in exp_keys if f'alpha={alpha}' in k.replace(' ', '')]
        if match:
            v = d_exp[match[0]]
            plt.scatter(v['x/c'], v['cp'], ec='b', fc='none', marker='s',
                        s=40, label='Gregory 1970 (exp)')

    plt.title(f'NACA 0012, alpha = {alpha} deg')
    plt.xlabel('x/c'); plt.ylabel(r'$C_p$')
    plt.ylim(ylim_cp[alpha]); plt.xlim(0, 1)
    plt.grid(); plt.legend(); plt.tight_layout(pad=0.3)
    plt.savefig(os.path.join(HERE, f'2DN00_cp_alpha_{alpha}deg.pdf'))

# (4) Cf vs x/c (upper) at each AoA ----------------------------------------
d_base = _safe_read(os.path.join(BASELINE, '2DN00_cf_at4alphas.dat'))
d_model = _safe_read(os.path.join(MODEL_DIR, '2DN00_cf_at4alphas.dat')) if MODEL_DIR else None
base_keys = list(d_base.keys()) if d_base else []
model_keys = list(d_model.keys()) if d_model else []

ylim_cf = {10: (-0.005, 0.04), 15: (-0.005, 0.07), 17: (-0.005, 0.07), 18: (-0.005, 0.07)}

for i, alpha in enumerate(ALPHAS):
    plt.figure(figsize=(6, 4.5))
    if i < len(base_keys):
        v = d_base[base_keys[i]]
        plt.plot(v['x/c'], v['cf'], '-', lw=2, color='grey',
                 label=BASELINE_LABEL, zorder=5)
    if d_model and i < len(model_keys):
        v = d_model[model_keys[i]]
        plt.plot(v['x/c'], v['cf'], '--', lw=2, color='deeppink',
                 label=MODEL_LABEL, zorder=10)

    plt.title(f'NACA 0012, alpha = {alpha} deg')
    plt.xlabel('x/c'); plt.ylabel(r'$C_f$ (upper)')
    plt.ylim(ylim_cf[alpha]); plt.xlim(0, 1)
    plt.grid(); plt.legend(); plt.tight_layout(pad=0.3)
    plt.savefig(os.path.join(HERE, f'2DN00_cf_alpha_{alpha}deg.pdf'))

print(f'Wrote plots to {HERE}')
