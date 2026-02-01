#!/usr/bin/env python3
"""
extract_hydrogens.py - Extract hydrogen atoms from trajectory for QENS analysis

QENS is dominated by incoherent scattering from hydrogen atoms due to their
large incoherent scattering cross-section (80.27 barns vs ~5 barns for other atoms).

Usage:
    python extract_hydrogens.py <trajectory.xtc> --tpr <topology.tpr> [options]

Examples:
    python extract_hydrogens.py prod.xtc --tpr prod.tpr
    python extract_hydrogens.py prod.xtc --tpr prod.tpr --output prod_H.xtc
    python extract_hydrogens.py prod.xtc --tpr prod.tpr --solute-only
"""

import subprocess
import argparse
import os
import sys
import tempfile

def create_hydrogen_index(tpr_file, output_ndx, solute_only=False, water_only=False):
    """Create index file with hydrogen selections."""
    selections = []
    
    if solute_only:
        # Only non-water hydrogens
        selections.append(('H_solute', 'name "H*" and not resname SOL TIP3 TIP4 HOH WAT'))
    elif water_only:
        # Only water hydrogens
        selections.append(('H_water', 'name "H*" and resname SOL TIP3 TIP4 HOH WAT'))
    else:
        # All hydrogens
        selections.append(('H_all', 'name "H*"'))
        # Also create separated groups
        selections.append(('H_solute', 'name "H*" and not resname SOL TIP3 TIP4 HOH WAT'))
        selections.append(('H_water', 'name "H*" and resname SOL TIP3 TIP4 HOH WAT'))
    
    # Write selection file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sel', delete=False) as f:
        for name, sel in selections:
            f.write(f'"{name}" {sel};\n')
        sel_file = f.name
    
    # Run gmx select
    cmd = ['gmx', 'select', '-s', tpr_file, '-on', output_ndx, '-sf', sel_file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    os.unlink(sel_file)
    
    if result.returncode != 0:
        print(f"Warning: gmx select failed: {result.stderr}")
        return False
    
    return True

def create_hydrogen_index_make_ndx(tpr_file, output_ndx):
    """Create hydrogen index using gmx make_ndx (fallback method)."""
    cmd = ['gmx', 'make_ndx', '-f', tpr_file, '-o', output_ndx]
    
    # Select all hydrogens
    input_text = "a H*\nname 0 Hydrogen\nq\n"
    
    result = subprocess.run(cmd, input=input_text, capture_output=True, text=True)
    return result.returncode == 0

def extract_trajectory(input_xtc, tpr_file, ndx_file, group_name, output_xtc):
    """Extract atoms from trajectory using index group."""
    cmd = ['gmx', 'trjconv', '-f', input_xtc, '-s', tpr_file, '-n', ndx_file, '-o', output_xtc]
    
    result = subprocess.run(cmd, input=f'{group_name}\n', capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    return True

def get_trajectory_info(xtc_file):
    """Get trajectory information."""
    cmd = ['gmx', 'check', '-f', xtc_file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    output = result.stderr + result.stdout
    info = {}
    
    for line in output.split('\n'):
        if 'Last frame' in line:
            parts = line.split()
            for i, p in enumerate(parts):
                if p == 'time':
                    info['last_time'] = float(parts[i+1])
        if 'Coords' in line:
            parts = line.split()
            info['n_atoms'] = int(parts[1])
    
    return info

def main():
    parser = argparse.ArgumentParser(
        description='Extract hydrogen atoms from trajectory for QENS analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s prod.xtc --tpr prod.tpr
  %(prog)s prod_center.xtc --tpr prod.tpr --output H_only.xtc
  %(prog)s prod.xtc --tpr prod.tpr --solute-only --output H_solute.xtc
        '''
    )
    
    parser.add_argument('trajectory', help='Input trajectory file (.xtc)')
    parser.add_argument('--tpr', '-s', required=True, help='TPR topology file')
    parser.add_argument('--output', '-o', help='Output trajectory file (default: <input>_hydrogen.xtc)')
    parser.add_argument('--solute-only', action='store_true',
                        help='Extract only solute (non-water) hydrogens')
    parser.add_argument('--water-only', action='store_true',
                        help='Extract only water hydrogens')
    parser.add_argument('--keep-ndx', action='store_true',
                        help='Keep the index file after extraction')
    
    args = parser.parse_args()
    
    # Validate input
    if not os.path.exists(args.trajectory):
        print(f"Error: Trajectory not found: {args.trajectory}")
        sys.exit(1)
    
    if not os.path.exists(args.tpr):
        print(f"Error: TPR file not found: {args.tpr}")
        sys.exit(1)
    
    if args.solute_only and args.water_only:
        print("Error: Cannot use both --solute-only and --water-only")
        sys.exit(1)
    
    # Set output filename
    if args.output:
        output_xtc = args.output
    else:
        base = os.path.splitext(args.trajectory)[0]
        suffix = '_H_solute' if args.solute_only else ('_H_water' if args.water_only else '_hydrogen')
        output_xtc = f"{base}{suffix}.xtc"
    
    # Create index file
    ndx_file = 'hydrogen_extract.ndx'
    print(f"Input trajectory: {args.trajectory}")
    print(f"Creating hydrogen index...")
    
    if not create_hydrogen_index(args.tpr, ndx_file, args.solute_only, args.water_only):
        print("Falling back to make_ndx method...")
        if not create_hydrogen_index_make_ndx(args.tpr, ndx_file):
            print("Error: Could not create hydrogen index")
            sys.exit(1)
    
    # Determine group name
    if args.solute_only:
        group_name = 'H_solute'
    elif args.water_only:
        group_name = 'H_water'
    else:
        group_name = 'H_all'
    
    # Try with specific group, fall back to index 0
    print(f"Extracting hydrogens ({group_name})...")
    
    # For make_ndx fallback, group is at index 0 named "Hydrogen"
    success = extract_trajectory(args.trajectory, args.tpr, ndx_file, group_name, output_xtc)
    
    if not success:
        # Try with "Hydrogen" (make_ndx naming)
        success = extract_trajectory(args.trajectory, args.tpr, ndx_file, 'Hydrogen', output_xtc)
    
    if not success:
        # Try with index 0
        success = extract_trajectory(args.trajectory, args.tpr, ndx_file, '0', output_xtc)
    
    if success and os.path.exists(output_xtc):
        # Get info about output
        info = get_trajectory_info(output_xtc)
        orig_info = get_trajectory_info(args.trajectory)
        
        print(f"\nOutput: {output_xtc}")
        print(f"  Atoms: {info.get('n_atoms', 'N/A')} (from {orig_info.get('n_atoms', 'N/A')})")
        print(f"  Duration: {info.get('last_time', 'N/A')} ps")
        
        # File size
        size_bytes = os.path.getsize(output_xtc)
        size_mb = size_bytes / (1024 * 1024)
        orig_size = os.path.getsize(args.trajectory) / (1024 * 1024)
        print(f"  Size: {size_mb:.1f} MB ({size_mb/orig_size*100:.1f}% of original)")
    else:
        print("Error: Extraction failed")
        sys.exit(1)
    
    # Cleanup
    if not args.keep_ndx and os.path.exists(ndx_file):
        os.unlink(ndx_file)
    
    print("\nDone!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
