'''Script to compare NASA-Hump 00Baseline results with LES reference data.'''

#================================================================================
#Libraries to include
import numpy as np
import matplotlib.pyplot as plt
from readExpData import readSingleGraphDir, getVTKWallFaceSet
from readDefFile import readDefFile
import pickle
import matplotlib
from matplotlib.lines import Line2D
import os
import csv

#Increase default plot fontsize to 15
matplotlib.rcParams.update({'font.size' : 15})


#================================================================================
#Definition of casepaths, plotting parameters and reading in case variables

baselineDir = '00Baseline'
LESPath = 'RefData'

#Locations of the single graphs; profiles are plotted at these locations
singleGraphLocs = ['x0.65c', 'x0.8c', 'x0.9c', 'x1.0c', 'x1.1c', 'x1.2c', 'x1.3c']

labels = ['RANS(SST)', 'LES']
linestyles = ['dashed', '']
colors = ['gray', 'black']
marray = ['none', 'o']
ms = 4

if not os.path.isdir('Figures'):
    os.mkdir('Figures')


def writeCsv(fileName, fieldNames, rows):
    with open(fileName, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldNames, delimiter='\t')
        writer.writeheader()
        writer.writerows(rows)


def interpWithNan(xNew, xOld, yOld):
    '''Interpolate yOld(xOld) to xNew and use NaN outside the source range.'''

    sortInds = np.argsort(xOld)
    xOld = np.asarray(xOld)[sortInds]
    yOld = np.asarray(yOld)[sortInds]

    yNew = np.interp(xNew, xOld, yOld)
    yNew[(xNew < xOld[0]) | (xNew > xOld[-1])] = np.nan

    return yNew

#Calculate relevant variables from the case definition
defDict = readDefFile('caseDef')
Tref = defDict['Tref'] #Reference temperature
R = defDict['R'] #Specific gas constant
gamma = defDict['gamma'] #Heat capacity ratio
Mref = defDict['Mref'] #Reference Mach number
c = defDict['c'] #Hump chord length
Re_c = defDict['Re_c'] #Chord-based Reynolds number
aref = np.sqrt(gamma*R*Tref) #Reference speed of sound
Uinf = Mref*aref #Reference velocity
nu = Uinf*c/Re_c #Kinematic viscosity


#================================================================================
#Read in the NASA LES results and reshape to a point mesh.

if not os.path.isfile(f'{LESPath}/pickledLESData.pickle'):
    import sys
    sys.path.insert(0, f'{LESPath}/')
    from readAndPickle import readAndPickle
    readAndPickle(LESPath)

with open(f'{LESPath}/pickledLESData.pickle', 'rb') as f:
    zoneDict1D = pickle.load(f)

zoneDict = {}

for zone in zoneDict1D:
    zoneDict[zone] = {}
    minX = np.min(zoneDict1D[zone]['x/c'])
    i1 = np.sum(np.abs(zoneDict1D[zone]['x/c'] - minX) < 1e-8*abs(minX))
    j1 = int(zoneDict1D[zone]['x/c'].size/i1 + 0.5)

    for var in zoneDict1D[zone]:
        zoneDict[zone][var] = zoneDict1D[zone][var].reshape((i1, j1))

del zoneDict1D

meshDict = {}

for var in zoneDict['Fine Grid']:
    meshDict[var] = np.vstack((zoneDict['Fine Grid'][var][:,::2],
                               zoneDict['Coarse Grid'][var][1:]))

del zoneDict


#================================================================================
#Extract Cp and Cf at the wall from the LES point grid.

meshDict['Cp'] = (meshDict['p/pinf'] - 1)/(0.5*Uinf**2)*R*Tref

dx = meshDict['x/c'][0, 1:] - meshDict['x/c'][0, :-1]
dy = meshDict['y/c'][0, 1:] - meshDict['y/c'][0, :-1]
dr = np.sqrt(dx**2 + dy**2)

Rwall = np.array([[dx/dr, dy/dr],
                  [-dy/dr, dx/dr]])

dUdx = (meshDict['dUdx'][0, 1:] + meshDict['dUdx'][0, :-1])/2
dUdy = (meshDict['dUdy'][0, 1:] + meshDict['dUdy'][0, :-1])/2
dVdx = (meshDict['dVdx'][0, 1:] + meshDict['dVdx'][0, :-1])/2
dVdy = (meshDict['dVdy'][0, 1:] + meshDict['dVdy'][0, :-1])/2

gradU = np.array([[dUdx, dUdy],
                  [dVdx, dVdy]])*Uinf/c

