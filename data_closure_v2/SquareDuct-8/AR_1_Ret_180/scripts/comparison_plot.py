import pyvista as pv
import os, glob
from readDefFile import readDefFile
import numpy as np
from scipy.interpolate import griddata
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib
import subprocess
from matplotlib.gridspec import GridSpec
from matplotlib.ticker import FuncFormatter
def foamToVTK(working_directory):
    subprocess.run('foamToVTK', cwd=working_directory)
    
def contourf_no_lines(*args, **kwargs):
    '''Function to plot both the filled contours and the contour lines.
    The contour lines are plotted to prevent white stripes in between contours,
    such that the outputted images are smooth.

    Inputs:
    Same inputs as the plt.contourf() function.

    Outputs:
    The contourf object'''

    #First plot the contour lines, then fill between them
    plt.contour(*args, **kwargs)
    im = plt.contourf(*args, **kwargs)
    return im

def nice_ticks(cbar, nbins, decimals):
    cbar.locator = ticker.MaxNLocator(nbins=nbins)  # Use a maximum of 5 bins for ticks
    cbar.update_ticks()
    # Format tick labels to have 2 decimal places
    # cbar.formatter = ticker.FuncFormatter(lambda x, _: f"{x:.{decimals}f}")
    cbar.update_ticks()
    return cbar

