'''Script to read in the mean data on certain lines produced by the
linePlotter.py script. Mean profiles are plotted together with reference data
from NASA. The program is to be run using python 3 as follows:
    $ python3 comparisonPlotter.py

Author : Kaj Hoefnagel
'''

#--------------------------------------------------------------------------------
#Libraries to be imported

import numpy as np
import matplotlib.pyplot as plt
import os
import glob
import matplotlib
import sys

#--------------------------------------------------------------------------------
#Definitions

r_jet = 0.0254 #Nozzle radius (1 inch)
D_jet = 2*r_jet #Nozzle diameter

#File containing the reference RANS data from NASA
ref_file = '../../NASARefCFDData/jetsubsonic_wind_sstv.dat'


#--------------------------------------------------------------------------------
#Reading in the big domain data


#Get a list of all csv files in the postProcessing/linePlotData directory.
#Note that glob.glob also includes the full path.
files = glob.glob('./postProcessing/linePlotData/*.csv')

#Initialize OF; the dictionary holding the data from our OpenFOAM run.
#The keys will be the various lines (centerline, x/D=2, etc...).
OF = {}

#Initialize OF_keys; the dictionary holding the column indices corresponding to
#the variables. Each variable is a key and the index is returned.
#For instance OF_keys['U:0'] returns the column index of the x-velocity.
OF_keys = {}

#Loop over each csv file in the postProcessing/linePlotData directory
for file in files:

    #Extract the file name (anything behind the last / is part of the full path)
    fname = file.split('/')[-1]

    #Extract the location from the file name
    loc = fname.replace('.csv', '')

    #Get the data from the csv file
    data = np.genfromtxt(file, skip_header=1, delimiter=',')

    #Add the data of the current location to the dictionary using the location
    #as a key.
    OF[loc] = data

    #Add the data keys to the OF_keys dict
    f = open(file)
    keys = f.readlines()[0].replace('\n','').replace('"','').split(',')
    f.close()
    key_dict = {}
    for i, key in enumerate(keys):
        key_dict[key] = i
    OF_keys[loc] = key_dict

#Calculate the u'v' component: u'v' = -nu_t*(du/dy + dv/dx)
#Append it to the OF array as a new column and add the column index to OF_keys.
for loc in OF.keys():
    
    up_vp = np.reshape(-OF[loc][:,OF_keys[loc]['nutMean']]*\
                       (OF[loc][:,OF_keys[loc]['Gradients:2']] +\
                        OF[loc][:,OF_keys[loc]['Gradients:6']]),
                       (np.shape(OF[loc])[0], 1))
    OF[loc] = np.hstack((OF[loc], up_vp))
    OF_keys[loc]['up_vp'] = np.shape(OF[loc])[1]-1


#--------------------------------------------------------------------------------
#Reading in the reference RANS data from NASA

#Read the lines from the reference file provided by NASA
f = open(ref_file)
lines = f.readlines()
f.close()

#Initialize the REF dictionary, holding the reference data at each location.
REF = {}

#The file contains each location as a zone. Each zone is started with a line with
#the name of the zone. This is then followed by the data at that zone.
#zone_lines is a list holding the line numbers of these zone name lines.
#zones is a list holding the names of each zone.
zone_lines = []
zones = []
for i, line in enumerate(lines):
    if line[:4] == 'ZONE':
        zone_lines.append(i)
        zones.append(line.split('"')[-2])

#Append the line number of last line
zone_lines.append(i) 

#Loop over each zone, extract the lines between two name lines; this is the data.
#This data is then added to the REF dictionary, with the extracted zone name as
#they key.
for z, zone in enumerate(zones):
    REF[zone] = np.genfromtxt(ref_file, skip_header=zone_lines[z]+1,
                              max_rows = zone_lines[z+1] - zone_lines[z] - 1)



#--------------------------------------------------------------------------------
#Plotting over the centerline

#Increase font size
matplotlib.rcParams.update({'font.size' : 9})

#Calculate the velocity of the jet; this is extracted from the mean velocity
#at the centerline at x=0.
U_jet = OF['centerline'][0,OF_keys['centerline']['UMean:0']]


#Initialize lists holding the line objects to put in the legend- and the
#corresponding labels to put in the legend respectively.
legendLines = []
legendLabels = []

#Initialize the centerline figure
fig = plt.figure(num=1, figsize=(6.7,3.4))

#Centerline x-velocity
plt.subplot(1,2,1)
plt.plot(OF['centerline'][:,OF_keys['centerline']['Points:0']]/D_jet,
         OF['centerline'][:,OF_keys['centerline']['UMean:0']]/U_jet,
         label=r'OpenFOAM $\mu$', c='k', linestyle=':')
plt.plot(REF['y/Dj=0 (centerline)'][:,0], REF['y/Dj=0 (centerline)'][:,2],
         label='WIND (ref)', c='k')
plt.xlim([0,22])
plt.xlabel(r'$x$/$D_{jet}$ [-]')
plt.ylabel(r'$u$/$U_{jet}$ [-]')
plt.grid()



