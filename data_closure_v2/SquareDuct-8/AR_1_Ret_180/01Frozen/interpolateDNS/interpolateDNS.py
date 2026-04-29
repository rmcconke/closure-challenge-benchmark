'''Script to interpolate the given DNS data to the RANS grid and store the three
relevant fields; U_LES, tauij_LES and k_LES.'''

#================================================================================
#Libraries to be imported

import numpy as np
import matplotlib.pyplot as plt
from readOFInternalField import readOFInternalField
from writeOFFieldFile import writeOFFieldFile
from readDefFile import readDefFile
from scipy.interpolate import griddata
import os
import glob

#================================================================================
#Case dependent variables

defDict = readDefFile('../../caseDef')

h = defDict['h'] #Half channel height
Re_b = defDict['Re_b'] #Bulk Reynolds number
Re_tau = defDict['Re_tau'] #Friction Reynolds number
nu = defDict['nu'] #Kinematic viscosity
AR = defDict['AR'] #Duct aspect ratio

#Aspect ratio in file format; int is to ensure 14.4 becomes 14 as in the files
AR_file = int(AR)

#Friction Reynolds number in the file format (the target); the actually measured
#Re_tau's were lower than this so the Re is rounded up to either 180 or 360
if Re_tau < 180:
    Re_tau_file = 180
else:
    Re_tau_file = 360

#Path to the folder with the DNS data preceded by the general file names, with
#the actual variable name (e.g. U) replaced by {} such that the actual variable
#name can be substituted in later.
RefDataFileFormat = '../../RefData/{}' + f'_{AR_file}_{Re_tau_file}.prof.txt'

#File containing the cell centre coordinates of the RANS case
cellCentresFile = '../../meshes/beta11/constant/C'


#Calculate the bulk velocity from the bulk velocity Reynolds number
U_b = Re_b*nu/h

#================================================================================
#Reading in the files. Note that the DNS quantities are nondimensional

#Read in the cell centre coordinates of the RANS mesh; only those of the
#internal mesh are used.
cellCentres = readOFInternalField(cellCentresFile)


#Read in the y- and z-coordinates respectively. In the z-coordinates file, two
#arrays are stored; the first being the friction velocity, the second the
#z-coordinate. Since the friction velocity is not needed, only the z-coordinate
#is saved. The minus sign is there to convert the coordinates to the positive
#y-z plane (in which the RANS mesh is defined). Note that for the AR=1 case
#there is no ycoord file since ycoord==zcoord, so the zcoord is read in for y.
if AR_file != 1:
    _, zRef = -np.genfromtxt(RefDataFileFormat.format('zcoord'), comments='%',
                             encoding='latin1')
    yRef = -np.genfromtxt(RefDataFileFormat.format('ycoord'), comments='%',
                          encoding='latin1')
else: #AR = 1
    _, zRef, _ = -np.genfromtxt(RefDataFileFormat.format('zcoord'), comments='%',
                                encoding='latin1')
    yRef = np.array(zRef)
    


#Make a meshgrid of the y- and z-coordinates such that the y- and z-coordinate
#are available for each point. Then reshape this into an array with shape
#(Npoints,2), with the first column corresponding to y and the second to z.
refGridYZ = np.concatenate([A.reshape((-1,1)) for A in\
                            np.meshgrid(yRef, zRef, indexing='ij')], axis=-1)

#Read in the velocity data and convert to the shape (Npoints,1). The minus sign
#is included for Uy and Uz to convert to the positive y-z plane.
UxRef = np.genfromtxt(RefDataFileFormat.format('U'), comments='%',
                       encoding='latin1').reshape((-1,1))
UyRef = -np.genfromtxt(RefDataFileFormat.format('V'), comments='%',
                       encoding='latin1').reshape((-1,1))
UzRef = -np.genfromtxt(RefDataFileFormat.format('W'), comments='%',
                       encoding='latin1').reshape((-1,1))

