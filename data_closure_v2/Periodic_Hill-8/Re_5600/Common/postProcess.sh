#!/bin/bash

# Exit when a line throws an error
set -e

modelPropagationFoam -postProcess -latestTime -funcs '(wallShearStress bottomValues)'-latestTime -noZero > log.postProcess

topoSet

foamToVTK -ascii -faceSet wallFaceSet -time 0 > log.foamToVTK

