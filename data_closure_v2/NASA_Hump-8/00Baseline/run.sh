#!/bin/bash

# Exit when a line throws an error
set -e

modelPropagationFoam > log.run
ln -sfn "$(ls -d [0-9]* | sort -n | tail -1)" baselineSolution

./postProcess.sh
