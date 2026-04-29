'''Simple script to read in the two LES data files, put them into nested
dictionaries and combine these nested dictionaries. At the higher level, these
dictionaries contain the mesh zone ('Fine Grid' or 'Coarse Grid'). Each zone
contains another dictionary with the flow variables as keys and a 1D array
as the corresponding value.These two dictionaries are combined into one; they
contain the same zones, but different variables. Finally, the result is saved as
a .pickle file so the dictionary can be quickly loaded by other scripts (reading
the .dat files takes rather long).

Author : Kaj Hoefnagel'''

#================================================================================
#Libraries to include

from readExpData import readNasaZoneFile
import pickle

#================================================================================
#Main code function

def readAndPickle(LESPath):
    '''Main function to read in the LES data files, combine their nested
    dictionaries into one and save the result in a pickle file such that it
    can be efficiently loaded by other scripts.

    Input:
    LESPath : Path to the LES data folder containing the LES data files. This
              is also where the pickled dictionary file will be stored.

    Output:
    - : Function has no return value, but instead writes the file
        pickledLESData.pickle in the passed LESPath.'''
    
    #Read in both data files and store them as dictionaries
    zoneDictA = readNasaZoneFile(f'{LESPath}/LES.dat')
    zoneDictB = readNasaZoneFile(f'{LESPath}/VelocityDerivatives.dat')

    #Initialize the combined dictionary
    zoneDictComb = {}

    #Loop over each zone and combine the underlying dictionaries of variables.
    for zone in zoneDictA:
        zoneDictComb[zone] = {**zoneDictA[zone], **zoneDictB[zone]}

    #Save the combined dictionary in pickle format
    with open(f'{LESPath}/pickledLESData.pickle', 'wb') as f:
        pickle.dump(zoneDictComb, f)

#================================================================================
#Execute if this script is run (not if it is included by another script).

if __name__ == "__main__":
    readAndPickle('.')
