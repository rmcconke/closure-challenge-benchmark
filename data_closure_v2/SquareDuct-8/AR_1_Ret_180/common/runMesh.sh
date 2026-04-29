#!/bin/bash

# Exit when a line throws an error
set -e

./clean.sh

blockMesh > log.blockMesh

postProcess -funcs '(writeCellCentres writeCellVolumes)' > log.writeCellCentres