gradUWN = np.einsum('ijm,jkm,lkm->ilm', Rwall, gradU, Rwall)
CfLESWall = nu/(0.5*Uinf**2)*gradUWN[0,1]
xLESWall = (meshDict['x/c'][0, 1:] + meshDict['x/c'][0, :-1])/2


def interpolateLESProfile(xLoc, var):
    '''Interpolate a LES field profile at a requested x/c station.'''

    values = []
    yVals = []

    for i in range(meshDict['x/c'].shape[0]):
        xRow = meshDict['x/c'][i]
        sortInds = np.argsort(xRow)
        xSorted = xRow[sortInds]

        if xLoc < xSorted[0] or xLoc > xSorted[-1]:
            continue

        yVals.append(np.interp(xLoc, xSorted, meshDict['y/c'][i][sortInds]))
        values.append(np.interp(xLoc, xSorted, var[i][sortInds]))

    yVals = np.array(yVals)
    values = np.array(values)
    sortInds = np.argsort(yVals)

    return yVals[sortInds], values[sortInds]


#================================================================================
#Read in baseline wall quantities.

wallDictBaseline = readSingleGraphDir(f'{baselineDir}/postProcessing/wallValues/')

xWallPoints, _, zWallPoints = getVTKWallFaceSet(baselineDir)
wallTangentVecUnnormalized = np.vstack((xWallPoints[1:] - xWallPoints[:-1],
                                        zWallPoints[1:] - zWallPoints[:-1]))
wallTangentVec = wallTangentVecUnnormalized/\
                 np.linalg.norm(wallTangentVecUnnormalized, axis=0)

# RANS skin friction is computed from the wall-tangential component of tau_w.
# The minus sign matches the wall-point/tangent orientation used by the VTK wall.
tauWallTangential = wallDictBaseline['wallShearStressx']*wallTangentVec[0] +\
                    wallDictBaseline['wallShearStressz']*wallTangentVec[1]
wallDictBaseline['Cf'] = -tauWallTangential/(0.5*Uinf**2)
wallDictBaseline['Cp'] = wallDictBaseline['p']/(0.5*Uinf**2)

xSSTWall = wallDictBaseline['x']/c
wallSideBySideRows = []
cpLESOnSST = interpWithNan(xSSTWall, meshDict['x/c'][0], meshDict['Cp'][0])
cfLESOnSST = interpWithNan(xSSTWall, xLESWall, CfLESWall)

for xVal, cpSST, cpLES, cfSST, cfLES in zip(
    xSSTWall,
    wallDictBaseline['Cp'],
    cpLESOnSST,
    wallDictBaseline['Cf'],
    cfLESOnSST,
):
    if np.isnan(cpLES) or np.isnan(cfLES):
        continue

    wallSideBySideRows.append({
        'x_over_c': xVal,
        'Cp_RANS_SST': cpSST,
        'Cp_LES': cpLES,
        'Cf_RANS_SST': cfSST,
        'Cf_LES': cfLES,
    })

writeCsv(
    'Figures/wall_Cp_Cf_NASA.csv',
    ['x_over_c', 'Cp_RANS_SST', 'Cp_LES', 'Cf_RANS_SST', 'Cf_LES'],
    wallSideBySideRows,
)


#================================================================================
#Plotting Cp and Cf along the wall.

#Plot Cp
plt.figure(num=1, figsize=(10,5))
plt.plot(wallDictBaseline['x']/c, wallDictBaseline['Cp'],
         c=colors[0], lw=2, linestyle=linestyles[0], zorder=5,
         label=labels[0], marker=marray[0], markersize=ms)
plt.plot(meshDict['x/c'][0], meshDict['Cp'][0],
         c=colors[1], lw=2, linestyle=linestyles[1], zorder=2,
         label=labels[1], marker=marray[1], markersize=ms)

plt.xlim([-0.5, 1.6])
plt.ylim([1.15, -1])
plt.grid()
plt.xlabel('x/c [-]', fontsize=18)
plt.ylabel(r'$C_p$ [-]', fontsize=18)
leg = plt.legend(bbox_to_anchor=(0.5, 1.15), loc='upper center',
                 ncol=len(labels), borderaxespad=0., fontsize=15)
leg.set_zorder(100)
plt.tight_layout(rect=[0, 0, 1, 1])
plt.savefig('Figures/compareCpWall-NASA.pdf')

