#!/bin/bash

frozenSimpleFoam > log.run

#Make a symbolic link to the latest time directory called frozenSolution. In this way, it is easy to automatically access files in this latest time directory, whatever the name (name is equal to the last iteration).
rm -f frozenSolution
ln -s $(cat log.run | grep 'SIMPLE solution converged in ' | awk '{print $5;}') frozenSolution

# ./postProcess.sh
postProcess -func writeCellVolumes

# source ~/anaconda3/etc/profile.d/conda.sh
# conda activate gepfoam
# python ./write_bases_features.py

