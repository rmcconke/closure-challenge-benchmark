'''File containing multiple functions that are useful for reading data files.
There are three main functions, while the rest are used as helper functions.
The three main functions are: getVTKWallFaceSet, readNasaZoneFile and
readSingleGraphDir.

Author : Kaj Hoefnagel
'''

#================================================================================
#Libraries to include

import numpy as np
import glob

#================================================================================
#Simple function to check whether there is text in a line

def textInLine(line):
    '''Function to check if a certain line has text in it or only numbers.
    This is done by checking if there are any letters in the line with the
    exception of the letter e to prevent recognizing e.g. 1.4e-10 as text.'''

    #If the line is empty it of course doesn't contain any text
    if line == '':
        return False

    #Create an array of booleans, each corresponding to a character in the line.
    #If that character is a letter (excluding e), its boolean is True. If any
    #boolean in this array is true, the function returns True, else it returns
    #False.
    return max([(ord(c)>96) & (ord(c)<101) | (ord(c)>101) & (ord(c)<123)\
                for c in line.lower()])

#================================================================================
#Function to extract point coordinates from a faceSet converted to VTK format.

def getVTKWallFaceSet(caseDir):
    '''Function to extract point coordinates of a faceSet converted to ASCII
    VTK format. The faceSet should be called wallFaceSet. The conversion to
    ASCII VTK is performed as:
        foamToVTK -ascii -faceSet wallFaceSet

    Inputs:
    caseDir : Directory of the case, if the conversion to ASCII VTK was
              successful, it should contain the file
              VTK/wallFaceSet/wallFaceSet_0.vtk

    Outputs:
    xWallPoints : 1D array of x-coordinates of the wall points.
    yWallPoints : 1D array of y-coordinates of the wall points.
    zWallPoints : 1D array of z-coordinates of the wall points.'''

    #Load the wallFaceSet ASCII VTK file into a string.
    with open(f'{caseDir}/VTK/wallFaceSet/wallFaceSet_0.vtk') as f:
        data = f.read()

    #Extract the data between the first enter after POINTS and ending at
    #POLYGONS.
    coordsStr = data.split('POINTS')[1].split('\n', 1)[1].split('POLYGONS')[0].\
                replace('\n', ' ')

    #Convert the string of wall coordinates to an array of numbers (1D). It is
    #structured as x1, y1, z1, x2, y2, z2, ..., xN, yN, zN.
    coords = np.array([float(coord) for coord in filter(None,
                                                        coordsStr.split(' '))])

    #Extract the wall points from the 1D array of numbers. Only uneven points
    #are used, as the even points only have a different y-coordinate since
    #the mesh is essentially 2D in the x-z plane, but has a 1-cell thickness in
    #y-direction.
    xWallPoints, yWallPoints, zWallPoints =\
                                     coords[::6], coords [1::6], coords[2::6]

    #Apparently these are not sorted; sort based on the x-coordinate
    sortInds = np.argsort(xWallPoints)

    return xWallPoints[sortInds], yWallPoints[sortInds],  zWallPoints[sortInds]


#================================================================================
#Function to read a NASA data file with various defined zones.

