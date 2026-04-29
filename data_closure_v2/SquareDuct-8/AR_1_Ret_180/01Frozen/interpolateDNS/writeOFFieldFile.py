'''Script to write a numpy array to a field file that can be imported in OpenFOAM
using the #include function. Call the writeOFFieldFile function to write a
non-uniform field. Call the writeOFUniformFieldFile function to write a uniform
field.

Author : Kaj Hoefnagel'''

#--------------------------------------------------------------------------------
#Libraries to be imported

import numpy as np

#--------------------------------------------------------------------------------
#Main function

def writeOFFieldFile(data, fieldType, fileFullPath):
    '''Function to save a numpy array as a uniform OpenFOAM field file that can
    later be used by OpenFOAM using the #include function. For example, if the
    file U_internalField is saved, it can then be included in the U file as e.g.
    an intitial condition using:
    #include "U_internalField"
    internalField $U_internalField

    Note that the variable name of the field will be equal to the filename.

    Inputs:
    -data : Data to be saved, should be a numpy array
    -fieldType : Type of field that is saved, e.g. scalar, vector, etc...
    -fileFullPath : Full path and filename of the file to be saved.'''

    # Convert to 2D NumPy array
    data = np.atleast_2d(np.asarray(data))

    if data.ndim != 2:
        raise ValueError("Data must be a 2D NumPy array.")

    # Open file for writing
    with open(fileFullPath, 'w') as f:
        fieldName = fileFullPath.split('/')[-1]

        f.write(f'{fieldName} nonuniform List<{fieldType}>\n')
        f.write(f'{len(data)}\n')
        f.write('(\n')

        # Format for scalar or vector entries
        if data.shape[1] == 1:
            writeFormat = '{}\n'
        else:
            writeFormat = '(' + ' '.join(['{:.16g}'] * data.shape[1]) + ')\n'

        for row in data:
            f.write(writeFormat.format(*row))

        f.write(');\n')


def writeOFUniformFieldFile(data, fileFullPath):
    '''Function to save a numpy array as a uniform OpenFOAM field file that can
    later be used by OpenFOAM using the #include function. For example, if the
    file U_internalField is saved, it can then be included in the U file as e.g.
    an intitial condition using:
    #include "U_internalField"
    internalField $U_internalField

    Note that the variable name of the field will be equal to the filename.

    Inputs:
    -data : Data to be saved, should at most be 1D (but 0D A.K.A. int/float
            is also fine).
    -fileFullPath : Full path and filename of the file to be saved.'''
    
    #Create the specified output file, or overwrite it if it already exists
    f = open(fileFullPath, 'w')

    #Write the first part of the line, defining the variable (simply the file
    #name specified in fileFullPath) as well as the uniform keyword.
    f.write(f'{fileFullPath.split("/")[-1]} uniform ')


    #Write the second part of the line, the uniform field. If the size of the
    #data is one, it is a scalar field so the scalar is simply written.
    #If the size of the data is greater than one, it has multiple components
    #(e.g. vector), so brackets are inserted and the components are written
    #between the brackets, separated by spaces.
    if data.size == 1:
        f.write(str(list(data)[0]))
    else:
        f.write('(' + ' '.join(['{}']*data.size).format(*data) + ')')

    #Write required ; at the end and insert a linebreak.
    f.write(';\n')

    #Close the file again
    f.close()    
