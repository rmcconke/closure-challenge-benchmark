#!/bin/bash
# Tested: R. Dwight - Jan 2020 - OF7.0

### Mesh generation and solver

frozenSimpleFoam > log.frozenSimpleFoam

# Cell-centers writen to 2000/C etc. for Python visualization

postProcess -func writeCellCentres
postProcess -func writeCellVolumes

ln -sfn "$(ls -d [0-9]* | sort -n | tail -1)" frozenSolution
