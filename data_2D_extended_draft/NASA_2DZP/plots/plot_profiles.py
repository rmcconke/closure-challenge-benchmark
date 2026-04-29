"""ZPG flat plate validation plots — NASA TMR / Collaborative Testing Challenge 2022.

Required metrics (turb-prs2022 challenge):
    (1) Cf vs. x
    (2) u+ vs. log10(y+) at x = 0.97  (compare with theory)

Plots overlay:
    - k-omega SST baseline (this submission)        ../baseline_komegasst/*.dat
    - Reference theory                               ../highfidelity/*.dat
    - Optional user model (set MODEL_DIR below)     same dat-file naming

Run:
    python plot_profiles.py
Output:
    PDFs in this directory (./plots/).
"""

import os
import sys
import numpy as np
import matplotlib
matplotlib.rcParams.update({'font.size': 14})
import matplotlib.pyplot as plt

# Import the parser shipped one level up
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from dat_to_csv import read_nasa_zone_file as _read

HERE = os.path.dirname(os.path.abspath(__file__))
BASELINE = os.path.join(HERE, '..', 'baseline_komegasst')
EXPERIMENT = os.path.join(HERE, '..', 'highfidelity')
MODEL_DIR = os.environ.get('MODEL_DIR')  # e.g. export MODEL_DIR=/path/to/your_model_dat_dir

BASELINE_LABEL = r'$k$-$\omega$ SST (baseline)'
EXP_LABEL = 'Coles velocity law'
MODEL_LABEL = 'Submitted model'


def _safe_read(path):
    if not os.path.isfile(path):
        return None
    return _read(path)


# (1) Cf vs x ---------------------------------------------------------------
plt.figure(figsize=(7, 4.5))
d = _safe_read(os.path.join(BASELINE, '2DZP_cf.dat'))
if d:
    for k, v in d.items():
        plt.plot(v['x'], v['Cf'], '-', lw=2, color='grey', label=BASELINE_LABEL, zorder=5)

if MODEL_DIR:
    d = _safe_read(os.path.join(MODEL_DIR, '2DZP_cf.dat'))
    if d:
        for k, v in d.items():
            plt.plot(v['x'], v['Cf'], '--', lw=2, color='deeppink', label=MODEL_LABEL, zorder=10)

d = _safe_read(os.path.join(EXPERIMENT, 'cf_as_function_of_x.dat'))
if d:
    colors = ['b', 'r', 'k']
    for i, (k, v) in enumerate(d.items()):
        plt.plot(v['x'], v['skinfr'], ':', lw=2, color=colors[i % 3], label=k.split(',')[1].strip())

plt.xlabel('x')
plt.ylabel(r'$C_f$')
plt.ylim(0.002, 0.006)
plt.xlim(0, 2)
plt.grid(); plt.legend(); plt.tight_layout(pad=0.3)
plt.savefig(os.path.join(HERE, '2DZP_cf.pdf'))

# (2) u+ vs log10(y+) at x=0.97 --------------------------------------------
plt.figure(figsize=(7, 4.5))
d = _safe_read(os.path.join(BASELINE, '2DZP_u+y+.dat'))
if d:
    for k, v in d.items():
        plt.plot(v['log(y+)'], v['u+'], '-', lw=2, color='grey', label=BASELINE_LABEL, zorder=5)

if MODEL_DIR:
    d = _safe_read(os.path.join(MODEL_DIR, '2DZP_u+y+.dat'))
    if d:
        for k, v in d.items():
            plt.plot(v['log(y+)'], v['u+'], '--', lw=2, color='deeppink', label=MODEL_LABEL, zorder=10)

d = _safe_read(os.path.join(EXPERIMENT, 'u+y+.dat'))
if d:
    for k, v in d.items():
        plt.plot(np.log10(v['y+']), v['u+'], ':', lw=2, color='k', label=EXP_LABEL)

plt.xlabel(r'$\log_{10}(y^+)$')
plt.ylabel(r'$u^+$')
plt.ylim(0, 30)
plt.xlim(-1, 4)
plt.grid(); plt.legend(); plt.tight_layout(pad=0.3)
plt.savefig(os.path.join(HERE, '2DZP_u+y+.pdf'))

print(f'Wrote plots to {HERE}')