def readNasaZoneFile(file):
    '''Function to read a NASA data file where potentially multiple zones are
    defined. A dictionary is returned with these zone(s) as keys. If there is
    only one zone that is not specifically named in the file, the returned
    dictionary will have a single key named 'zone'. In the returned dictionary,
    the value corresponding to each zone is another dictionary. This nested
    dictionary will have each variable in the file as a key and the associated
    values in an array as the corresponding value.

    Inputs:
    file : Location of the NASA data file

    Outputs:
    zoneDict : Dictionary with the zone(s) as keys and a nested dictionary
               as values. This nested dictionary has the defined variables as
               keys and arrays as corresponding values.'''
    
    #Load the file contents into a string    
    with open(file) as f:
        data = f.read()

    #Convert the data string to lowercase
    dataLower = data.lower()

    #----------------------------------------------------------------------------
    #Find the variables defined in the header of the NASA file. Sometimes they
    #are on a single line, sometimes spread over multiple lines, both should be
    #read in correctly.

    #Find the starting index of the variable definition by finding the index
    #of the first instance of the word variables in the file.
    variableLineStartInd = dataLower.find('variables')

    #Find the last index of the variable definition. This is done by finding the
    #first instance of '=' after the '=' after variables. Then, the index of the
    #closest instance of '\n' is found before this next '='. This '\n' is
    #assumed to be the end of the variable definition.
    variableLineEndInd = dataLower.rfind('\n', variableLineStartInd,
                            dataLower.find('=', dataLower.find('=',
                                                    variableLineStartInd)+1))

    #Extract the assumed part where the variables are defined as a string
    variableLine = data[variableLineStartInd:variableLineEndInd]

    #Variables are defined between ". The string with variables is split on " and
    #everything between " is assumed to be a variable.
    variables = variableLine.split('"')[1::2]

    #----------------------------------------------------------------------------
    #Extracting zone names and the starting and stopping indices of zone data.

    #Initialize list of zone names
    zones = []

    #Boolean that is set to true when a new zone is identified: this then tells
    #the code to start looking for the index where the zone data starts.
    findDataStart = False

    #Initialize list of indices where the zone data starts, each entry
    #corresponds to a zone in the zones list.
    dataStartInds = []

    #Initialize list of indices indicating where each zone starts, meaning the
    #data of the previous zone has stopped.
    zoneInds = []

    #If there is only one zone in the file, it is not specifically mentioned
    #Hotfix: add the zeroth line as the zone line and add 'zone' as the key

    #Sometimes when there is only one zone, this zone is not specifically named.
    #However, a zone definition line is needed for the data extraction later on.
    #Thus, a zone is created with the name 'zone', it is pretended that this zone
    #is defined at index 0 such that the code correctly starts looking for the
    #data start after this.
    if 'zone' not in dataLower:
        zones.append('zone')
        zoneInds.append(0)
        findDataStart = True

    #Loop over each data line
    for i, (line, lowerLine) in enumerate(zip(data.split('\n'),
                                              dataLower.split('\n'))):

        #If a zone is defined in the line, add its name to zones. Add the line
        #index to zoneInds. Also set findDataStart to true such that the code
        #starts looking for the first line of data.
        if 'zone t=' in lowerLine or 'zone, t=' in lowerLine:
            zones.append(line.split('"')[1])
            zoneInds.append(i)
            findDataStart = True

        #If findDataStart is True, the code should look for the first data line.
        #This is done by checking if there is text in the line. If a line
        #without text is found, this is assumed to be the first data line.
        #In that case, findDataStart is set to false again and the index of
        #The data line is appended to dataStartInds.
        if findDataStart:
            if not textInLine(line):
                dataStartInds.append(i)
                findDataStart = False

    #The index of a non-existent extra line is appended to the zoneInds list.
    #This is such that for the last defined zone, the code knows where to stop
    #(this will be the last line of the file).
    zoneInds.append(i+1)

    #Initialize the zoneDict, which is the dictionary to be returned.
    zoneDict = {}

    #Loop over each zone found in the file
    for i, zone in enumerate(zones):

        #Load the data lines of the current zone into a buffer
        Buff = np.genfromtxt(file, skip_header=dataStartInds[i],
                             max_rows=zoneInds[i+1] - dataStartInds[i])

        #Create a dictionary object from the buffer, with the variables as keys
        #and the buffer data column as values (1D arrays). Add this dictionary
        #to the zoneDict, with the current zone name as the key.
        zoneDict[zone] = dict([(variables[j], Buff[:,j])\
                               for j in range(len(variables))])
                

    return zoneDict

#================================================================================
#Function to find the latest time directory in a certain OpenFOAM case

def findLatestTimeDir(case):
    '''Function to find the latest time directory of an OpenFOAM case.

    Input:
    case : path to the OpenFOAM case of which to find the latest time directory.

    Output:
    maxTimeDir : full path to the latest time directory in case'''

    #Obtain a list of all directories in the case
    dirs = glob.glob(case + '/*/')

    #Initialize the maximum time at -1, this is updated if a later time value
    #is found.
    maxTime = -1

    #Loop over each directory in the case
    for d in dirs:

        #Obtain the directory name (d is the full path)
        dirName = d[:-1].split('/')[-1]

        #If the directory can be converted to a float (it is a number), this
        #number is stored in t and the rest of the code is executed. If not,
        #the code goes to the next directory.
        try:
            t = float(dirName)
        except:
            continue

        #If the time directory is at a later time than the latest time extracted
        #so far, the maxTime and maxTimeDir are updated to the current directory.
        if t > maxTime:
            maxTimeDir = d
            maxTime = t

    #If maxTime is still at its initialized value, there were no time directories
    #in the case. In this case an error is raised.
    if maxTime == -1:
        raise Exception(f"No time directories found in {case}")

    return maxTimeDir


#================================================================================
#Function to read a postProcessing directory

