#!/bin/bash

# Exit when a line throws an error
set -e

# Remove the time directories (except 0)
rm -rf 0.* 1* 2* 3* 4* 5* 6* 7* 8* 9*


# Delete post-processing output
rm -rf postProcessing

# Remove processor directories
rm -rf processor*

# Delete logs
rm -f log.* *~
