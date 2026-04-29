#!/bin/bash


frozenSimpleFoam  -postProcess -latestTime -funcs '(wallShearStress bottomValues)'

topoSet

foamToVTK -ascii -constant -faceSet wallFaceSet > log.foamToVTK

python3 residualConvergence.py

python3 probeConvergence.py


