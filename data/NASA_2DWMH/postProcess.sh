#!/bin/bash

# Exit when a line throws an error
set -e

topoSet 

foamToVTK -ascii -faceSet wallFaceSet -time 0 > log.foamToVTK

modelPropagationFoam -postProcess -funcs '(wallShearStress wallValues)' -latestTime -noZero > log.postProcess

python3 residualConvergence.py

python3 probeConvergence.py
