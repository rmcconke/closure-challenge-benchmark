'''Script to plot the convergence of velocity, pressure, k and omega with time at
certain probed locations. Requires the probe function to be enabled in the
system/controlDict during the run. The program outputs five convergence plots;
pressure, Ux, Uz, k and omega and saves these in the case directory. Since
simulations typically have very small timesteps, the number of points is usually
rather large (~100k). To boost performance, a piecewise linear spline is actually
plotted. The number of points to plot per second can be specified below.
The program is to be run using python 3 as follows:
    $ python3 probeConvergence.py

Author : Kaj Hoefnagel'''

#--------------------------------------------------------------------------------
#Libraries to be imported

import os
import glob
import numpy as np
import matplotlib.pyplot as plt
import matplotlib

#--------------------------------------------------------------------------------
#Function to read raw probe data files through time

def readRawProbeFile(file):
    '''Function to read in a single probe file in raw format. Works both for
    scalars and vectors.

    Inputs:
    file : Full path to the probes file to be read in

    Outputs:
    TArray : 1D numpy array holding the time instances at which the probes
             measurements were taken.
    DataArray : 3D numpy array; the zeroth axis corresponds to the time;
                the first axis corresponds to different probes and the last
                axis corresponds to vector components (e.g. Ux, Uy, Uz).'''

    #Open the file in read only format
    f = open(file)

    #Initialize probeDict; a dictionary which will later hold the location
    #data of each probe index.
    probeDict = {}

    #Initialize Data list, holding the data at each probe at each timestep
    Data = []

    #Initialize the time list, holding the time of each probe measurement
    T = []
    
    for line in f.readlines():
        
        #If the line starts with a hashtag, it is a commented line
        if line[0] == '#':

                #The probe locations are defined in the commented header.
                #Thus, if 'Probe' and '(' are in the commented line,
                #the probe location is extracted.
                if 'Probe' in line and '(' in line:

                        #Remove the brackets and split the line at spaces
                        probe_line = line.replace('(','').replace(')','').split()

                        #Third element of the split line is the probe index
                        probe_num = int(probe_line[2])

                        #The last three elements of the split line are the
                        #x-, y- and z-coordinates of the probe.
                        probe_loc = (probe_line[-3:])
                        probe_loc_str = '({}; {}; {})'.format(*probe_loc)

                        #The x-, y- and z-coordinates of the probe index
                        #are appended to the probe_dict as a string.
                        probeDict[probe_num] = probe_loc_str

                #If a line is a commented line, the code after this point
                #should not be executed. Continue skips any code in the current
                #loop and goes to the next line.
                continue

        #The next part is only executed if the line does not start with #
        numEntries = line.replace('\n','').split()
        t = float(numEntries[0])

        #If there are no brackets in the line, the field is a scalar. Then,
        #the probe data is simply extracted from the numerical entries.
        if ')' not in line:
            probeList = [[float(numEntry)] for numEntry in numEntries[1:]]

        #If there is a bracket in the line, it is a vector/tensor field.
        else:

            #probeList will hold various vectors; one vector for each probe.
            #vecList holds one such vector.
            probeList = []
            vecList = []

            #Loop over each entry in the current line (except the first one; time)
            for numEntry in numEntries[1:]:

                #If there is a ')' in the current entry, the vector is closed.
                #Then append the vecList to the probeList as it is a complete
                #vector. Also re-initialize the vecList so the next vector
                #can be added.
                if ')' in numEntry:
                    vecList.append(float(numEntry.replace(')', '')))
                    probeList.append(vecList)
                    vecList = []

                #If there is no ')' in the current entry, it is any vector entry
                #except the last. Such an entry can simply be added to the
                #veclist. The replace '(' with '' is to get rid of the '(' in
                #the first vector entry.
                else:
                    vecList.append(float(numEntry.replace('(', '')))

        #Append the probe data in the current line to the large data list.
        #Also append the extracted time-instance to the time list.
        Data.append(probeList)
        T.append(t)

    #Close the file to save memory
    f.close()

    #Convert the data and time lists to numpy arrays
    DataArray = np.array(Data)
    TArray = np.array(T)

    return TArray, DataArray, probeDict        

#--------------------------------------------------------------------------------
#Get the data, times and probe labels

