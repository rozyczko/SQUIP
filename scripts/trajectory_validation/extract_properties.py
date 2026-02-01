#!/usr/bin/env python3
"""
extract_properties.py - Extract and analyze thermodynamic properties from .edr files
Usage: python extract_properties.py <prod.edr> [--output-dir results/]
"""

import subprocess
import sys
import argparse
import os
import numpy as np

def run_gmx_energy(edr_file, selection, output_xvg):
    """Run gmx energy with given selection."""
    cmd = ["gmx", "energy", "-f", edr_file, "-o", output_xvg]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, text=True)
    stdout, stderr = proc.communicate(input=selection)
    return proc.returncode == 0

def parse_xvg(xvg_file):
    """Parse XVG file and return times and values."""
    times = []
    values = []
    
    with open(xvg_file, 'r') as f:
        for line in f:
            if line.startswith('#') or line.startswith('@'):
                continue
            parts = line.split()
            if len(parts) >= 2:
                times.append(float(parts[0]))
                values.append(float(parts[1]))
    
    return np.array(times), np.array(values)

def compute_stats(values, skip_fraction=0.1):
    """Compute statistics, optionally skipping initial equilibration."""
    n_skip = int(len(values) * skip_fraction)
    equil_values = values[n_skip:]
    
    return {
        'mean': np.mean(equil_values),
        'std': np.std(equil_values),
        'min': np.min(equil_values),
        'max': np.max(equil_values),
        'full_mean': np.mean(values),
        'full_std': np.std(values),
        'n_points': len(equil_values),
        'n_skipped': n_skip
    }

def check_drift(times, values, property_name):
    """Check for linear drift in property."""
    # Simple linear regression
    n = len(times)
    if n < 10:
        return None
    
    x = times - times[0]
    y = values
    
    x_mean = np.mean(x)
    y_mean = np.mean(y)
    
    num = np.sum((x - x_mean) * (y - y_mean))
    den = np.sum((x - x_mean)**2)
    
    if den == 0:
        return None
    
    slope = num / den
    
    # Calculate drift per nanosecond
    drift_per_ns = slope * 1000  # slope is per ps
    
    return drift_per_ns

PROPERTIES = {
    'Temperature': {'selection': '16 0', 'unit': 'K', 'expected_300K': 300, 'expected_350K': 350, 'tolerance': 5},
    'Pressure': {'selection': '18 0', 'unit': 'bar', 'expected': 1, 'tolerance': 100},
    'Density': {'selection': '24 0', 'unit': 'kg/m³', 'expected': 1000, 'tolerance': 50},
    'Total-Energy': {'selection': '12 0', 'unit': 'kJ/mol'},
    'Potential': {'selection': '11 0', 'unit': 'kJ/mol'},
    'Kinetic-En.': {'selection': '13 0', 'unit': 'kJ/mol'},
    'Volume': {'selection': '23 0', 'unit': 'nm³'},
}

def main():
    parser = argparse.ArgumentParser(description='Extract thermodynamic properties from EDR')
    parser.add_argument('edr_file', help='Input .edr file')
    parser.add_argument('--output-dir', '-o', default='.', help='Output directory')
    parser.add_argument('--skip', type=float, default=0.1,
                        help='Fraction of data to skip for equilibration (default: 0.1)')
    parser.add_argument('--temperature', type=int, choices=[300, 350],
                        help='Expected temperature for validation')
    args = parser.parse_args()
    
    if not os.path.exists(args.edr_file):
        print(f"ERROR: File not found: {args.edr_file}")
        sys.exit(1)
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    print(f"Analyzing: {args.edr_file}")
    print(f"Output directory: {args.output_dir}")
    print(f"Skipping first {args.skip*100:.0f}% for equilibration")
    print()
    
    results = {}
    
    for prop_name, prop_info in PROPERTIES.items():
        xvg_file = os.path.join(args.output_dir, f"{prop_name.lower().replace('.', '')}.xvg")
        
        print(f"Extracting {prop_name}...", end=" ")
        
        if not run_gmx_energy(args.edr_file, prop_info['selection'], xvg_file):
            print("FAILED")
            continue
        
        try:
            times, values = parse_xvg(xvg_file)
            stats = compute_stats(values, args.skip)
            drift = check_drift(times, values, prop_name)
            
            results[prop_name] = {
                'stats': stats,
                'drift': drift,
                'unit': prop_info['unit'],
                'times': times,
                'values': values
            }
            
            print(f"{stats['mean']:.2f} ± {stats['std']:.2f} {prop_info['unit']}")
            
        except Exception as e:
            print(f"ERROR: {e}")
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for prop_name, data in results.items():
        stats = data['stats']
        unit = data['unit']
        drift = data['drift']
        
        print(f"\n{prop_name}:")
        print(f"  Mean (after equil): {stats['mean']:.4f} ± {stats['std']:.4f} {unit}")
        print(f"  Full trajectory:    {stats['full_mean']:.4f} ± {stats['full_std']:.4f} {unit}")
        print(f"  Range:              [{stats['min']:.4f}, {stats['max']:.4f}] {unit}")
        
        if drift is not None:
            print(f"  Drift:              {drift:.4f} {unit}/ns")
        
        # Validation checks
        prop_info = PROPERTIES.get(prop_name, {})
        
        if prop_name == 'Temperature' and args.temperature:
            expected = args.temperature
            if abs(stats['mean'] - expected) < prop_info.get('tolerance', 5):
                print(f"  ✓ PASS: Within {prop_info.get('tolerance', 5)} K of {expected} K")
            else:
                print(f"  ✗ FAIL: Expected ~{expected} K")
        
        elif 'expected' in prop_info:
            expected = prop_info['expected']
            tol = prop_info.get('tolerance', expected * 0.1)
            if abs(stats['mean'] - expected) < tol:
                print(f"  ✓ PASS: Within tolerance of {expected} {unit}")
    
    # Save summary
    summary_file = os.path.join(args.output_dir, "summary.txt")
    with open(summary_file, 'w') as f:
        f.write(f"EDR Analysis Summary\n")
        f.write(f"File: {args.edr_file}\n")
        f.write(f"Skip fraction: {args.skip}\n\n")
        
        for prop_name, data in results.items():
            stats = data['stats']
            f.write(f"{prop_name}: {stats['mean']:.4f} ± {stats['std']:.4f} {data['unit']}\n")
    
    print(f"\nSummary saved: {summary_file}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
