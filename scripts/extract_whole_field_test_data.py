import numpy as np
from Ofpp import parse_internal_field
import tempfile
import os

test_paths = {'alpha_15_13929_4048': 'data/Parm_PH_29/alpha_15/alpha_15_13929_4048',
'alpha_15_13929_3036': 'data/Parm_PH_29/alpha_15/alpha_15_13929_3036',
              'alpha_15_13929_2024': 'data/Parm_PH_29/alpha_15/alpha_15_13929_2024',
              'alpha_05_4071_4048': 'data/Parm_PH_29/alpha_05/alpha_05_4071_4048',
              'alpha_05_4071_3036': 'data/Parm_PH_29/alpha_05/alpha_05_4071_3036',
              'alpha_05_4071_2024': 'data/Parm_PH_29/alpha_05/alpha_05_4071_2024',
              'AR_7_Ret_180': 'data/DUCT/AR_7_Ret_180',
              'AR_10_Ret_180': 'data/DUCT/AR_10_Ret_180'
              }


def parse_vector_field_manual(filepath, skip_header=0):
    """Parse vector field using numpy for problematic cases
    
    Args:
        filepath: path to the file
        skip_header: number of lines to skip at the beginning
    """
    with open(filepath, 'r') as f:
        lines = f.readlines()[skip_header:]
    
    # Find where the data starts (after the count line)
    start_idx = None
    for i, line in enumerate(lines):
        if line.strip().isdigit():  # This is the count line
            start_idx = i + 2  # Skip count and opening (
            break
    
    if start_idx is None:
        raise ValueError("Could not find data count in file")
    
    # Collect vector lines
    vector_lines = []
    for line in lines[start_idx:]:
        line = line.strip()
        if line == ');' or line == ')':
            break
        if line.startswith('(') and line.endswith(')'):
            # Remove parentheses and add to list
            vector_lines.append(line.strip('()'))
    
    # Write to temporary file for genfromtxt
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
        tmp.write('\n'.join(vector_lines))
        tmp_path = tmp.name
    
    # Parse with numpy
    data = np.genfromtxt(tmp_path, dtype=float)
    
    # Clean up
    os.remove(tmp_path)
    
    return data


def extract_case(case_name, case_path):
    if case_name.startswith('AR_'):
        coords = parse_internal_field(f"{case_path}/constant/C")
        U_LES = parse_vector_field_manual(f"{case_path}/0/U_LES", skip_header=0)
    elif case_name == 'NASA_2DWMH':
        coords = parse_internal_field(f"{case_path}/0/C")
        U_LES = parse_vector_field_manual(f"{case_path}/0/U_LES", skip_header=17)
    else:
        coords = parse_internal_field(f"{case_path}/0/C")
        U_LES = parse_internal_field(f"{case_path}/0/U_LES")
    
    return coords, U_LES


def main():
    all_data = {}
    
    # Fixed random seed for repeatability
    rng = np.random.RandomState(42)
    n_samples = 1000
    
    for case_name, case_path in test_paths.items():
        print(f"Extracting {case_name}...")
        coords, U_LES = extract_case(case_name, case_path)
        
        # Sample the same indices from both arrays
        n_points = coords.shape[0]
        if n_points > n_samples:
            indices = rng.choice(n_points, size=n_samples, replace=False)
            coords_sampled = coords[indices]
            U_LES_sampled = U_LES[indices]
        else:
            coords_sampled = coords
            U_LES_sampled = U_LES
        
        all_data[f'{case_name}/coords'] = coords
        all_data[f'{case_name}/U'] = U_LES
        
        print(f"  Shape: coords={coords.shape}, U={U_LES.shape}")
    
    output_file = 'scripts/plots_data/ground_truth_extrapolation_full.npz'
    np.savez_compressed(output_file, **all_data)
    
    print(f"\nSaved all data to {output_file}")
    
    size_mb = os.path.getsize(output_file) / (1024**2)
    print(f"File size: {size_mb:.2f} MB")
    
    print(f"\nKeys in file:")
    data = np.load(output_file)
    for key in sorted(data.files):
        print(f"  {key}: shape={data[key].shape}")


if __name__ == "__main__":
    main()