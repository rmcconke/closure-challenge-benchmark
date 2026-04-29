import numpy as np
import glob
import matplotlib.pyplot as plt
from writeNasaResults import writeNasaResults
from readExpData import readSingleGraphDir


M = 0.2
Tinf = 300
gamma = 1.4
R = 287.05
pinf = 101325


Uinf = M*np.sqrt(gamma*R*Tinf)
rhoinf = pinf/(Tinf*R)
nuinf = 1.562e-5/rhoinf

saveDir = '../../../epsilonModel/baselineResults/'

header = '#Flat plate results run on the finest 545 x 385 grid\n'


plateDict = readSingleGraphDir('./postProcessing/singleGraph_y0')

wallShearStress = np.linalg.norm(np.vstack([plateDict['wallShearStressx'],
                                            plateDict['wallShearStressy'],
                                            plateDict['wallShearStressz']]),
                                 axis=0)*rhoinf

Cf = wallShearStress/(0.5*rhoinf*Uinf**2)

x_Cf = np.hstack((plateDict['x'].reshape((-1,1)), Cf.reshape((-1,1))))

writeNasaResults(header, ['x', 'Cf'], {'Dwight 2022' : x_Cf}, 
                 saveDir + '2DZP_cf.dat')





profileDict = readSingleGraphDir('./postProcessing/singleGraph_x0.97')

tau_w = np.interp(0.97, plateDict['x'], wallShearStress)

uPlus = profileDict['Ux']/np.sqrt(tau_w/rhoinf)

yPlus = profileDict['z']*np.sqrt(tau_w/rhoinf)/nuinf

logYPlus_uPlus = np.hstack((np.log10(yPlus).reshape((-1,1)),
                            uPlus.reshape((-1,1))))

writeNasaResults(header, ['log(y+)', 'u+'], {'Dwight 2022' : logYPlus_uPlus},
                 saveDir + '2DZP_u+y+.dat')
                 