#Get the available time directories in the postProcessing/convergenceProbes
#folder. If the run was restarted, there will be multiple folders here.
#By default these are not sorted, so timeDirsSorted are these directories sorted.
timeDirs = np.array(glob.glob('./postProcessing/convergenceProbes/*'))
timeDirsFloat = [float(timeDir.split('/')[-1]) for timeDir in timeDirs]
timeDirsSorted = timeDirs[np.argsort(timeDirsFloat)]

#Initialize dictionaries for field data, time data and probe locations
#respectively.
fieldProbeDict = {}
fieldTimeDict = {}
probeDictDict = {}

#Loop over each sorted time directory in the postProcessing/convergenceProbes
#folder.
for timeDir in timeDirsSorted:

    #Loop over each field (e.g. k) stored in the current timeDir
    for fieldFile in glob.glob(timeDir + '/*'):

        #Extract the field name from the fieldFile (which is the full path)
        field = fieldFile.split('/')[-1]
        
        TArray, DataArray, probeDict = readRawProbeFile(fieldFile)

        #If this field was already added to the fieldProbeDict at an earlier
        #time, append the new timesteps to the existing arrays.
        if field in fieldProbeDict.keys():
            fieldProbeDict[field] = np.vstack((fieldProbeDict[field], DataArray))
            fieldTimeDict[field] = np.hstack((fieldTimeDict[field], TArray))

        #If the field has not been added to the fieldProbeDict yet, add it.
        #Also add the probeDict to the probeDictDict (denoting the probe
        #locations)
        else:
            fieldProbeDict[field] = DataArray
            fieldTimeDict[field] = TArray
            probeDictDict[field] = probeDict


#--------------------------------------------------------------------------------
#Function to plot the convergence of a single field (e.g. k) for multiple probes.

def plotFieldConvergence(fieldProbe, fieldTime, probeDict, ylabel):
    '''Function to plot the convergence of a single field (e.g. k) for multiple
    probes.

    Inputs:
    fieldProbe : N x P array, with N the number of timesteps and P the number of
                 probes. This array holds the field data for each probe at each
                 timestep.
    fieldTime : length N array holding the time values.
    probeDict : Dictionary containing pairs of probe column index and plot label.
    ylabel : Label to put on the plot y-axis.'''

    #Initialize the figure
    plt.figure(figsize=(6,5))

    #Loop over each probe (probeInd indicates the column index).
    #For each probe, plot the field data through time and set the appropriate
    #label.
    for probeInd in range(np.shape(fieldProbe)[-1]):
        plt.plot(fieldTime, fieldProbe[:,probeInd], label=probeDict[probeInd])

    #Enable a grid, set the x- and y-labels and enable the legend
    plt.grid()
    plt.xlabel('T [sec]')
    plt.ylabel(ylabel)
    plt.legend(ncol = 2)

    #Determine the current y-lim, extent it downwards to make room for the legend
    ylim = plt.gca().get_ylim()
    yrange = np.diff(ylim)[0]
    plt.gca().set_ylim(ylim[0]-yrange*0.4, ylim[1])

    plt.tight_layout()

#--------------------------------------------------------------------------------
#Calling the plotting function for the various fields

#Update the font size of the plots
matplotlib.rcParams.update({'font.size' : 12})

#Call the plotting for each data field. A separate plot window is created for
#each. Also save the figure to the case directory. 
plotFieldConvergence(fieldProbeDict['U'][:,:,0], fieldTimeDict['U'],
                     probeDictDict['U'], r'$U_x$ [m/s]')
plt.savefig('Ux_convergence.pdf')

plotFieldConvergence(fieldProbeDict['U'][:,:,2], fieldTimeDict['U'],
                     probeDictDict['U'], r'$U_y$ [m/s]')
plt.savefig('Uy_convergence.pdf')

plotFieldConvergence(fieldProbeDict['p'][:,:,0], fieldTimeDict['p'],
                     probeDictDict['p'], r'$p$ [N/$m^2$]')
plt.savefig('p_convergence.pdf')

plotFieldConvergence(fieldProbeDict['k'][:,:,0], fieldTimeDict['k'],
                     probeDictDict['k'], r'$k$ [$m^2$/$s^2$]')
plt.savefig('k_convergence.pdf')

plotFieldConvergence(fieldProbeDict['omega'][:,:,0], fieldTimeDict['omega'],
                     probeDictDict['omega'], r'$\omega$ [$s^{-1}$]')
plt.savefig('omega_convergence.pdf')


#More variables can easily be added here

#Show all plot windows at once
plt.show()





        
