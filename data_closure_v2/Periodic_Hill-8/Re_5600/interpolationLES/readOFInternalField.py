'''Script to extract the internalField array from an OpenFOAM solution file in
an efficient manner. Main function: readOFInternalField.'''

#================================================================================
#Libraries to import

import numpy as np

#================================================================================
#Helper function

def splitString(s):
    '''Function that takes a string as an input and returns a list of substrings,
    splitted on the space.

    Input:
    s : Input string

    Output
    l : list of substrings resulting from splitting s on the spaces'''
    
    return s.split(' ')

def readOFInternalField(file):
    '''Main function that extracts the internalField from an OpenFOAM solution
    file.

    Input:
    file : OpenFOAM solution file (e.g. U) from which the internalField is to be
           extracted.

    Output:
    arr : The internalField of the inputted solution file converted to an array.'''
    
    #Read the lines of the file into a single string
    with open(file) as f:
        lines = f.read()

    #Split the filestring to only retain the characters between internalField
    #and the first following semicolon; this part of the file holds the
    #internalField array.
    fullBuff = lines.split('internalField')[1].split(';')[0]

    #If the internalField is defined as something nonUniform, it is stored as
    #an array.
    if 'nonuniform' in fullBuff:

        #The array starts at the first opening bracket and ends at the last
        #closing bracket. All linebreaks and tabs are replaced by spaces for
        #consistency. Furthermore, multiple consecutive spaces are reduced to
        #single spaces.
        numBuff = ' '.join(fullBuff.split('(', maxsplit=1)[1].rsplit(')', 1)[0].\
                              replace('\n', ' ').replace('\t', ' ').split())

        #If the string buffer still contains brackets, each entry has multiple
        #components.
        if '(' in numBuff:

            #Replace the ') (' entries in the array with '\n', such that a
            #linebreak indicates a new entry. Then delete the leading and
            #trailing bracket.
            arrBuff = numBuff.replace(') (', '\n').replace(')', '').\
                      replace('(', '')

            #Convert the resulting string buffer to a 2D array by first splitting
            #on the linebreaks and splitting the resulting list of strings on
            #spaces. The resulting 2D list of strings is then converted to a 2D
            #array of floats.
            arr = np.array(list(map(splitString, arrBuff.split('\n'))),
                           dtype=np.float64)


        #If the string buffer doesn't contain brackets anymore, each entry
        #is a scalar.
        else:

            #The numBuff string can easily be converted to a list of strings by
            #splitting on the space. This list of strings is the converted to
            #an array of floats.
            arr = np.array(numBuff.split(' '), dtype=np.float64)

        return arr

    #If nonuniform is not in the declaration of internalField, it is assumed to
    #be uniform.
    else:

        #If there is a bracket, the uniform field is a vector/tensor field.
        if '(' in fullBuff:

            #The numbers between the two brackets are extracted, linebreaks
            #and tabs are replaced by spaces, multiple spaces are replaced by
            #a single space.
            numBuff = ' '.join(fullBuff.split('(')[1].split(')')[0].\
                               replace('\n', ' ').replace('\t', ' ').split())

            #The string of numbers is converted to an array by splitting on the
            #space and converting to floats. Also, the array is made 2D.
            arr = np.array(numBuff.split(' '), dtype=np.float64)[None]

        #If there is no bracket, the uniform field is a scalar field.
        else:

            #The scalar is extracted by first replacing each tab and linebreak
            #by a space. Then the string is split on spaces and the last entry
            #is taken and converted to a 2D float array.
            arr = np.array(fullBuff.replace('\t', ' ').replace('\n', ' ').\
                           split(' ')[-1], dtype=np.float64)[None]
        
        return arr

