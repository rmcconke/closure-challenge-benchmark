#!/bin/bash

# Exit when a line throws an error
set -e

#==================================================================================================
#Post-process the baseline

echo "Post-processing the baseline"

#Go to the baseline run directory
cd 00Baseline/beta11/ 

#Post-process the case
./postProcess.sh

#Go back to the case directory
cd ../../


#==================================================================================================
#Post-process the frozen

echo "Post-processing the frozen"

#Go to the frozen run directory
cd 01Frozen/beta11/

#Post-process the case
./postProcess.sh

#Go back to the case directory
cd ../../

#==================================================================================================
#Post-process the propagation

echo "Post-processing the propagation"

#Go to the propagation run directory
cd 02Propagation/beta11/ 

#Post-process the case
./postProcess.sh

#Go back to the case directory
cd ../../


