#!/bin/bash

# Exit when a line throws an error
set -e

# Remove the time directories (except 0)
rm -rf 0.* 1* 2* 3* 4* 5* 6* 7* 8* 9*

# Remove pdf plots from postprocessing codes
rm -f *.pdf

# Delete post-processing output
rm -rf postProcessing

# Remove processor directories
rm -rf processor*

# Delete logs
rm -f log.* *~

rm -rf VTK

rm -rf dynamicCode convergencePlots

rm -rf baselineSolution frozenSolution propagationSolution

#Delete wall-roughness file for the hetRoughness case
rm -f Ks_tot
