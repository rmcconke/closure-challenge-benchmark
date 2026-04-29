#!/bin/bash

# Exit when a line throws an error
set -e

#==================================================================================================
#Creating the mesh

echo "Creating the mesh"

#Go to the mesh directory
cd meshes/beta11/

#Clean the mesh before running to ensure a new mesh is created
./clean.sh

#Run the mesh to create a new polyMesh
./run.sh

#Go back to the case directory
cd ../../

#==================================================================================================
#Running and plotting the baseline

echo "Running the baseline"

#Go to the baseline run directory
cd 00Baseline/beta11/ 

#Clean the case before running to ensure it starts at zero
./clean.sh

#Run the case (this includes post-processing)
./run.sh


#Go back to the case directory
cd ../../


#==================================================================================================
#Interpolating and running frozen

echo "Interpolating and running the frozen"

#Go to the field interpolation directory
cd 01Frozen/interpolateDNS

#Delete existing interpolated fields
rm -f interpolatedFields/*

#Run the interpolation script to generate new interpolated fields
python3 interpolateDNS.py

#Go to the frozen run directory
cd ../beta11/ 

#Clean the case before running to ensure it starts at zero
./clean.sh

#Run the case (this includes post-processing)
./run.sh

#Go back to the case directory
cd ../../


#==================================================================================================
#Interpolating and running frozen

echo "Plotting and writing profiles"

python3 plot_U_dig_baseline_dns.py
python3 write_profiles.py
