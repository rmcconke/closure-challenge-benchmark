import numpy as np
import glob

def textInLine(line):
    if line == '':
        return False
    return max([(ord(c)>96) & (ord(c)<101) | (ord(c)>101) & (ord(c)<123)\
                for c in line.lower()])

def readNasaZoneFile(file):
    with open(file) as f:
        data = f.read()



    dataLower = data.lower()


    #Find variables, these are assumed to be defined on a single line
    variableLineStartInd = dataLower.find('variables')
    variableLineEndInd = variableLineStartInd + \
                         dataLower[variableLineStartInd:].find('\n')
    variableLine = data[variableLineStartInd:variableLineEndInd]
    variables = variableLine.split('"')[1::2]

    zones = []
    findDataStart = False
    dataStartInds = []
    zoneInds = []

    #If there is only one zone in the file, it is not specifically mentioned
    #Hotfix: add the zeroth line as the zone line and add 'zone' as the key
    if 'zone' not in dataLower:
        zones.append('zone')
        zoneInds.append(0)
        findDataStart = True
    
    for i, (line, lowerLine) in enumerate(zip(data.split('\n'),
                                              dataLower.split('\n'))):
        if 'zone t=' in lowerLine or 'zone, t=' in lowerLine:
            zones.append(line.split('"')[1])
            zoneInds.append(i)
            findDataStart = True

        if findDataStart:
            if not textInLine(line):
                dataStartInds.append(i)
                findDataStart = False


    zoneInds.append(i+1)


    zoneDict = {}
    for i, zone in enumerate(zones):

        Buff = np.genfromtxt(file, skip_header=dataStartInds[i],
                             max_rows=zoneInds[i+1] - dataStartInds[i])

        zoneDict[zone] = dict([(variables[j], Buff[:,j])\
                               for j in range(len(variables))])
                

    return zoneDict


def findLatestTimeDir(case):
    '''Function to find the latest time directory of an OpenFOAM case.

    Input:
    case : path to the OpenFOAM case of which to find the latest time directory.

    Output:
    maxTimeDir : full path to the latest time directory in case'''

    dirs = glob.glob(case + '/*/')

    maxTime = -1

    for d in dirs:
        dirName = d[:-1].split('/')[-1]
        try:
            t = float(dirName)
        except:
            continue
        
        if t > maxTime:
            maxTimeDir = d
            maxTime = t

    if maxTime == -1:
        raise Exception(f"No time directories found in {case}")

    return maxTimeDir

def readSingleGraphDir(singleGraphDir):


    latestTimeDir = findLatestTimeDir(singleGraphDir)

    varDict = {}
    for file in glob.glob(f'{latestTimeDir}/*.xy'):
        varDict = {**readxyOrRawFile(file), **varDict}
    for file in glob.glob(f'{latestTimeDir}/*.raw'):
        varDict = {**readxyOrRawFile(file), **varDict}    

    return varDict
        

    

def readxyOrRawFile(file):

    Buff = np.genfromtxt(file)

    variables = ['x', 'y', 'z']
    if '.xy' in file:
        fileVars = file.split('/')[-1].replace('.xy', '').split('_')[1:]
    elif '.raw' in file:
        fileVars = file.split('/')[-1].replace('.raw', '').split('_')[:-1]
    for var in fileVars:
        if var == 'U':
            variables.append('Ux')
            variables.append('Uy')
            variables.append('Uz')
        elif var == 'wallShearStress':
            variables.append('wallShearStressx')
            variables.append('wallShearStressy')
            variables.append('wallShearStressz')
        elif var == 'gradU':
            variables.append('dUx/dx')
            variables.append('dUx/dy')
            variables.append('dUx/dz')
            variables.append('dUy/dx')
            variables.append('dUy/dy')
            variables.append('dUy/dz')
            variables.append('dUz/dx')
            variables.append('dUz/dy')
            variables.append('dUz/dz')
        elif var == 'LES':
            variables[-1] += '_LES'
        else:
            variables.append(var)


    varDict = dict([(variables[j], Buff[:,j]) for j in range(len(variables))])

    return varDict




