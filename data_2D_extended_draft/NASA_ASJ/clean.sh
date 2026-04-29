#!/bin/bash

# Remove the time directories (except 0)
rm -rf 0.* 1* 2* 3* 4* 5* 6* 7* 8* 9*

# Remove pdf plots from postprocessing codes
rm -f *.pdf

# Delete post-processing output
rm -rf postProcessing

# Delete logs
rm -f log.* *~






