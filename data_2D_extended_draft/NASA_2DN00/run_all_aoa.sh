#!/bin/bash
# Run all 4 NACA 0012 AoA cases concurrently with 6 MPI ranks each.
# Usage:  source /opt/openfoam7/etc/bashrc && ./run_all_aoa.sh
# Logs:   ./run_all_aoa.<aoa>.log per case
# Each case writes its own log.run / log.decomposePar / log.rhoSimpleFoam / log.reconstructPar inside its own dir.

HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"

# Strip conda from PATH so plain `mpirun` resolves to system OpenMPI (which OF7 is linked against).
PATH="$(echo "$PATH" | tr ':' '\n' | grep -v anaconda | grep -v miniconda | tr '\n' ':' | sed 's/:$//')"
export PATH

# OpenFOAM 7 bashrc references unbound vars (ZSH_NAME) — source without set -u
source /opt/openfoam7/etc/bashrc

PIDS=()
for d in 10deg 15deg 17deg 18deg; do
    (
        cd "$d"
        echo "[$d] starting at $(date)" > "../run_all_aoa.${d}.log"
        decomposePar > log.decomposePar 2>&1
        mpirun -np 6 rhoSimpleFoam -parallel > log.rhoSimpleFoam 2>&1
        reconstructPar > log.reconstructPar 2>&1
        rm -rf processor*
        echo "[$d] solver done at $(date)" >> "../run_all_aoa.${d}.log"
        echo "[$d] finished at $(date) (rc=$?)" >> "../run_all_aoa.${d}.log"
    ) &
    PIDS+=($!)
done

echo "Started PIDs: ${PIDS[@]}"
wait "${PIDS[@]}"
echo "All 4 AoA cases done at $(date)."
