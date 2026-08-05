from math import e
import numpy as np
from scipy.interpolate import griddata
data = np.load('scripts/plots_data/ground_truth_extrapolation_full.npz')
from closure_challenge import evaluation_points
from closure_challenge.eval import evaluate_individual_case

test_cases=['alpha_15_13929_4048', 'alpha_15_13929_2024', 'alpha_05_4071_4048', 'alpha_05_4071_2024', 'AR_14_Ret_180']



for case in test_cases:

    if case == 'alpha_15_13929_4048':
        low_U = data['alpha_15_13929_2024/U']
        high_U = data['alpha_15_13929_3036/U']
        deltaU = high_U - low_U
        extrapolated_U = high_U + deltaU 
        print(f"example point: high_U={high_U[0]}, low_U={low_U[0]}, deltaU={deltaU[0]}, extrapolated_U={extrapolated_U[0]}")
        coords = data['alpha_15_13929_4048/coords']
        x_extrapolated = coords[:, 0]
        y_extrapolated = coords[:, 1]
        z_extrapolated = coords[:, 2]
        
    elif case == 'alpha_15_13929_2024':
        low_U = data['alpha_15_13929_3036/U']
        high_U = data['alpha_15_13929_4048/U']
        deltaU = high_U - low_U
        extrapolated_U = low_U - deltaU 
        print(f"example point: high_U={high_U[0]}, low_U={low_U[0]}, deltaU={deltaU[0]}, extrapolated_U={extrapolated_U[0]}")
        coords = data['alpha_15_13929_2024/coords']
        x_extrapolated = coords[:, 0]
        y_extrapolated = coords[:, 1]
        z_extrapolated = coords[:, 2]

    elif case == 'alpha_05_4071_4048':
        low_U = data['alpha_05_4071_2024/U']
        high_U = data['alpha_05_4071_3036/U']
        deltaU = high_U - low_U
        extrapolated_U = high_U + deltaU 
        print(f"example point: high_U={high_U[0]}, low_U={low_U[0]}, deltaU={deltaU[0]}, extrapolated_U={extrapolated_U[0]}")
        coords = data['alpha_05_4071_4048/coords']
        x_extrapolated = coords[:, 0]
        y_extrapolated = coords[:, 1]
        z_extrapolated = coords[:, 2]

    elif case == 'alpha_05_4071_2024':
        low_U = data['alpha_05_4071_3036/U']
        high_U = data['alpha_05_4071_4048/U']
        deltaU = high_U - low_U
        extrapolated_U = low_U - deltaU 
        print(f"example point: high_U={high_U[0]}, low_U={low_U[0]}, deltaU={deltaU[0]}, extrapolated_U={extrapolated_U[0]}")
        coords = data['alpha_05_4071_2024/coords']
        x_extrapolated = coords[:, 0]
        y_extrapolated = coords[:, 1]
        z_extrapolated = coords[:, 2]
        
    elif case == 'AR_14_Ret_180':
        print(f"Processing case: {case}")
    
        coords_low = data['AR_7_Ret_180/coords']
        coords_high = data['AR_10_Ret_180/coords']

        U_low = data['AR_7_Ret_180/U']
        U_high = data['AR_10_Ret_180/U']

        y_low_normalized = coords_low[:, 1] / max(coords_low[:, 1])
        z_low_normalized = coords_low[:, 2] / max(coords_low[:, 2])
        y_high_normalized = coords_high[:, 1] / max(coords_high[:, 1])
        z_high_normalized = coords_high[:, 2] / max(coords_high[:, 2])

        print(f"min(coords_low[:, 1])={min(coords_low[:, 1])}, max(coords_low[:, 1])={max(coords_low[:, 1])}, min(coords_low[:, 2])={min(coords_low[:, 2])}, max(coords_low[:, 2])={max(coords_low[:, 2])}")
        print(f"min(coords_high[:, 1])={min(coords_high[:, 1])}, max(coords_high[:, 1])={max(coords_high[:, 1])}, min(coords_high[:, 2])={min(coords_high[:, 2])}, max(coords_high[:, 2])={max(coords_high[:, 2])}")

        print(f"min(y_low_normalized)={min(y_low_normalized)}, max(y_low_normalized)={max(y_low_normalized)}, min(z_low_normalized)={min(z_low_normalized)}, max(z_low_normalized)={max(z_low_normalized)}")
        print(f"min(y_high_normalized)={min(y_high_normalized)}, max(y_high_normalized)={max(y_high_normalized)}, min(z_high_normalized)={min(z_high_normalized)}, max(z_high_normalized)={max(z_high_normalized)}")
        

        z_interp_normalized = np.linspace(0.05, 0.999, 1000)
        y_interp_normalized = z_interp_normalized 

        Z_interp_normalized, Y_interp_normalized = np.meshgrid(z_interp_normalized, y_interp_normalized)
        z_interp_normalized = Z_interp_normalized.flatten()
        y_interp_normalized = Y_interp_normalized.flatten()

        U_low_interp = griddata((y_low_normalized, z_low_normalized), U_low, (y_interp_normalized, z_interp_normalized), method='linear')
        U_high_interp = griddata((y_high_normalized, z_high_normalized), U_high, (y_interp_normalized, z_interp_normalized), method='linear')

        extrapolated_U = U_high_interp + (U_high_interp - U_low_interp)*4/3

        print(f"example point: U_low_interp={U_low_interp[0]}, U_high_interp={U_high_interp[0]}, U_extrapolated={extrapolated_U[0]}")

        z_extrapolated = z_interp_normalized * 0.01399197224
        y_extrapolated = y_interp_normalized * 0.000999426589
        x_extrapolated = np.ones_like(z_extrapolated) * 0.005


    eval_points = evaluation_points(case)
    print(eval_points.shape)

    interp_U = griddata((x_extrapolated, y_extrapolated, z_extrapolated), extrapolated_U, (eval_points[:, 0], eval_points[:, 1], eval_points[:, 2]), method='nearest')
    print(f"example point: interp_U={interp_U[0]}")
    
    score = evaluate_individual_case(case, interp_U)

    print(f"Case {case} score: {score}")
    
    

