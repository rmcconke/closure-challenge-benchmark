#!/bin/bash

# Exit when a line throws an error
set -e

decomposePar > log.decomposePar

mpirun -np 4 frozenSimpleFoam -parallel > log.run

reconstructPar > log.reconstructPar

rm -r processor*

./postProcess.sh


