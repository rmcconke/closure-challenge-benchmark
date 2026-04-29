#!/bin/bash


modelPropagationFoam  -postProcess -latestTime -funcs '(wallShearStress bottomValues)'

topoSet

foamToVTK -ascii -faceSet wallFaceSet -time 0 > log.foamToVTK

python3 residualConvergence.py

python3 probeConvergence.py

