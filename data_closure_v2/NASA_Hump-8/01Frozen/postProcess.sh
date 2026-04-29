#!/bin/bash

# Exit when a line throws an error
set -e

topoSet 

foamToVTK -ascii -constant -faceSet wallFaceSet > log.foamToVTK

python3 residualConvergence.py

python3 probeConvergence.py