#Read in the components of the Reynolds stress tensor. Note that since both the
#sign of y- and z need to be flipped when converting to the positive y-z plane,
#only tau12 and tau13 need a negative sign.
tau11Ref = np.genfromtxt(RefDataFileFormat.format('uu'), comments='%',
                         encoding='latin1').reshape((-1,1))
tau12Ref = -np.genfromtxt(RefDataFileFormat.format('uv'), comments='%',
                         encoding='latin1').reshape((-1,1))
tau13Ref = -np.genfromtxt(RefDataFileFormat.format('uw'), comments='%',
                         encoding='latin1').reshape((-1,1))
tau22Ref = np.genfromtxt(RefDataFileFormat.format('vv'), comments='%',
                         encoding='latin1').reshape((-1,1))
tau23Ref = np.genfromtxt(RefDataFileFormat.format('vw'), comments='%',
                         encoding='latin1').reshape((-1,1))
tau33Ref = np.genfromtxt(RefDataFileFormat.format('ww'), comments='%',
                         encoding='latin1').reshape((-1,1))

#Calculate k from the diagonal components of the Reynolds stress tensor.
kRef = (tau11Ref + tau22Ref + tau33Ref)/2


#================================================================================
#Interpolating to the RANS grid points. Note that all quantities are kept
#nondimensional in this step.

#Interpolate velocity components; nondimensionalize RANS coordinates.
UxInterp = griddata(refGridYZ, UxRef, cellCentres[:,1:]/h, method='cubic')
UyInterp = griddata(refGridYZ, UyRef, cellCentres[:,1:]/h, method='cubic')
UzInterp = griddata(refGridYZ, UzRef, cellCentres[:,1:]/h, method='cubic')

#Combine interpolated velocity components into a (Npoints,3) array.
UInterp = np.concatenate([UxInterp, UyInterp, UzInterp], axis=-1)

#Interpolate the Reynolds stress components; nondimensionalize RANS coordinates.
tau11Interp = griddata(refGridYZ, tau11Ref, cellCentres[:,1:]/h, method='cubic')
tau12Interp = griddata(refGridYZ, tau12Ref, cellCentres[:,1:]/h, method='cubic')
tau13Interp = griddata(refGridYZ, tau13Ref, cellCentres[:,1:]/h, method='cubic')
tau22Interp = griddata(refGridYZ, tau22Ref, cellCentres[:,1:]/h, method='cubic')
tau23Interp = griddata(refGridYZ, tau23Ref, cellCentres[:,1:]/h, method='cubic')
tau33Interp = griddata(refGridYZ, tau33Ref, cellCentres[:,1:]/h, method='cubic')

#Combine interpolated Reynolds stress components into a (Npoints,6) array.
tauInterp = np.concatenate([tau11Interp, tau12Interp, tau13Interp,
                            tau22Interp, tau23Interp, tau33Interp], axis=-1)

#Interpolate k; nondimensionalize RANS coordinates.
kInterp = griddata(refGridYZ, kRef, cellCentres[:,1:]/h, method='cubic')


#================================================================================
#Saving the interpolated arrays

#Check whether the interpolatedFields folder exists; if not, create it.
#If it does, remove its contents.
if os.path.isdir('./interpolatedFields/'):
    for f in glob.glob('./interpolatedFields/'):
        if os.path.isfile(f):
            os.remove(file)
else:
    os.mkdir('./interpolatedFields')

#Write the interpolated velocity field
writeOFFieldFile(UInterp*U_b, 'vector', './interpolatedFields/U_LES')

#Write the interpolated Reynolds stress field
writeOFFieldFile(tauInterp*U_b**2, 'symmTensor',
                 './interpolatedFields/tauij_LES')

#Write the interpolated turbulent kinetic energy field
writeOFFieldFile(kInterp*U_b**2, 'scalar',
                 './interpolatedFields/k_LES')