#Centerline k
plt.subplot(1,2,2)
line, = plt.plot(OF['centerline'][:,OF_keys['centerline']['Points:0']]/D_jet,
                 OF['centerline'][:,OF_keys['centerline']['kMean']]/\
                 (U_jet*U_jet), c='k', linestyle=':')
legendLines.append(line)
legendLabels.append(r'OpenFOAM $\mu$')
line, = plt.plot(REF['y/Dj=0 (centerline)'][:,0],
                 REF['y/Dj=0 (centerline)'][:,5], c='k')
legendLines.append(line)
legendLabels.append('WIND (ref)')
plt.xlim([0,22])
plt.xlabel(r'$x$/$D_{jet}$ [-]')
plt.ylabel(r'$k$/$U_{jet}^2$ [-]')
plt.grid()

fig.legend(legendLines, legendLabels,
           'lower center', ncol = 2)
plt.tight_layout()
plt.subplots_adjust(bottom=0.29)
plt.savefig('./centerlinePlots.pdf')



#--------------------------------------------------------------------------------
#Plotting at various x/D_jet locations

#Define a color for each x/D_jet location
color_dict = {'2' : 'r',
              '5' : 'k',
              '10' : 'b',
              '15' : 'g',
              '20' : 'm'}

legendLines = []
legendLabels = []

fig = plt.figure(num=2, figsize=(6.7,7))

#x-velocity at various x/D_jet
plt.subplot(2,2,1)
for i, key in enumerate(OF.keys()):
    if 'x_over_D' in key:
        x_over_D = key.replace('x_over_D_', '')
        plt.plot(OF[key][:,OF_keys[key]['UMean:0']]/U_jet,
                 OF[key][:,OF_keys[key]['Points:2']]/D_jet,
                 c=color_dict[x_over_D], linestyle=':')

for key in REF.keys():
    if 'x/Dj=' in key:
        x_over_D = key.replace('x/Dj=', '')
        plt.plot(REF[key][:,2], REF[key][:,1],
                 c=color_dict[x_over_D])
plt.ylim([0,1.5])
plt.xlabel(r'$u$/$U_{jet}$ [-]')
plt.ylabel(r'$y$/$D_{jet}$ [-]')
plt.grid()


#z-velocity at various x/D_jet
plt.subplot(2,2,2)
for i, key in enumerate(OF.keys()):
    if 'x_over_D' in key:
        x_over_D = key.replace('x_over_D_', '')
        plt.plot(OF[key][:,OF_keys[key]['UMean:2']]/U_jet,
                 OF[key][:,OF_keys[key]['Points:2']]/D_jet,
                 c=color_dict[x_over_D], linestyle=':')

for key in REF.keys():
    if 'x/Dj=' in key:
        x_over_D = key.replace('x/Dj=', '')
        plt.plot(REF[key][:,3], REF[key][:,1],
                 c=color_dict[x_over_D])

plt.ylim([0,1.5])
plt.xlabel(r'$v$/$U_{jet}$ [-]')
plt.ylabel(r'$y$/$D_{jet}$ [-]')
plt.grid()



#u'v' at various x/D_jet
plt.subplot(2,2,3)
for i, key in enumerate(OF.keys()):
    if 'x_over_D' in key:
        x_over_D = key.replace('x_over_D_', '')
        plt.plot(OF[key][:,OF_keys[key]['up_vp']]/(U_jet*U_jet),
                 OF[key][:,OF_keys[key]['Points:2']]/D_jet,
                 c=color_dict[x_over_D], linestyle=':')

for key in REF.keys():
    if 'x/Dj=' in key:
        x_over_D = key.replace('x/Dj=', '')
        plt.plot(REF[key][:,4], REF[key][:,1],
                 c=color_dict[x_over_D])
plt.ylim([0,1.5])
plt.xlabel(r'$\overline{u^\prime v^\prime}$/$U_{jet}^2$ [-]')
plt.ylabel(r'$y$/$D_{jet}$ [-]')
plt.grid()
      


#k at various x/D_jet
plt.subplot(2,2,4)
for i, key in enumerate(OF.keys()):
    if 'x_over_D' in key:
        x_over_D = key.replace('x_over_D_', '')
        line, = plt.plot(OF[key][:,OF_keys[key]['kMean']]/(U_jet*U_jet),
                 OF[key][:,OF_keys[key]['Points:2']]/D_jet,
                 c=color_dict[x_over_D], linestyle=':')
        if x_over_D == '2':
            legendLines.append(line)
            legendLabels.append(r'OpenFOAM $\mu$')
for key in REF.keys():
    if 'x/Dj=' in key:
        x_over_D = key.replace('x/Dj=', '')
        line, = plt.plot(REF[key][:,5], REF[key][:,1], c=color_dict[x_over_D])
        legendLines.append(line)
        legendLabels.append(r'WIND, $x$/$D_{jet}=$'+x_over_D)
plt.ylim([0,1.5])
plt.xlabel(r'$k$/$U_{jet}^2$ [-]')
plt.ylabel(r'$y$/$D_{jet}$ [-]')
plt.grid()


fig.legend(legendLines, legendLabels, 'lower center', ncol = 3)
plt.tight_layout()
plt.subplots_adjust(bottom=0.19)
plt.savefig('./x_over_D_plots.pdf')
plt.show()

