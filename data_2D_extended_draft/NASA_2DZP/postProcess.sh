#!/bin/bash


simpleFoam -postProcess -latestTime -funcs '(wallShearStress writeCellCentres singleGraph_y0 singleGraph_x0.97)'


