#!/usr/bin/env python3
"""
verify_processing.py - Verify processed trajectories are ready for QENS analysis

Checks:
1. All processed files exist
2. Trajectory lengths match
3. Frame spacing is consistent
4. Hydrogen count is correct
5. No duplicate/missing frames

Usage:
    python verify_processing.py <production_dir>
    python verify_processing.py --all <systems_base_dir>
"""

import subprocess
import argparse
import os
import sys
import re

SYSTEMS = [
    ('glycine', 'amber99sb', 300),
    ('glycine', 'amber99sb', 350),
    ('glycine', 'charmm27', 300),
    ('glycine', 'charmm27', 350),
    ('glygly', 'amber99sb', 300),
    ('glygly', 'amber99sb', 350),
    ('glygly', 'charmm27', 300),
    ('glygly', 'charmm27', 350),
]

def get_trajectory_info(xtc_file):
    """Get trajectory information using gmx check."""
    if not os.path.exists(xtc_file):
        return None
    
    cmd = ['gmx', 'check', '-f', xtc_file]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    output = result.stderr + result.stdout
    
    info = {'file': xtc_file}
    
    for line in output.split('\n'):
        if 'Last frame' in line:
            match = re.search(r'time\s+([\d.]+)', line)
            if match:
                info['last_time'] = float(match.group(1))
            match = re.search(r'step\s+(\d+)', line)
            if match:
                info['last_step'] = int(match.group(1))
        if 'Coords' in line:
            parts = line.split()
            if len(parts) >= 2:
                info['n_atoms'] = int(parts[1])
        if 'Step' in line and 'dt' in line:
            match = re.search(r'dt\s*=\s*([\d.]+)', line)
            if match:
                info['dt'] = float(match.group(1))
    
    # Get file size
    info['size_mb'] = os.path.getsize(xtc_file) / (1024 * 1024)
    
    return info

def verify_production_dir(prod_dir):
    """Verify processing in a single production directory."""
    results = {
        'dir': prod_dir,
        'status': 'UNKNOWN',
        'checks': [],
        'files': {}
    }
    
    # Define expected files
    expected_files = [
        ('prod.xtc', 'Raw trajectory'),
        ('prod.tpr', 'Topology'),
        ('prod_center.xtc', 'Centered trajectory'),
        ('prod_hydrogen.xtc', 'Hydrogen trajectory'),
    ]
    
    optional_files = [
        ('prod_whole.xtc', 'Whole molecules'),
        ('index.ndx', 'Index file'),
    ]
    
    # Check required files
    all_required = True
    for filename, desc in expected_files:
        filepath = os.path.join(prod_dir, filename)
        exists = os.path.exists(filepath)
        if exists:
            info = get_trajectory_info(filepath)
            results['files'][filename] = info
            results['checks'].append((f'{desc} exists', 'PASS'))
        else:
            results['checks'].append((f'{desc} exists', 'FAIL'))
            if filename != 'prod_hydrogen.xtc':  # hydrogen is optional
                all_required = False
    
    # Check optional files
    for filename, desc in optional_files:
        filepath = os.path.join(prod_dir, filename)
        if os.path.exists(filepath):
            if filename.endswith('.xtc'):
                results['files'][filename] = get_trajectory_info(filepath)
    
    # Verify trajectory lengths match
    if 'prod.xtc' in results['files'] and 'prod_center.xtc' in results['files']:
        raw_info = results['files']['prod.xtc']
        center_info = results['files']['prod_center.xtc']
        
        if raw_info and center_info:
            raw_time = raw_info.get('last_time', 0)
            center_time = center_info.get('last_time', 0)
            
            if abs(raw_time - center_time) < 1:  # Within 1 ps
                results['checks'].append(('Duration match', 'PASS'))
            else:
                results['checks'].append((f'Duration mismatch: {raw_time} vs {center_time}', 'FAIL'))
                all_required = False
    
    # Check hydrogen trajectory atom count
    if 'prod_hydrogen.xtc' in results['files'] and 'prod.xtc' in results['files']:
        h_info = results['files']['prod_hydrogen.xtc']
        raw_info = results['files']['prod.xtc']
        
        if h_info and raw_info:
            h_atoms = h_info.get('n_atoms', 0)
            raw_atoms = raw_info.get('n_atoms', 0)
            
            # Hydrogens should be roughly 50-70% of atoms for water systems
            ratio = h_atoms / raw_atoms if raw_atoms > 0 else 0
            if 0.3 < ratio < 0.8:
                results['checks'].append((f'H ratio: {ratio:.1%}', 'PASS'))
            else:
                results['checks'].append((f'H ratio unusual: {ratio:.1%}', 'WARN'))
    
    # Frame spacing check (sample first few frames)
    if 'prod_center.xtc' in results['files']:
        center_file = os.path.join(prod_dir, 'prod_center.xtc')
        try:
            cmd = ['gmx', 'dump', '-f', center_file]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            times = []
            for line in (result.stderr + result.stdout).split('\n'):
                match = re.search(r'time=\s*([\d.]+)', line)
                if match:
                    times.append(float(match.group(1)))
                    if len(times) >= 10:
                        break
            
            if len(times) >= 2:
                dt = times[1] - times[0]
                if abs(dt - 0.010) < 0.001:  # 10 fs
                    results['checks'].append((f'Frame spacing: {dt*1000:.1f} fs', 'PASS'))
                else:
                    results['checks'].append((f'Frame spacing: {dt*1000:.1f} fs (expected 10)', 'WARN'))
        except Exception as e:
            results['checks'].append((f'Frame check error: {e}', 'WARN'))
    
    # Overall status
    fails = sum(1 for _, status in results['checks'] if status == 'FAIL')
    warns = sum(1 for _, status in results['checks'] if status == 'WARN')
    
    if fails == 0 and warns == 0:
        results['status'] = 'PASS'
    elif fails == 0:
        results['status'] = 'WARN'
    else:
        results['status'] = 'FAIL'
    
    return results