#Plot Cf
plt.figure(num=2, figsize=(10,5))
plt.plot(wallDictBaseline['x']/c, wallDictBaseline['Cf'],
         c=colors[0], lw=2, linestyle=linestyles[0], zorder=5,
         label=labels[0], marker=marray[0], markersize=ms)
plt.plot(xLESWall, CfLESWall,
         c=colors[1], lw=2, linestyle=linestyles[1], zorder=2,
         label=labels[1], marker=marray[1], markersize=4, markevery=20)

plt.xlim([-0.5, 1.6])
plt.ylim([-0.004, 0.008])
plt.xticks([-0.40, -0.20, 0.00, 0.20, 0.40, 0.60, 0.80, 1.00, 1.20, 1.40])
plt.yticks([-0.004, 0, 0.004, 0.008])
plt.grid()
plt.xlabel('x/c [-]', fontsize=20)
plt.ylabel(r'$C_f$ [-]', fontsize=20)
leg = plt.legend(bbox_to_anchor=(0.5, 1.15), loc='upper center',
                 ncol=len(labels), borderaxespad=0., fontsize=15.5)
leg.set_zorder(100)
plt.tight_layout(rect=[0, 0, 1, 1])
plt.savefig('Figures/compareCfWall-NASA.pdf')


#================================================================================
#Plotting Ux, k and upwp profiles at the singleGraph locations.

ind1 = np.where(wallDictBaseline['x']/c > 0.62)[0][0]
ind2 = np.where(wallDictBaseline['x']/c < 1.42)[0][-1]

for figNum in range(3, 6):
    plt.figure(num=figNum, figsize=(10,4.5))
    plt.plot(wallDictBaseline['x'][ind1:ind2]/c,
             wallDictBaseline['z'][ind1:ind2]/c, c='k')

lesK = 0.5*(meshDict['uu/Uinf^2'] + meshDict['vv/Uinf^2'] + meshDict['ww/Uinf^2'])
lesUpwp = meshDict['uv/Uinf^2']
profileSideBySideRows = []

for loc in singleGraphLocs:
    baselineDict = readSingleGraphDir(f'{baselineDir}/postProcessing/singleGraph_{loc}/')

    if all(key in baselineDict for key in ('nut', 'dUx/dz', 'dUz/dx')):
        baselineDict['upwp'] = -baselineDict['nut']*(baselineDict['dUx/dz'] +\
                                                     baselineDict['dUz/dx'])
    else:
        # Older 00Baseline outputs do not include gradU. Fall back to the
        # dominant vertical-gradient term from the sampled velocity profile.
        baselineDict['upwp'] = -baselineDict['nut']*\
                               np.gradient(baselineDict['Ux'], baselineDict['z'])

    x = float(loc[1:-1])

    for figNum in range(3, 6):
        plt.figure(num=figNum)
        plt.plot([x]*2, [baselineDict['z'][0]/c, baselineDict['z'][-1]/c],
                 c='lightgrey', lw=2, zorder=0)

    Fu = 0.1
    Fk = 1
    Fuv = 2

    yLES, uLES = interpolateLESProfile(x, meshDict['U/Uinf'])
    _, kLES = interpolateLESProfile(x, lesK)
    _, upwpLES = interpolateLESProfile(x, lesUpwp)

    ySST = baselineDict['z']/c
    uSST = baselineDict['Ux']/Uinf
    kSST = baselineDict['k']/Uinf**2
    upwpSST = baselineDict['upwp']/Uinf**2
    uLESOnSST = interpWithNan(ySST, yLES, uLES)
    kLESOnSST = interpWithNan(ySST, yLES, kLES)
    upwpLESOnSST = interpWithNan(ySST, yLES, upwpLES)

    for yVal, u0, u1, k0, k1, uv0, uv1 in zip(
        ySST,
        uSST,
        uLESOnSST,
        kSST,
        kLESOnSST,
        upwpSST,
        upwpLESOnSST,
    ):
        if np.isnan(u1) or np.isnan(k1) or np.isnan(uv1):
            continue

        profileSideBySideRows.append({
            'station_x_over_c': x,
            'wall_normal_over_c': yVal,
            'Ux_over_Uref_RANS_SST': u0,
            'Ux_over_Uref_LES': u1,
            'k_over_Uref2_RANS_SST': k0,
            'k_over_Uref2_LES': k1,
            'uv_over_Uref2_RANS_SST': uv0,
            'uv_over_Uref2_LES': uv1,
        })

    #Plotting Ux profiles
    plt.figure(num=3)
    plt.plot(x + np.array([0, *Fu*baselineDict['Ux']/Uinf]),
             np.array([baselineDict['z'][0]/c, *baselineDict['z']/c]),
             c=colors[0], lw=2, linestyle=linestyles[0], zorder=5,
             marker=marray[0], markersize=ms)
    plt.plot(x + Fu*uLES, yLES,
             c=colors[1], lw=2, linestyle=linestyles[1], zorder=5,
             marker=marray[1], markersize=ms, markevery=3)

    #Plotting k profiles
    plt.figure(num=4)
    plt.plot(x + np.array([0, *Fk*baselineDict['k']/Uinf**2]),
             np.array([baselineDict['z'][0]/c, *baselineDict['z']/c]),
             c=colors[0], lw=2, linestyle=linestyles[0], zorder=5,
             marker=marray[0], markersize=ms)
    plt.plot(x + Fk*kLES, yLES,
             c=colors[1], lw=2, linestyle=linestyles[1], zorder=5,
             marker=marray[1], markersize=ms, markevery=3)

    #Plotting u'w' profiles
    plt.figure(num=5)
    if 'upwp' in baselineDict:
        plt.plot(x + np.array([0, *Fuv*baselineDict['upwp']/Uinf**2]),
                 np.array([baselineDict['z'][0]/c, *baselineDict['z']/c]),
                 c=colors[0], lw=2, linestyle=linestyles[0], zorder=5,
                 marker=marray[0], markersize=ms)
    plt.plot(x + Fuv*upwpLES, yLES,
             c=colors[1], lw=2, linestyle=linestyles[1], zorder=5,
             marker=marray[1], markersize=ms, markevery=3)