def plot_contour_comparison(var):
    # var = 'k'
    # matplotlib.rcParams['font.family'] = 'Times New Roman'
    #Set contour plot font size to 12
    # matplotlib.rcParams.update({'font.size' : 8})
    ARVertPlotThreshold = 2
    
    defDict = readDefFile('../caseDef')
    
    h = defDict['h'] #Half channel height
    Re_b = defDict['Re_b'] #Bulk Reynolds number
    Re_tau = defDict['Re_tau'] #Friction Reynolds number
    nu = defDict['nu'] #Kinematic viscosity
    AR = defDict['AR'] #Duct aspect ratio
    U_b = Re_b*nu/h
    figsizeDict = {1 : (5.148, 3.3),
                    3 : (10, 3.5),
                    5 : (8.5, 3.5)}
    
    if not os.path.exists('../02Propagation/beta11/VTK'):
        foamToVTK('../02Propagation/beta11')
    if not os.path.exists('../01Frozen/beta11/VTK'):
        foamToVTK('../01Frozen/beta11')
    if not os.path.exists('../00Baseline/beta11/VTK'):
        foamToVTK('../00Baseline/beta11')
        
    vtk_files = ['../00Baseline/beta11/VTK/beta11_*.vtk', '../02Propagation/beta11/VTK/beta11_*.vtk', '../01Frozen/beta11/VTK/beta11_*.vtk']
    baeline_vtks = glob.glob(vtk_files[0])
    if not baeline_vtks:
        raise ValueError (f"No VTK files found in {vtk_files[0]}.")
    else: 
        baseline_max_file = max(baeline_vtks, key=lambda x: int(os.path.splitext(os.path.basename(x))[0].split('_')[-1]))
    propagation_vtks = glob.glob(vtk_files[1]) 
    if not propagation_vtks:
        raise ValueError (f"No VTK files found in {vtk_files[2]}.")
    else:
        propagation_max_file = max(propagation_vtks, key=lambda x: int(os.path.splitext(os.path.basename(x))[0].split('_')[-1]))
    dns_vtks = glob.glob(vtk_files[2])
    if not dns_vtks:
        raise ValueError (f"No VTK files found in {vtk_files[2]}.")
    else: 
        dns_max_file = max(dns_vtks, key=lambda x: int(os.path.splitext(os.path.basename(x))[0].split('_')[-1]))
        
    # Read the VTK files
    baseline_vtk_path = baseline_max_file
    propagation_vtk_path = propagation_max_file
    dns_vtk_path = dns_max_file
    
    baseline_mesh = pv.read(baseline_vtk_path)
    propagation_mesh = pv.read(propagation_vtk_path)
    dns_mesh = pv.read(dns_vtk_path)
    
    # Slice the datasets at a specific x-value if required
    # If you already know the x-value you can specify it directly
    x_value = baseline_mesh.center[0]  # Replace this with your desired x-value
    baseline_slice = baseline_mesh.slice(normal='x', origin=(x_value, 0, 0))
    propagation_slice = propagation_mesh.slice(normal='x', origin=(x_value, 0, 0))
    dns_slice = dns_mesh.slice(normal='x', origin=(x_value, 0, 0))
    
    # Extract the 'k' field assuming it's stored as point data
    # This will give you a 1D array of 'k' values from the slice
    # baseline_k = baseline_slice.point_data['k']
    # dns_k = dns_slice.point_data['k_LES']
    
    # Define your structured grid bounds and resolution
    # These bounds should cover the spatial extent of your PolyData points
    # The resolution (nx, ny) can be chosen based on the desired fineness of the grid
    xmin, xmax, ymin, ymax = baseline_slice.bounds[2], baseline_slice.bounds[3], baseline_slice.bounds[4], baseline_slice.bounds[5]
    nx, ny = 1024, 1024  # Example resolution, adjust to your needs
    
    # Create a grid of points (structured)
    grid_x, grid_y = np.meshgrid(np.linspace(xmin, xmax, nx), np.linspace(ymin, ymax, ny))
    
    # Flatten the grid for the interpolation function
    grid_points = np.c_[grid_x.ravel(), grid_y.ravel()]
    # # Interpolate using griddata. This assumes 'k' is available in point_data
    # baseline_values = griddata(baseline_slice.points[:, 1:], baseline_slice.point_data[var], grid_points, method='linear')
    # dns_values = griddata(dns_slice.points[:, 1:], dns_slice.point_data[var+'_LES'], grid_points, method='linear')
    
    # Reshape the interpolated data to have the same structure as the grid
    if var == 'k':
        baseline_values = griddata(baseline_slice.points[:, 1:], baseline_slice.point_data[var], grid_points, method='linear')
        propagation_values = griddata(propagation_slice.points[:, 1:], propagation_slice.point_data[var], grid_points, method='linear')
        dns_values = griddata(dns_slice.points[:, 1:], dns_slice.point_data[var+'_LES'], grid_points, method='linear')
        baseline_reshaped = baseline_values.reshape(grid_x.shape)/U_b**2
        propagation_reshaped = propagation_values.reshape(grid_x.shape)/U_b**2
        dns_reshaped = dns_values.reshape(grid_x.shape)/U_b**2
        label = r'$k$/$U_b^2$'
    # elif var == 'U_x':
    #     baseline_values = griddata(baseline_slice.points[:, 1:], baseline_slice.point_data['U'][:,0], grid_points, method='linear')
    #     dns_values = griddata(dns_slice.points[:, 1:], dns_slice.point_data['U_LES'][:,0], grid_points, method='linear')
    #     baseline_reshaped = baseline_values.reshape(grid_x.shape)/U_b
    #     dns_reshaped = dns_values.reshape(grid_x.shape)/U_b
    #     label = r'$U_x$/$U_b$' 
    elif var == 'vortex':
        baseline_values = griddata(baseline_slice.points[:, 1:], np.sqrt(baseline_slice.point_data['U'][:,1]**2+baseline_slice.point_data['U'][:,2]**2), grid_points, method='linear')
        U_y_b = griddata(baseline_slice.points[:, 1:], baseline_slice.point_data['U'][:,1], grid_points, method='linear')
        U_z_b = griddata(baseline_slice.points[:, 1:], baseline_slice.point_data['U'][:,2], grid_points, method='linear')
        U_y_b_reshaped = U_y_b.reshape(grid_x.shape)
        U_z_b_reshaped = U_z_b.reshape(grid_x.shape)
        
        propagation_values = griddata(propagation_slice.points[:, 1:], np.sqrt(propagation_slice.point_data['U'][:,1]**2+propagation_slice.point_data['U'][:,2]**2), grid_points, method='linear')
        U_y_p = griddata(propagation_slice.points[:, 1:], propagation_slice.point_data['U'][:,1], grid_points, method='linear')
        U_z_p = griddata(propagation_slice.points[:, 1:], propagation_slice.point_data['U'][:,2], grid_points, method='linear')
        U_y_p_reshaped = U_y_p.reshape(grid_x.shape)
        U_z_p_reshaped = U_z_p.reshape(grid_x.shape)
        
        dns_values = griddata(dns_slice.points[:, 1:], np.sqrt(dns_slice.point_data['U_LES'][:,1]**2+dns_slice.point_data['U_LES'][:,2]**2), grid_points, method='linear')
        U_y = griddata(dns_slice.points[:, 1:], dns_slice.point_data['U_LES'][:,1], grid_points, method='linear')
        U_z = griddata(dns_slice.points[:, 1:], dns_slice.point_data['U_LES'][:,2], grid_points, method='linear')
        U_y_reshaped = U_y.reshape(grid_x.shape)
        U_z_reshaped = U_z.reshape(grid_x.shape)
        baseline_reshaped = baseline_values.reshape(grid_x.shape)/U_b
        propagation_reshaped = propagation_values.reshape(grid_x.shape)/U_b
        dns_reshaped = dns_values.reshape(grid_x.shape)/U_b
        label = r'$\sqrt{\left(U_y^2+U_z^2\right)}/U_b$'
    else:
        raise KeyError(f"{var} is not a valid key.")
    
    min_ = min(np.min(baseline_reshaped), np.min(dns_reshaped))
    max_ = max(np.max(baseline_reshaped), np.max(dns_reshaped))
    
    # Calculate common levels for contour plots
    levels = np.linspace(min_, max_, num=48)
    # Plot Baseline contour
    fig = plt.figure(figsize=figsizeDict[AR])
    #Low aspect ratio cases are plotted side by side.
    # if AR < ARVertPlotThreshold:
    #     plt.subplot(121)
    # else:
    #     plt.subplot(211)
    
    # contourf_no_lines(grid_x, grid_y, baseline_reshaped, levels=levels, cmap='viridis')
    # plt.title('Baseline')
    # plt.gca().set_aspect('equal')
    # plt.axis('off')
    # # Plot DNS contour
    # if AR < ARVertPlotThreshold:
    #     plt.subplot(122)
    # else:
    #     plt.subplot(212)
        
    
    # im = contourf_no_lines(grid_x, grid_y, dns_reshaped, levels=levels, cmap='viridis')
    # if var == 'vortex':
    #     plt.streamplot(grid_x, grid_y, U_y_reshaped, U_z_reshaped, color='white', linewidth=0.5)
    
    # plt.title('DNS')
    # plt.gca().set_aspect('equal')
    # plt.axis('off')
    
    # # Create a shared colorbar
    # plt.tight_layout()
    # # plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1, wspace=0.2, hspace=0.3)
    # plt.subplots_adjust(right=0.8)
    # cbar_ax = fig.add_axes([0.83, 0.15, 0.05, 0.7])
    # cbar = plt.colorbar(im, cax=cbar_ax)
    # cbar = nice_ticks(cbar, nbins=10, decimals=4)
    # cbar.set_label(label)
    
    # fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsizeDict[AR])
                                    # gridspec_kw={"width_ratios":[1,1,0.2]})
    gs = GridSpec(1, 3, width_ratios=[1, 1, 1], figure=fig)
    
    # Create and plot the first subplot
    ax1 = fig.add_subplot(gs[0])
    ax1.set_position([0.01, 0.1, 0.32, 0.8])  # [left, bottom, width, height] for ax1
    ax1.set_title('Baseline', pad=3)
    ax1.contour(grid_x, grid_y, baseline_reshaped, levels=levels, cmap='viridis')
    ax1.contourf(grid_x, grid_y, baseline_reshaped, levels=levels, cmap='viridis')
    ax1.set_aspect('equal', adjustable='box')
    ax1.set_xlim([xmin, xmax])
    ax1.set_ylim([ymin, ymax])
    ax1.axis('off')
    
    # Create and plot the second subplot
    ax2 = fig.add_subplot(gs[1])
    ax2.set_position([0.34, 0.1, 0.32, 0.8])  # Adjust left and width for ax2 to bring it closer to ax1
    # ax2.set_title(r'ModelPropagation ($b_{ij}^\Delta$)', pad=5)
    ax2.set_title('Propagation', pad=3)
    ax2.contour(grid_x, grid_y, propagation_reshaped, levels=levels, cmap='viridis', extend='max')
    im = ax2.contourf(grid_x, grid_y, propagation_reshaped, levels=levels, cmap='viridis', extend='max')
    ax2.set_aspect('equal', adjustable='box')
    ax2.set_xlim([xmin, xmax])
    ax2.set_ylim([ymin, ymax])
    ax2.axis('off')
    
    if var == 'vortex':
          ax2.streamplot(grid_x, grid_y, U_y_p_reshaped, U_z_p_reshaped, color='white', linewidth=0.3)
    
          
    # Create and plot the third subplot
    ax3 = fig.add_subplot(gs[2])
    ax3.set_position([0.67, 0.1, 0.32, 0.8])  # Adjust left and width for ax2 to bring it closer to ax1
    ax3.set_title('DNS', pad=3)
    ax3.contour(grid_x, grid_y, dns_reshaped, levels=levels, cmap='viridis')
    im = ax3.contourf(grid_x, grid_y, dns_reshaped, levels=levels, cmap='viridis')
    ax3.set_aspect('equal', adjustable='box')
    ax3.set_xlim([xmin, xmax])
    ax3.set_ylim([ymin, ymax])
    ax3.axis('off')
    
    if var == 'vortex':
          ax3.streamplot(grid_x, grid_y, U_y_reshaped, U_z_reshaped, color='white', linewidth=0.3)
    
    
    
    # cbar_ax = fig.add_subplot(gs[3])
    # cbar_ax.set_position([0.89, 0.1, 0.02, 0.8])
    # cbar_ax.axis('off')
    # plt.subplots_adjust(left=0.05, right=0.8, bottom=0.05, top=0.9)
    # plt.subplots_adjust(left=0.03)
    # cbar_ax = fig.add_axes([0.9, 0.15, 0.03, 0.7])
    cbar = fig.colorbar(im, ax=[ax1, ax2, ax3], 
                        location='top', 
                        orientation='horizontal', 
                        shrink=0.90, 
                        aspect=50,
                        pad=0.13)
    # cbar = fig.colorbar(im, cax=cbar_ax)
    
    def custom_formatter(x, pos):
        if x == 0:
            return '0'
        else:
            return f'{x:.3f}'
    cbar = nice_ticks(cbar, nbins=8, decimals=4)
    cbar.ax.xaxis.set_major_formatter(FuncFormatter(custom_formatter))
    
    
    
    cbar.set_label(label, labelpad=5)
    cbar.ax.xaxis.set_ticks_position('bottom')
    cbar.ax.tick_params(axis='x', which='major', pad=1)
    # plt.tight_layout()
    
    
    
    # Display the plot
    if not os.path.exists("../Figures"):
        os.makedirs("../Figures")
    # plt.savefig(f'../Figures/compare{var}Contours_Propagation.jpg')#, bbox_inches='tight')
    plt.savefig(f'../Figures/compare{var}Contours_Propagation.png', dpi=150, bbox_inches='tight', format='png', pad_inches=0.01)
    plt.show()
    plt.close()

if __name__=='__main__':
    vars = ['k', 'vortex']
    for var in vars:
        plot_contour_comparison(var)