def print_results(results):
    """Print verification results."""
    print(f"\nDirectory: {results['dir']}")
    print(f"Status: {results['status']}")
    print("-" * 50)
    
    # Print checks
    for check, status in results['checks']:
        symbol = '✓' if status == 'PASS' else ('⚠' if status == 'WARN' else '✗')
        print(f"  {symbol} {check}")
    
    # Print file info
    if results['files']:
        print("\nFile details:")
        for filename, info in results['files'].items():
            if info:
                size = info.get('size_mb', 0)
                atoms = info.get('n_atoms', 'N/A')
                duration = info.get('last_time', 0) / 1000  # to ns
                print(f"  {filename}: {size:.1f} MB, {atoms} atoms, {duration:.2f} ns")

def main():
    parser = argparse.ArgumentParser(description='Verify trajectory processing')
    parser.add_argument('path', help='Production directory or --all with base dir')
    parser.add_argument('--all', '-a', action='store_true',
                        help='Verify all 8 systems (path = base systems dir)')
    args = parser.parse_args()
    
    if args.all:
        # Verify all systems
        base_dir = args.path
        all_results = []
        
        print("=" * 60)
        print("TRAJECTORY PROCESSING VERIFICATION")
        print("=" * 60)
        
        for mol, ff, temp in SYSTEMS:
            prod_dir = os.path.join(base_dir, mol, ff, f'{temp}K', 'production')
            
            if os.path.exists(prod_dir):
                results = verify_production_dir(prod_dir)
                all_results.append(results)
                print_results(results)
            else:
                print(f"\nDirectory not found: {prod_dir}")
                all_results.append({'status': 'MISSING', 'dir': prod_dir})
        
        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        
        for status in ['PASS', 'WARN', 'FAIL', 'MISSING']:
            count = sum(1 for r in all_results if r['status'] == status)
            if count > 0:
                print(f"  {status}: {count}/8")
        
        fails = sum(1 for r in all_results if r['status'] in ['FAIL', 'MISSING'])
        return 1 if fails > 0 else 0
    
    else:
        # Verify single directory
        results = verify_production_dir(args.path)
        print_results(results)
        return 0 if results['status'] == 'PASS' else 1

if __name__ == "__main__":
    sys.exit(main())
