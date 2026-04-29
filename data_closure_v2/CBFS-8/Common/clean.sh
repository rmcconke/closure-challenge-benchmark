#!/bin/bash

# Delete all numeric directories except '0', e.g. '1000', '2000', etc.
ls -d [1-9][0-9]* | xargs rm -rf

# Delete post-processing output
rm -rf postProcessing
rm -rf convergencePlots
rm -f profile.pdf

# Delete logs
rm -f log.* *~

# 
rm -rf processor*
rm -rf VTK
