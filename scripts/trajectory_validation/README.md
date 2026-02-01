# Trajectory Validation Scripts

Scripts for validating GROMACS production MD trajectories (Substep 2.4).

## Quick Start

```bash
# Upload entire directory to workstation
scp -r scripts/trajectory_validation/ user@workstation:~/SQUIP/scripts/

# Run on workstation
cd ~/SQUIP/scripts/trajectory_validation
chmod +x *.sh
./validate_all.sh ../systems
```

## Scripts Overview

### Bash Scripts

| Script | Purpose |
|--------|---------|
| `validate_all.sh` | Master script - validates all 8 systems |
| `validate_trajectory.sh` | Full validation for single trajectory |
| `quick_check.sh` | Fast pass/fail check for single system |
| `check_warnings.sh` | Scan log for LINCS/errors |

### Python Scripts

| Script | Purpose |
|--------|---------|
| `check_frame_spacing.py` | Verify 10 fs frame intervals |
| `extract_properties.py` | Extract T, P, density from .edr |
| `generate_report.py` | Consolidated report for all systems |

## Individual Script Usage

### Quick Check (fast pass/fail)
```bash
./quick_check.sh systems/glycine/amber99sb/300K/production/
```

### Full Validation
```bash
./validate_trajectory.sh systems/glycine/amber99sb/300K/production/ glycine_amber_300K
```

### Check Frame Spacing
```bash
python check_frame_spacing.py systems/glycine/amber99sb/300K/production/prod.xtc
```

### Extract Properties
```bash
python extract_properties.py systems/glycine/amber99sb/300K/production/prod.edr --output-dir results/ --temperature 300
```

### Generate Consolidated Report
```bash
python generate_report.py --base-dir systems/ --output validation_report.txt
```

### Check Warnings
```bash
./check_warnings.sh systems/glycine/amber99sb/300K/production/prod.log
```

## Validation Checks

The scripts verify:

1. **Completeness**: Trajectory reaches ~20 ns
2. **Frame spacing**: Consistent 10 fs intervals
3. **Temperature**: Within 5 K of target (300 K or 350 K)
4. **Pressure**: Reasonable fluctuations around 1 bar
5. **Density**: ~1000 kg/m³ for aqueous systems
6. **Warnings**: No fatal errors, few LINCS warnings
7. **File integrity**: All required files present

## Expected Results

For a successful 20 ns production run:
- Trajectory length: ~20,000 ps
- Frame count: ~2,000,000 frames
- Trajectory size: 100-150 GB
- Temperature: 300±5 K or 350±5 K
- Pressure: 1±100 bar (large fluctuations normal)
- LINCS warnings: < 100

## Output Files

Each validation produces:
- `*_report.txt` - Full validation report
- `*_temperature.xvg` - Temperature time series
- `*_pressure.xvg` - Pressure time series
- `*_density.xvg` - Density time series
- `*_total_energy.xvg` - Total energy time series

## Dependencies

- GROMACS (gmx commands in PATH)
- Python 3.6+ with NumPy
- bc (for shell arithmetic)
