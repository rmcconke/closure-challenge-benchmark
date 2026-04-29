#!/bin/bash
#PBS -l walltime=0:10:00
#PBS -l nodes=1:ppn=8:typef
#PBS -N OF7-test
#PBS -q fpt-test

# Dump starting environment data (will not be same as on master)
uname -n      # Name of node
export        # All envvars
pwd           # Working directory on start (should be ~)
which python  # Which Python is implied

# Init environment
cd $PBS_O_WORKDIR
module load mpi/openmpi-4.1.2
module load openfoam/7

### 1. Mesh generation and solver
blockMesh > log.blockMesh
checkMesh > log.checkMesh

decomposePar > log.decomposePar
mpirun -np 8 simpleFoam -parallel > log.simpleFoam 
reconstructPar > log.reconstructPar

# Note: `./monitor.sj` at this point, plots regularly updated convergence.

### 2. Postprocessing: Output wall-shear stresses to 'postProcessing' dir
simpleFoam -postProcess -func wallShearStress > log.wallShearStress

### 3. Postprocessing: Sample solution according to system/sampleDict, output
###    in 'postProcessing' dir
postProcess -func sampleDict > log.sampleDict
