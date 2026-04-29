#!/bin/bash
# Tested: R. Dwight - Jan 2020 - OF7.0

### 1. Mesh generation and solver
blockMesh > log.blockMesh
checkMesh > log.checkMesh

# Note: `./monitor.sj` at this point, plots regularly updated convergence.

postProcess -funcs '(writeCellCentres writeCellVolumes)' > log.writeCellCentres


### 3. Postprocessing: Sample solution according to system/sampleDict, output
###    in 'postProcessing' dir


