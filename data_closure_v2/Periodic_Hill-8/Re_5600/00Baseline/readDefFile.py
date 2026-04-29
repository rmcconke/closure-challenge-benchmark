def readDefFile(defFile):
    '''Function to read variables and their assigned values from an OpenFOAM
    style definition file. Lines must be formatted:
        variable   value; //comment
    No multi-line variable assignments supported (yet).

    Inputs:
    defFile : File from which to read the variables

    Outputs:
    defDict : Dictionary holding variables as keys and their assigned values as
              values.'''

    #Initialize dictionary holding variables as keys and their assigned values
    #as values.
    defDict = {}

    #Reading file contents into a string
    with open(defFile) as f:
        F = f.read()

    #Split into lines and filter out empty lines
    lines = list(filter(None, F.split('\n')))

    #Remove comments from lines; put all lines together in one string,
    #keep linebreaks.
    strippedLines = ''
    for rawLine in lines:
        strippedLines += rawLine.split('//')[0] + '\n'

    #Replace tabs and linebreaks with spaces
    spaceOnlyLines = strippedLines.replace('\t', ' ').replace('\n', ' ')

    #Split the long string at the ; into a list of supposed variables
    splitVars = list(filter(None, spaceOnlyLines.split(';')))

    #Strip any leading and trailing spaces in these variables.
    #Also remove any strings that are empty after these removals.
    strippedVars = list(filter(None, [var.lstrip().rstrip() for var in splitVars]))

    #Split the variable on the space and remove any empty strings in the list
    #which occur when there are multiple spaces between the variable and the
    #value. The first entry from the split is presumed to be the variable,
    #while the rest is presumed to be the value. This can be also a list.
    for strippedVar in strippedVars:
        varValue = list(filter(None, strippedVar.split(' ')))
        var, value = varValue[0], varValue[1:]

        #Try to convert the value to a float and add it to the dict.
        #If this is not possible, simply add the string/list to the list.
        try:
            defDict[var] = float(value[0])
        except:
            defDict[var] = value

    #After looping over each line, return the variable, value dict.
    return defDict