def readSingleGraphDir(singleGraphDir):
    '''Function to read a post-processing directory containing data in .xy or
    .raw files. Returns a dictionary with the variables as keys and data arrays
    as corresponding values. Always only reads the data at the latest available
    time.

    Input:
    singleGraphDir : directory of the post-processing function
                     (e.g. singleGraph_x0.65c).

    Output:
    varDict : Dictionary holding the data at the latest available time. The keys
              are the read in variables and the corresponding values are data
              arrays.'''

    #Find the latest available time directory
    latestTimeDir = findLatestTimeDir(singleGraphDir)

    #Initialize the return dictionary
    varDict = {}

    #Loop over all .xy and raw files in this latest time directory. The
    #readxyOrRawFile function takes the file as an argument and returns a
    #dictionary with the variables as keys and arrays as corresponding values.
    #This dictionary is generated for each file and added to varDict.
    for file in glob.glob(f'{latestTimeDir}/*.xy'):
        varDict = {**readxyOrRawFile(file), **varDict}
    for file in glob.glob(f'{latestTimeDir}/*.raw'):
        varDict = {**readxyOrRawFile(file), **varDict}    

    return varDict
        

#================================================================================
#Function to read a .xy or .raw file

def readxyOrRawFile(file):
    '''Function to read a .xy or .raw file. Also extracts the variable names from
    the name of the file. Returns a dictionary with these variable names as keys
    and data arrays as corresponding values.

    Input:
    file : The .xy or .raw file to be read in. The first word is ignored,
           but after the first _ in the name, the variables are extracted, which
           should be separated by _.

    Output:
    varDict : Dictionary with the variable names as keys and read in data arrays
              as corresponding values.'''


    #Use numpy's genfromtxt function to extract the file contents into a single
    #array, which is stored in the Buff variable.
    Buff = np.genfromtxt(file)

    #Make sure Buff is a 2D array, even if there is only one line (in this case
    #genfromtxt returns a 1D array).
    Buff = Buff.reshape((-1, Buff.shape[-1]))

    #The first three columns correspond to x, y and z, but these are never in the
    #files name. Thus, the variables list is initialized with these already in it.    
    variables = ['x', 'y', 'z']

    #Extract the variables from the file name by splitting on _ and excluding the
    #first word as this is not a variable (this is usually something like line).
    if '.xy' in file:
        fileVars = file.split('/')[-1].replace('.xy', '').split('_')[1:]
    elif '.raw' in file:
        fileVars = file.split('/')[-1].replace('.raw', '').split('_')[:-1]


    #Loop over each variable extracted from the file name
    for var in fileVars:

        #As it is impossible to tell how many components a certain variable has
        #and what variable name is suitable for each component, this information
        #is hardcoded in the current function (only for non-scalars).
        if var == 'U':
            nComps = 3
            variables.append('Ux')
            variables.append('Uy')
            variables.append('Uz')
        elif var == 'wallShearStress':
            nComps = 3
            variables.append('wallShearStressx')
            variables.append('wallShearStressy')
            variables.append('wallShearStressz')
        elif var == 'Pk':
            nComps = 1
            variables.append('Pk')
            
        elif var == 'nut':
            nComps = 1
            variables.append('nut')
        elif var == 'Pkprop':
            nComps = 1
            variables.append('Pkprop')
        elif var == 'gradU':
            nComps = 9
            variables.append('dUx/dx')
            variables.append('dUx/dy')
            variables.append('dUx/dz')
            variables.append('dUy/dx')
            variables.append('dUy/dy')
            variables.append('dUy/dz')
            variables.append('dUz/dx')
            variables.append('dUz/dy')
            variables.append('dUz/dz')
        elif var == 'bijDelta':
            nComps = 6
            variables.append('b11Delta')
            variables.append('b12Delta')
            variables.append('b13Delta')
            variables.append('b22Delta')
            variables.append('b23Delta')
            variables.append('b33Delta')
        elif var == 'tauij':
            nComps = 6
            variables.append('tau11')
            variables.append('tau12')
            variables.append('tau13')
            variables.append('tau22')
            variables.append('tau23')
            variables.append('tau33')

        #If a variable is called LES, it is not actually a variable. Rather,
        #some frozen variables have the _LES extension (e.g. U_LES). In the
        #splitting of the variable name on _, the LES part got separated from
        #the variable. Thus, it is attached again by adding _LES to the last
        #nComps variables. 
        elif var == 'LES':
            for i in range(1, nComps+1):
                variables[-i] += '_LES'

        #If a variable is not defined above and is also not LES, it is assumed to
        #be a simple scalar variable (e.g. omega).
        else:

            #Scalar so one component
            nComps = 1
            
            variables.append(var)

    #Check whether the number of variables indeed corresponds to the number of
    #columns read in from the file. If not, it is likely that a non-scalar
    #variable is present in the file name that is not defined above. In this
    #case an error is raised warning the user of this fact.
    if Buff.shape[-1] != len(variables):
        raise Exception('One or more non-scalar variables are present in ' +\
                        f'{file}, but not defined in the readxyOrRawFile ' +\
                        'function. Please add them to this function')

    #Create the dictionary with the variables as keys and the buffer columns as
    #corresponding values (1D arrays).
    varDict = dict([(variables[j], Buff[:,j]) for j in range(len(variables))])

    return varDict

