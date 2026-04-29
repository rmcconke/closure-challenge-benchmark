#!/bin/bash

cp -r orig.0 0


mapFields ../rhoSimpleFoam_Final/Reference.Case4/ -sourceTime 'latestTime' -consistent >log.mapFields

rm 0/omega
cp orig.0/omega 0/

# Run the simulation using the simpleFoam
simpleFoam > log.run

simpleFoam -postProcess


