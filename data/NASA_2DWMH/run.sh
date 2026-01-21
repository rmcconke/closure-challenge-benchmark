#!/bin/bash

# Exit when a line throws an error
set -e

modelPropagationFoam > log.run

./postProcess.sh
