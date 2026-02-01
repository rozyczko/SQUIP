# Trajectory Processing Scripts

Scripts for processing production trajectories for QENS analysis (Substep 2.5).

## Quick Start

```bash
# Upload to workstation
scp -r scripts/trajectory_processing/ user@workstation:~/SQUIP/scripts/

# On workstation
cd ~/SQUIP/scripts/trajectory_processing
chmod +x *.sh

# Process all 8 systems
./process_all.sh ../systems
```

## Scripts Overview

### Master Script

| Script | Purpose |
|--------|---------|
| `process_all.sh` | Process all 8 production trajectories |

### Individual Processing Scripts

| Script | Purpose |
|--------|---------|
| `process_trajectory.sh` | Full processing pipeline for one system |
| `center_trajectory.sh` | Center trajectory and fix PBC |
| `extract_hydrogens.py` | Extract hydrogen-only trajectory |
| `extract_solute.sh` | Extract non-water atoms |
| `create_windows.sh` | Create time-windowed subtrajectories |

### Verification

| Script | Purpose |
|--------|---------|
| `verify_processing.py` | Verify processing was successful |

## Processing Pipeline

The full processing pipeline creates:

1. **prod_whole.xtc** - Molecules made whole (no broken bonds across PBC)
2. **prod_center.xtc** - Centered trajectory with compact PBC representation
3. **prod_hydrogen.xtc** - Hydrogen atoms only (for QENS analysis)
4. **index.ndx** - Index file with useful atom groups

### Why These Steps?

- **Making whole**: Fixes molecules that cross periodic boundaries
- **Centering**: Keeps system in center of box, compact representation
- **Hydrogen extraction**: QENS dominated by H incoherent scattering (σ_inc = 80.27 barn)

## Usage Examples

### Process All Systems

```bash
./process_all.sh systems/
```

### Process Single System

```bash
./process_trajectory.sh systems/glycine/amber99sb/300K/production/
```

### Just Center a Trajectory

```bash
./center_trajectory.sh systems/glycine/amber99sb/300K/production/
```

### Extract Hydrogens with Options

```bash
# All hydrogens
python extract_hydrogens.py prod.xtc --tpr prod.tpr

# Only solute (non-water) hydrogens
python extract_hydrogens.py prod.xtc --tpr prod.tpr --solute-only

# Only water hydrogens
python extract_hydrogens.py prod.xtc --tpr prod.tpr --water-only
```

### Create Time Windows

```bash
# Default: 1 ns windows, no overlap
./create_windows.sh systems/glycine/amber99sb/300K/production/

# 2 ns windows
./create_windows.sh systems/glycine/amber99sb/300K/production/ 2

# 2 ns windows with 1 ns overlap
./create_windows.sh systems/glycine/amber99sb/300K/production/ 2 1
```

### Extract Solute Only

```bash
./extract_solute.sh systems/glycine/amber99sb/300K/production/
```

### Verify Processing

```bash
# Single system
python verify_processing.py systems/glycine/amber99sb/300K/production/

# All 8 systems
python verify_processing.py --all systems/
```

## Expected Output

After processing, each production directory should contain:

```
production/
├── prod.tpr           # Original TPR
├── prod.xtc           # Raw trajectory (~100-150 GB)
├── prod.edr           # Energy file
├── prod.log           # Log file
├── prod.gro           # Final structure
├── prod_whole.xtc     # Whole molecules
├── prod_center.xtc    # Centered (same size as raw)
├── prod_hydrogen.xtc  # H only (~5-15 GB)
├── prod_solute.xtc    # Solute only (optional)
└── index.ndx          # Index groups
```

## Storage Estimates

For 20 ns trajectory at 10 fs output:

| File | AMBER (TIP4P-Ew) | CHARMM (TIP3P) |
|------|------------------|----------------|
| prod.xtc | ~140 GB | ~115 GB |
| prod_center.xtc | ~140 GB | ~115 GB |
| prod_hydrogen.xtc | ~15 GB | ~12 GB |

Total per system: ~300-350 GB (with intermediate files)

## QENS-Specific Notes

### Hydrogen Trajectories

For QENS analysis, hydrogen atoms dominate the measured signal due to their large incoherent neutron scattering cross-section:

| Atom | σ_inc (barn) |
|------|--------------|
| H | 80.27 |
| D | 2.05 |
| C | 0.001 |
| N | 0.5 |
| O | 0.0 |

The `extract_hydrogens.py` script creates H-only trajectories for efficient S(q,ω) calculation.

### Time Windows

For ensemble averaging and error estimation, `create_windows.sh` splits trajectories into independent time blocks. Typical usage:
- 1 ns windows for good statistics
- 2 ns windows for longer correlation times
- Overlapping windows for block averaging

## Dependencies

- GROMACS 2021+ (gmx commands in PATH)
- Python 3.6+ with standard library
- bc (for shell arithmetic)

## Troubleshooting

### "Group not found"

If `gmx trjconv` complains about group names, use index numbers instead:
```bash
echo "0 0" | gmx trjconv -f in.xtc -s prod.tpr -o out.xtc -center -pbc mol
```

### Large Memory Usage

For very large trajectories, process in chunks:
```bash
gmx trjconv -f prod.xtc -s prod.tpr -o prod_center.xtc -b 0 -e 10000 ...
```

### Slow Processing

For faster processing, skip unnecessary steps. If only hydrogen trajectory is needed:
```bash
python extract_hydrogens.py prod.xtc --tpr prod.tpr
```
