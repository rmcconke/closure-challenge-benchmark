#!/bin/bash

# Run the simulation using the rhoPimpleFoam solving (compressible, transient)
rhoPimpleFoam > log.run

# Run the probeConvergence script, showing the convergence through time at various probed locations
python3 probeConvergence.py

# Run the linePlotterMean script, saving mean data over certain lines in the postProcessing/linePlotData/ folder
pvpython linePlotterMean.py

# Run the comparisonPlotterMean script, showing the line data together with reference RANS data from NASA
python3 comparisonPlotterMean.py


