#!/usr/bin/env python3
"""Plot profiles - Plot OpenFOAM "simpleGraph" output - usually velocity/k profiles.

Argument[s] "testcases" are paths to one or more OpenFOAM testcase top-level directories.
If no paths are given, the cwd will be used.  Data expected in "postProcessing/simpleGraph*"
sub-paths.

Usage:
  plot_profiles.py [<testcases> ...]

Options:
  -h --help     Show this screen.
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import re
from collections import defaultdict
import docopt
from PyFoam.RunDictionary.ParsedParameterFile import ParsedParameterFile
def read_single_case(path):
    """
    Read (possibly multiple) profiles from a single OpenFOAM case.  Read only the latest
    output, in all variables.  Determine number of profiles, variables, end final time,
    from the filenames.  Return in a dict-of-dicts with the structure:
    
      raw = {'singleGraph_peak': {'Ux': [1.,1.,1.,...], 'p': [.5, ...], ...},
             'singleGraph_2': {'Ux': [1.,1.,1.,...], ...},
             ... }
    
    where the data is in ndarrays.

    Assumptions:
      - Output is in files of the form 
          "postProcessing/singleGraph*/1000/line_*.xy"
        where "1000" is whatever the latest timestep is, and after
        the "line_" the variable names are listed, seperated by "_".
      - All singleGraphs have same most-recent output time.
      - All singleGraphs have the same variables.
      - All singleGraphs have xyz as first 3 variables.

    """
    # This should be the case top-level directory of the OpenFOAM case
    p = Path(path)
    
    # Get all postprocessing output named singleGraph*
    graphs = list(p.glob('postProcessing/singleGraph*'))
    if len(graphs) == 0:
        raise ValueError(f'No "postProcessing/singleGraph"s found in case {path}.')
    
    # Find the most recent output time
    maxtime = max([int(l.name) for l in graphs[0].glob('*')])
    maxtime = f'{maxtime}'  # as string
    print(f'Reading from path "{p.name}" at output iteration = {maxtime}')
    
    # Find the variable names (from the filenames)
    # Some munging necessary for variables with underscores "U_LES", "k_LES", etc.
    # These variables are renamed just "U", "k" in the output of this function.
    # Further munging needed for vectors/tensors: "U" -> "Ux","Uy","Uz", not
    # clear how tensors are formatted (TODO if needed).
    filenames = [l.name for l in (graphs[0] / maxtime).glob('*')]
    variable_namess = []
    for f in filenames:
        vnames = re.search('line_(.*)\.xy', f).group(1).split('_')
        vnames = [l for l in vnames if not l in {'LES'}]
        if vnames[0] in {'U'}:
            variable_namess.append(['x', 'y', 'z'] + ['Ux', 'Uy', 'Uz'])
        else:
            variable_namess.append(['x', 'y', 'z'] + vnames)

    # Finally read all the actual data...
    raw = defaultdict(dict)
    for graph in graphs:
        for filename, variable_names in zip(filenames, variable_namess):
            pdata = np.loadtxt(graph / maxtime / filename)
            if pdata.shape[0] == 0:
                print(f'Empty file: {graph / maxtime / filename}')
            else:
                for i,v in zip(range(pdata.shape[1]), variable_names):
                    raw[graph.name][v] = pdata[:,i]
    bottom = np.array(ParsedParameterFile( p / "constant" / "C")["boundaryField"]["bottomWall"]["value"])
    raw['bottom']['x'] = bottom[:, 0]
    raw['bottom']['y'] = bottom[:, 1]
    top = np.array(ParsedParameterFile( p / "constant" / "C")["boundaryField"]["topWall"]["value"])
    raw['top']['x'] = top[:, 0]
    raw['top']['y'] = top[:, 1]
    return raw

def plot_boundary(axes, data):
    """Plot bottom"""
    for ax in axes:
        ax.plot(data['bottom']['x'], data['bottom']['y'], color='0.8', linewidth=2)
        ax.plot(data['top']['x'], data['top']['y'], color='0.8', linewidth=2)
def plot_grid(axes, data):
    """Draw grid-lines at profile zeros."""
    for ax in axes:
        for name,profile in data.items():
            ax.plot(profile['x'], profile['y'], '--', color='0.8', linewidth=0.5)
    
def plot_single_case(axes, data, name, style):
    label = name
    Ub = 0.72
    for profilename,profile in data.items():
        transforms = ["profile['Ux']*0.5/Ub",
                      "profile['k']*5/(Ub**2)",
                      #"10*profile['PkLES']",
                      #"10*profile['Pk']",
                      #"10*profile['PkBoussinesq']",
                      #"10*profile['PkDelta']",
                      #"profile['kDeficit']",
                      #"profile['p']"]
                      ]
        tnames = ['$\\frac{1}{2}U_x/U_b + x$', '$5k/U_b^2 +x$', 'PkLES', 'Pk', 'PkBoussinesq', 'PkDelta', 'kDeficit', "p"]
        missing_names = set()
        for ax, tname, transform in zip(axes, tnames, transforms):
            try:
                d = eval(transform)
                ax.plot(d+profile['x'], profile['y'], style, label=label)
                ax.set_title(tname)
            except KeyError as e:
                missing_names.add(f'{e}'[1:-1])
        label = '_nolegend_'
    if len(missing_names) > 0:
        print(f'WARNING: In {name} variables {missing_names} were not available.')
            
def plot_all(names, datas, styles):
    """
    Plot all cases, in all variables, across all profiles.
    """
    fig = plt.figure(figsize=(8.27,11.69/2))  # A4 portrait
    axes = fig.subplots(2, 1, sharex=True)
    plot_grid(axes, datas[0])
    plot_boundary(axes, datas[0])
    for name,data,style in zip(names, datas, styles):
        plot_single_case(axes, data, name, style)
    for ax in axes:
        ax.set_xlim(-0.2, 9.2)
        ax.set_ylim(-0.1, 3.2)
        ax.set_aspect('equal', adjustable='box')
        
    #for ax in axes:
    #    ax.set_aspect('equal', 'box')
    axes[0].legend(loc='upper right')
    outfile = "profile.pdf"
    print(f"Writing <{outfile}>")
    plt.tight_layout()
    fig.savefig(outfile)

    
if __name__ == '__main__':

    styles = ['-k', '-r', '--b', ':g', '-.m']
    
    args = docopt.docopt(__doc__, version='v1')
    casepaths = args['<testcases>']
    if len(casepaths) == 0:
        raw = read_single_case('.')
        plot_all([Path('.').absolute().name], [raw], styles)
    else:
        datas = []
        for casepath in casepaths:
            datas.append( read_single_case(casepath) )
        casenames = [Path(p).absolute().name for p in casepaths]
        plot_all(casenames, datas, styles)
        
