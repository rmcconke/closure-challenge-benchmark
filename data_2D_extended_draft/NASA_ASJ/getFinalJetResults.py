import numpy as np
import glob
import matplotlib.pyplot as plt
from writeNasaResults import writeNasaResults
from readExpData import readSingleGraphDir




Djet = 2*0.0254
Mjet = 0.5
p = 101325
R = 287.05
T = 294.44444
gamma = 1.4

Ujet = Mjet*np.sqrt(gamma*R*T)


saveDir = '../../../../epsilonModel/baselineResults/'


header = '#Jet results run on the second to finest ' +\
         '2x97x97; 2x61x97; 2x257x225 grid\n'


stationsZoneDict = {'singleGraph_x2D' : 'x/Djet=2',
                    'singleGraph_x5D' : 'x/Djet=5',
                    'singleGraph_x10D' : 'x/Djet=10',
                    'singleGraph_x15D' : 'x/Djet=15',
                    'singleGraph_x20D' : 'x/Djet=20'}

#First centerline
centerlineDict = readSingleGraphDir('./postProcessing/singleGraph_y0D/')

x_Ux_centerline = np.hstack(((centerlineDict['x']/Djet).reshape((-1,1)),
                             (centerlineDict['Ux']/Ujet).reshape((-1,1))))

writeNasaResults(header, ['x/Dj', 'u/Uj'], {'Dwight 2022' : x_Ux_centerline},
                 saveDir + 'ASJ_u_vs_x.dat')

uZoneDict = {}
upvpZoneDict = {}
for singleGraph in stationsZoneDict.keys():

    singleGraphDict = readSingleGraphDir(f'./postProcessing/{singleGraph}/')

    y_Ux = np.hstack(((singleGraphDict['z']/Djet).reshape((-1,1)),
                      (singleGraphDict['Ux']/Ujet).reshape((-1,1))))

    uZoneDict[stationsZoneDict[singleGraph] + ', Dwight 2022'] = y_Ux

    upvp = -singleGraphDict['nut']*(singleGraphDict['dUx/dz'] +\
                                    singleGraphDict['dUz/dx'])

    y_upvp = np.hstack(((singleGraphDict['z']/Djet).reshape((-1,1)),
                        (upvp/Ujet**2).reshape((-1,1))))
    
    upvpZoneDict[stationsZoneDict[singleGraph] + ', Dwight 2022'] = y_upvp

writeNasaResults(header, ['y/Dj', 'u/Uj'], uZoneDict, 
                 saveDir + 'ASJ_u_at5stations.dat')
writeNasaResults(header, ['y/Dj', "u'v'/Uj^2"], upvpZoneDict,
                 saveDir + 'ASJ_uv_at5stations.dat')


