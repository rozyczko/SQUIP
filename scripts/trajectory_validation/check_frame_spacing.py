#!/usr/bin/env python3
"""
"""check_frame_spacing.py - Verify 30 fs frame spacing in trajectory
Usage: python check_frame_spacing.py <trajectory.xtc> [--tpr topology.tpr]
"""

import subprocess
import sys
import re
import argparse

def get_frame_times(xtc_file, tpr_file=None, max_frames=1000):
    """Extract frame times from trajectory using gmx dump."""
    cmd = ["gmx", "dump", "-f", xtc_file]
    if tpr_file:
        cmd.extend(["-s", tpr_file])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        output = result.stderr + result.stdout
    except subprocess.TimeoutExpired:
        print("Warning: gmx dump timed out, may be very large trajectory")
        return []
    
    times = []
    for line in output.split('\n'):
        match = re.search(r'time=\s*([\d.]+)', line)
        if match:
            times.append(float(match.group(1)))
            if len(times) >= max_frames:
                break
    
    return times

def analyze_spacing(times, expected_dt=0.030):
    """Analyze frame spacing (expected 30 fs = 0.030 ps)."""
    if len(times) < 2:
        return None, None, None, None
    
    spacings = []
    anomalies = []
    
    for i in range(1, len(times)):
        dt = times[i] - times[i-1]
        spacings.append(dt)
        
        # Check if spacing deviates from expected (allow 1% tolerance)
        if abs(dt - expected_dt) > expected_dt * 0.01:
            anomalies.append((i, times[i-1], times[i], dt))
    
    avg_dt = sum(spacings) / len(spacings)
    min_dt = min(spacings)
    max_dt = max(spacings)
    
    return avg_dt, min_dt, max_dt, anomalies

def main():
    parser = argparse.ArgumentParser(description='Check trajectory frame spacing')
    parser.add_argument('trajectory', help='Input trajectory file (.xtc)')
    parser.add_argument('--tpr', '-s', help='TPR file for topology', default=None)
    parser.add_argument('--expected-dt', type=float, default=0.030,
                        help='Expected time step in ps (default: 0.030 = 30 fs)')
    parser.add_argument('--max-frames', type=int, default=1000,
                        help='Maximum frames to check (default: 1000)')
    args = parser.parse_args()
    
    print(f"Checking frame spacing in: {args.trajectory}")
    print(f"Expected dt: {args.expected_dt} ps ({args.expected_dt * 1000:.1f} fs)")
    print()
    
    times = get_frame_times(args.trajectory, args.tpr, args.max_frames)
    
    if not times:
        print("ERROR: Could not extract frame times")
        sys.exit(1)
    
    print(f"Frames analyzed: {len(times)}")
    print(f"First time: {times[0]} ps")
    print(f"Last time: {times[-1]} ps")
    print(f"Time range: {times[-1] - times[0]} ps")
    print()
    
    avg_dt, min_dt, max_dt, anomalies = analyze_spacing(times, args.expected_dt)
    
    if avg_dt is None:
        print("ERROR: Not enough frames to analyze")
        sys.exit(1)
    
    print("Frame Spacing Analysis:")
    print(f"  Average dt: {avg_dt:.6f} ps ({avg_dt * 1000:.3f} fs)")
    print(f"  Min dt:     {min_dt:.6f} ps")
    print(f"  Max dt:     {max_dt:.6f} ps")
    print()
    
    # Check if average matches expected
    tolerance = args.expected_dt * 0.01
    if abs(avg_dt - args.expected_dt) <= tolerance:
        print(f"✓ Frame spacing CORRECT (within 1% of {args.expected_dt} ps)")
        status = "PASS"
    else:
        print(f"✗ Frame spacing INCORRECT (expected {args.expected_dt} ps)")
        status = "FAIL"
    
    if anomalies:
        print(f"\nWARNING: {len(anomalies)} anomalous frame spacings detected:")
        for idx, t1, t2, dt in anomalies[:10]:
            print(f"  Frame {idx}: {t1:.6f} -> {t2:.6f} ps (dt = {dt:.6f} ps)")
        if len(anomalies) > 10:
            print(f"  ... and {len(anomalies) - 10} more")
    else:
        print("\n✓ No anomalous frame spacings detected")
    
    print(f"\nStatus: {status}")
    return 0 if status == "PASS" else 1

if __name__ == "__main__":
    sys.exit(main())
