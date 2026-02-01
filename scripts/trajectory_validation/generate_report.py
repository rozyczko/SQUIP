#!/usr/bin/env python3
"""
generate_report.py - Generate consolidated validation report for all systems
Usage: python generate_report.py --base-dir /path/to/systems
"""

import os
import subprocess
import sys
import argparse
from datetime import datetime

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

def get_trajectory_info(prod_dir):
    """Get trajectory length and frame count."""
    xtc_file = os.path.join(prod_dir, 'prod.xtc')
    if not os.path.exists(xtc_file):
        return None, None
    
    try:
        result = subprocess.run(['gmx', 'check', '-f', xtc_file],
                               capture_output=True, text=True, timeout=60)
        output = result.stderr + result.stdout
        
        last_time = None
        for line in output.split('\n'):
            if 'Last frame' in line:
                parts = line.split()
                for i, p in enumerate(parts):
                    if p == 'time':
                        last_time = float(parts[i+1])
                        break
        
        return last_time, None
    except Exception as e:
        return None, str(e)

def get_energy_averages(prod_dir):
    """Extract average temperature, pressure, density."""
    edr_file = os.path.join(prod_dir, 'prod.edr')
    if not os.path.exists(edr_file):
        return {}
    
    results = {}
    properties = [
        ('temperature', '16 0'),
        ('pressure', '18 0'),
        ('density', '24 0'),
    ]
    
    for prop_name, selection in properties:
        try:
            xvg_file = f'/tmp/{prop_name}.xvg'
            proc = subprocess.Popen(['gmx', 'energy', '-f', edr_file, '-o', xvg_file],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True)
            proc.communicate(input=selection, timeout=60)
            
            if os.path.exists(xvg_file):
                values = []
                with open(xvg_file) as f:
                    for line in f:
                        if not line.startswith('#') and not line.startswith('@'):
                            parts = line.split()
                            if len(parts) >= 2:
                                values.append(float(parts[1]))
                
                if values:
                    # Skip first 10% for equilibration
                    skip = len(values) // 10
                    equil_values = values[skip:]
                    avg = sum(equil_values) / len(equil_values)
                    results[prop_name] = avg
                
                os.remove(xvg_file)
        except Exception:
            pass
    
    return results

def check_completion(prod_dir):
    """Check if simulation completed."""
    log_file = os.path.join(prod_dir, 'prod.log')
    if not os.path.exists(log_file):
        return False, "Log file missing"
    
    with open(log_file) as f:
        content = f.read()
    
    if 'Finished mdrun' in content:
        return True, "Completed"
    elif 'FATAL' in content.upper():
        return False, "Fatal error"
    else:
        return False, "Incomplete"

def get_performance(prod_dir):
    """Extract performance from log."""
    log_file = os.path.join(prod_dir, 'prod.log')
    if not os.path.exists(log_file):
        return None
    
    with open(log_file) as f:
        for line in f:
            if 'ns/day' in line.lower():
                parts = line.split()
                for i, p in enumerate(parts):
                    try:
                        val = float(p)
                        if i + 1 < len(parts) and 'ns' in parts[i+1].lower():
                            return val
                    except ValueError:
                        continue
    return None

def get_file_size(filepath):
    """Get file size in GB."""
    if os.path.exists(filepath):
        size_bytes = os.path.getsize(filepath)
        return size_bytes / (1024**3)
    return 0

def main():
    parser = argparse.ArgumentParser(description='Generate validation report')
    parser.add_argument('--base-dir', '-d', required=True, help='Base systems directory')
    parser.add_argument('--output', '-o', default='validation_report.txt', help='Output report file')
    args = parser.parse_args()
    
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("PRODUCTION MD VALIDATION REPORT")
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"Base directory: {args.base_dir}")
    report_lines.append("=" * 80)
    
    summary = {
        'completed': 0,
        'incomplete': 0,
        'not_started': 0,
        'total_size': 0,
    }
    
    for mol, ff, temp in SYSTEMS:
        prod_dir = os.path.join(args.base_dir, mol, ff, f'{temp}K', 'production')
        
        report_lines.append("")
        report_lines.append(f"\n{'='*60}")
        report_lines.append(f"System: {mol} / {ff} / {temp}K")
        report_lines.append(f"Directory: {prod_dir}")
        report_lines.append("-" * 60)
        
        # Check if production directory exists
        if not os.path.exists(prod_dir):
            report_lines.append("Status: NOT STARTED")
            summary['not_started'] += 1
            continue
        
        # Check completion
        completed, status = check_completion(prod_dir)
        report_lines.append(f"Completion: {status}")
        
        if completed:
            summary['completed'] += 1
        else:
            summary['incomplete'] += 1
            continue
        
        # Get trajectory info
        last_time, error = get_trajectory_info(prod_dir)
        if last_time:
            report_lines.append(f"Trajectory length: {last_time/1000:.2f} ns")
        
        # Get thermodynamic properties
        props = get_energy_averages(prod_dir)
        if 'temperature' in props:
            delta_T = props['temperature'] - temp
            status = "✓" if abs(delta_T) < 5 else "✗"
            report_lines.append(f"Temperature: {props['temperature']:.1f} K (expected {temp} K) {status}")
        if 'pressure' in props:
            report_lines.append(f"Pressure: {props['pressure']:.1f} bar")
        if 'density' in props:
            report_lines.append(f"Density: {props['density']:.1f} kg/m³")
        
        # Performance
        perf = get_performance(prod_dir)
        if perf:
            report_lines.append(f"Performance: {perf:.1f} ns/day")
        
        # File sizes
        xtc_size = get_file_size(os.path.join(prod_dir, 'prod.xtc'))
        summary['total_size'] += xtc_size
        report_lines.append(f"Trajectory size: {xtc_size:.1f} GB")
    
    # Summary
    report_lines.append("\n" + "=" * 80)
    report_lines.append("SUMMARY")
    report_lines.append("=" * 80)
    report_lines.append(f"Completed:   {summary['completed']}/8")
    report_lines.append(f"Incomplete:  {summary['incomplete']}/8")
    report_lines.append(f"Not started: {summary['not_started']}/8")
    report_lines.append(f"Total trajectory storage: {summary['total_size']:.1f} GB")
    
    if summary['completed'] == 8:
        report_lines.append("\n✓ ALL SYSTEMS COMPLETED")
    
    report_lines.append("=" * 80)
    
    # Write report
    report_text = '\n'.join(report_lines)
    print(report_text)
    
    with open(args.output, 'w') as f:
        f.write(report_text)
    
    print(f"\nReport saved: {args.output}")
    
    return 0 if summary['completed'] == 8 else 1

if __name__ == "__main__":
    sys.exit(main())
