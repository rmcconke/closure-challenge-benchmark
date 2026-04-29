#!/bin/bash

# Exit when a line throws an error
set -e

decomposePar > log.decomposePar

mpirun -np 8 simpleFoam -parallel > log.run

reconstructPar > log.reconstructPar

rm -rf processor*

#Make a symbolic link to the latest time directory called baselineSolution. In this way, it is easy to automatically access files in this latest time directory, whatever the name (name is equal to the last iteration).
rm -f baselineSolution
ln -s $(cat log.run | grep 'SIMPLE solution converged in ' | awk '{print $5;}') baselineSolution

foamToVTK -latestTime


