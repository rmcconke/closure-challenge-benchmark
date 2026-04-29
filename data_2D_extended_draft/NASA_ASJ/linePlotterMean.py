'''Code to extract mean field data along certain lines and store this data as
.csv files in the postProcessing/linePlotData in the case directory. This is
achieved using ParaView's python library, this also means this code needs to be
run using pvpython:
    $ pvpython linePlotter.py

For now this code only works with composed cases (but adaptation to decomposed
shouldn't be too difficult).

Author : Kaj Hoefnagel
'''

#--------------------------------------------------------------------------------
#Libraries to be imported

from paraview.simple import *
import glob
import os


#--------------------------------------------------------------------------------
#Definitions

#Jet radius; one inch
r_jet = 0.0254

#Jet diameter
D_jet = 2*r_jet

#Dictionary to define the lines to plot over; the centerline as well as vertical
#lines at various distances behind the nozzle.
#Each line is defined as the two end points.
lines = {'centerline' : ([0, 0, 0], [22*D_jet, 0, 0]),
         'x_over_D_2' : ([2*D_jet, 0, 0], [2*D_jet, 0, 1.5*D_jet]),
         'x_over_D_5' : ([5*D_jet, 0, 0], [5*D_jet, 0, 1.5*D_jet]),
         'x_over_D_10' : ([10*D_jet, 0, 0], [10*D_jet, 0, 1.5*D_jet]),
         'x_over_D_15' : ([15*D_jet, 0, 0], [15*D_jet, 0, 1.5*D_jet]),
         'x_over_D_20' : ([20*D_jet, 0, 0], [20*D_jet, 0, 1.5*D_jet])}


#--------------------------------------------------------------------------------
#Check/prepare the file structure


#Check if the postProcessing directory is already present for the case,
#if not, make it.
if os.path.isdir('./postProcessing') == False:
    os.mkdir(case_path+'/postProcessing')

#Check if the postProcessing/linePlotData directory is already present for the
#case, if not, make it.
if os.path.isdir('./postProcessing/linePlotData') == False:
    os.mkdir('./postProcessing/linePlotData')


#Remove existing files in the postProcessing/linePlotData directory
existing_files = glob.glob('./postProcessing/linePlotData/*')
for existing_file in existing_files:
    os.remove(existing_file)

#Create the foam.foam file in the case directory (if it doesn't already exist)
f = open('./foam.foam', 'w')
f.close()


#--------------------------------------------------------------------------------
#Initializing ParaView

#Initialize the case reader
foamfoam = OpenFOAMReader(FileName='./foam.foam')

#Read in the entire mesh and all required mean fields
foamfoam.MeshRegions = ['internalMesh']
foamfoam.CellArrays = ['UMean', 'kMean', 'nutMean']

#Set the time to the latest available time instance
time = foamfoam.TimestepValues[-1]

#Introduce a forced time to force the time to the latest available one
forceTime1 = ForceTime(Input=foamfoam)
forceTime1.ForcedTime = time

#Find velocity gradient tensor field
gradientOfUnstructuredDataSet1 = GradientOfUnstructuredDataSet(Input=forceTime1)
gradientOfUnstructuredDataSet1.ScalarArray = ['CELLS', 'UMean']

#--------------------------------------------------------------------------------
#Interpolating the mean values to each line

#Loop over each line to interpolate on
for line_key in lines.keys():

    #Create a plotOverLine object from the simulation at the forced time
    #as well as the velocity gradient tensor field (also at this forced time)
    plotOverLine1 = PlotOverLine(Input=[forceTime1,
                                        gradientOfUnstructuredDataSet1],
                                        Source='High Resolution Line Source')

    #Set the two end points of this line to the correct values
    plotOverLine1.Source.Point1, plotOverLine1.Source.Point2 = \
                                         lines[line_key]

    #Set the number of points on this line to be interpolated to 100
    plotOverLine1.Source.Resolution = 100

    #Save the field data on this line (including derivatives of the
    #velocity field).
    SaveData('./postProcessing/linePlotData/{}.csv'\
             .format(line_key, time),
             proxy=plotOverLine1)
