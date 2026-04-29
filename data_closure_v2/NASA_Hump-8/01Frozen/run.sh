#!/bin/bash

# Exit when a line throws an error
set -e

frozenSimpleFoam > log.run

./postProcess.sh