writeCsv(
    'Figures/velocity_shear_profiles_NASA.csv',
    [
        'station_x_over_c',
        'wall_normal_over_c',
        'Ux_over_Uref_RANS_SST',
        'Ux_over_Uref_LES',
        'k_over_Uref2_RANS_SST',
        'k_over_Uref2_LES',
        'uv_over_Uref2_RANS_SST',
        'uv_over_Uref2_LES',
    ],
    profileSideBySideRows,
)

legendLines = [Line2D([0,1], [0,0], linestyle=linestyles[i],
                      c=colors[i], marker=marray[i], lw=2)
               for i in range(2)]

#Decorate and save the Ux profile plot
plt.figure(num=3)
plt.xlabel(r'$0.1U_x/U_{ref} + x/c$ [-]', fontsize=19)
plt.ylabel('y/c [-]', fontsize=19)
plt.ylim(0,0.15)
plt.xlim(0.625,1.41)
plt.yticks([0, 0.05, 0.1, 0.15])
plt.xticks([0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3])
leg = plt.legend(legendLines, labels, bbox_to_anchor=(0.5, 1.2),
                 loc='upper center', ncol=len(labels), borderaxespad=0.,
                 fontsize=16)
leg.set_zorder(100)
plt.tight_layout(rect=[0, 0, 1, 1])
plt.savefig('Figures/compareUxProfiles_NASA.pdf')

#Decorate and save the k profile plot
plt.figure(num=4)
plt.xlabel(r'$k/U_{ref}^2 + x/c$ [-]', fontsize=21)
plt.ylabel('y/c [-]', fontsize=21)
plt.ylim(0,0.15)
plt.xlim(0.62,1.4)
plt.yticks([0, 0.05, 0.1, 0.15])
plt.xticks([0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3])
leg = plt.legend(legendLines, labels, bbox_to_anchor=(0.5, 1.2),
                 loc='upper center', ncol=len(labels), borderaxespad=0.,
                 fontsize=16)
leg.set_zorder(100)
plt.tight_layout(rect=[0, 0, 1, 1])
plt.savefig('Figures/comparekProfiles_NASA.pdf')

#Decorate and save the u'w' profile plot
plt.figure(num=5)
plt.xlabel(r'$2\overline{u^\prime v^\prime}/U_{ref}^2 + x/c$ [-]', fontsize=21)
plt.ylabel('y/c [-]', fontsize=21)
plt.ylim(0,0.15)
plt.xlim(0.625,1.35)
plt.yticks([0, 0.05, 0.1, 0.15])
plt.xticks([0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3])
leg = plt.legend(legendLines, labels, bbox_to_anchor=(0.5, 1.2),
                 loc='upper center', ncol=len(labels), borderaxespad=0.,
                 fontsize=16)
leg.set_zorder(100)
plt.tight_layout(rect=[0, 0, 1, 1])
plt.savefig('Figures/compareupwpProfiles_NASA.pdf')
