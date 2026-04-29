'''Script to plot the convergence of the various residuals with time. Requires
the residuals function to be enabled in the system/controlDict during the run.
The program outputs a single plot containing all available residuals.
The program is to be run using python3 as follows:
    $ python3 residualConvergence.py

Author : Kaj Hoefnagel'''

#--------------------------------------------------------------------------------
#Libraries to be imported

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import glob
import os


#--------------------------------------------------------------------------------
#Function to read .dat residual files

def readRawResidualFile(file):
    '''Function to read in a single residuals.dat file and convert it to a
    dictionary holding the various variables.

    Inputs:
    file : path to the residuals.dat file to be read in.

    Outputs:
    residualDict : Dictionary with time and the available residuals as keys,
                   with the array of values as a corresponding value.'''

    #Open the file in a memory safe way
    with open(file) as f:
        #Split f into lines; filter out empty lines
        lines = list(filter(None, f.read().split('\n')))

    for line in lines: #Loop over each line (including comments)
            
        #If the line starts with a hashtag, it is a commented line
        if line[0] == '#':

            #If Time in the line, it is the line describing the variables;
            #extract these.
            if 'time' in line.lower():

                #Format the line for further processing by replacing tabs
                #with spaces and removing the # (to make the line a comment).
                lineFormatted = line.replace('\t', ' ').replace('#', '')

                #Split the line on spaces (should be at least one space between
                #variables) and filter empty strings; this leaves the variables.
                resVars = list(filter(None, lineFormatted.lower().split(' ')))

                #Initialize the dictionary of residuals, with the variable as
                #the key and the list of values as a value. Initialized with
                #empty lists that are appended while reading rest of the file.
                residualDict = dict([(resVar, []) for resVar in resVars])
                

            #Further code should not be executed if the line is a comment
            continue

        #Replace tabs with spaces for consistent splitting in the next step
        lineFormatted = line.replace('\t', ' ')

        #Split the line on spaces and filter out empty strings to only keep
        #a list of numerical values (still in string format).
        lineSplit = list(filter(None, lineFormatted.split(' ')))

        #Loop over all expected residual variables. OpenFOAM can write a
        #shorter first row with N/A values, so missing entries are treated as
        #NaN to keep all arrays aligned.
        for i, resVar in enumerate(resVars):
            strValue = lineSplit[i] if i < len(lineSplit) else None

            #Try to convert the string value to a float and append to the list.
            #If this conversion is not possible (e.g. the values is 'N/A'),
            #append NaN to the list.
            try:
                residualDict[resVar].append(float(strValue))
            except (TypeError, ValueError):
                residualDict[resVar].append(np.nan)

    #Convert lists to arrays for speed
    for var in residualDict:
        residualDict[var] = np.array(residualDict[var])
    
    return residualDict

#--------------------------------------------------------------------------------
#Read in and combine residual data from multiple time directories (multiple time
#directories appear when the run was restarted).

#Get the available time directories in the postProcessing/residuals folder
#If the run was restarted, there will be multiple folders here.
#By default these are not sorted, so timeDirsSorted are these directories sorted.
timeDirs = np.array(glob.glob('./postProcessing/residuals/*'))
timeDirsFloat = [float(timeDir.split('/')[-1]) for timeDir in timeDirs]
timeDirsSorted = timeDirs[np.argsort(timeDirsFloat)]

#Initialize dictionary holding the residuals over time (potentially combined
#from multiple files if the run was restarted).
residualDict = {}

#Loop over each residual time directory
for timeDir in timeDirsSorted:

    #Get the residual dict for the current time folder, see readRawResidualFile
    #for more information.
    residualDictTimeDir = readRawResidualFile(timeDir + '/residuals.dat')

    #For each key (variable) in residualDictTimeDir, check if it already in
    #residualDict. If not, initialize it with the value from the current time
    #folder. If it is, append to the already set array from prior time folders.
    for key in residualDictTimeDir:
        if key in residualDict:
            residualDict[key] = np.append(residualDict[key],
                                           residualDictTimeDir[key])
        else:
            residualDict[key] = residualDictTimeDir[key]

# Ignore the initialization row at timestep 0. OpenFOAM writes N/A residuals
# there, which should not be included in the convergence plot.
validMask = residualDict['time'] != 0
for key in residualDict:
    validMask = validMask & np.isfinite(residualDict[key])

for key in residualDict:
    residualDict[key] = residualDict[key][validMask]

##TODO: implement piecewise linear spline that is plotted instead to boost
##      performance.

#--------------------------------------------------------------------------------
#Plotting

#Increase plot font size
matplotlib.rcParams.update({'font.size' : 16})

#Check if the convergencePlots directory already exists; if not, create it.
if not os.path.isdir('./convergencePlots'):
    os.mkdir('./convergencePlots')

#Dictionary of variables as they appear in the residuals.dat file and the
#corresponding legend label to use for them in the plot.
labelDict = {'ux' : r'$U_x$',
             'uy' : r'$U_y$',
             'uz' : r'$U_z$',
             'omega' : r'$\omega$',
             'nut' : r'$\nu_t$',
             'k' : r'$k$',
             'p' : r'$p$'}

#Markers to use for the various residuals
markers = ['o', 's', 'v', 'd', 'X', '^', '<']

#Parameters to get a good marker visualization.
#Number of markers per graph
nMarkers = 15

#Number of points between markers to get nMarkers
markerInterval  = max(1, int(len(residualDict['time'])/nMarkers))

#Number of residual graphs that are plotted (-1 since 'time' is also a key)
nGraphs = len(residualDict.keys()) - 1

#Array of offsets so the markers of various graphs don't overlap.
offsets = np.linspace(0, markerInterval, nGraphs+1, dtype=int)[:-1]


j = 0 #iterator that ignores keys that are not plotted (time and NaN)

plt.figure(figsize=(10,5))

#Loop over the variables in the residualDict
for i, var in enumerate(residualDict):

    #Don't plot time and residual arrays that contain NaNs
    if var == 'time' or np.isnan(residualDict[var]).max():
        continue

    #Plot the residual against time and add markers    
    plt.semilogy(residualDict['time'], residualDict[var], label=labelDict[var],
                 marker = markers[j], markevery=(offsets[j], markerInterval),
                 zorder=j+10, markersize=8)

    #Only increment j if the variable was plotted
    j += 1

#Decorators
plt.grid()
plt.xlabel('Iterations')
plt.ylabel('Normalized residual')
plt.legend(ncol=4, loc='upper center')

#Determine the current y-lim, extent it upwards to make room for the legend
ylim = plt.gca().get_ylim()
yrange = np.log10(ylim[1]/ylim[0])
plt.gca().set_ylim(ylim[0], ylim[1]*10**(yrange*0.3))
plt.tight_layout()

#Save the figure
plt.savefig('convergencePlots/residualConvergence.pdf')

                
