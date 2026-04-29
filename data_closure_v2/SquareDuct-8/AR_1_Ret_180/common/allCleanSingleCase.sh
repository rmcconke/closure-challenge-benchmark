#!/bin/bash

# Exit when a line throws an error
set -e

#==================================================================================================
#Cleaning the mesh

echo "Cleaning the mesh"

#Go to the mesh directory
cd meshes/beta11/

#Clean the mesh
./clean.sh

#Go back to the case directory
cd ../../


#==================================================================================================
#Cleaning the baseline

echo "Cleaning the baseline"

#Go to the baseline run directory
cd 00Baseline/beta11/ 

#Clean the case before running to ensure it starts at zero
./clean.sh

cd ../

#Remove any comparison figures from the Figures directory
rm -f Figures/comparison*

#Go back to the case directory
cd ../


#==================================================================================================
#Cleaning the frozen

echo "Cleaning the frozen"

#Go to the field interpolation directory and run the interpolation script
cd 01Frozen/interpolateDNS

#Remove any interpolated frozen fields
rm -f interpolatedFields/*

#Go to the frozen run directory
cd ../beta11/ 

#Clean the case
./clean.sh

cd ../

#Remove any comparison figures from the Figures directory
rm -f Figures/comparison*

#Go back to the case directory
cd ../

#==================================================================================================
#Cleaning the propagation

echo "Cleaning the propagation"

#Go to the propagation run directory
cd 02Propagation/beta11/ 

#Clean the case before running to ensure it starts at zero
./clean.sh

cd ../

#Remove any comparison figures from the Figures directory
rm -f Figures/comparison*

#Go back to the case directory
cd ../


