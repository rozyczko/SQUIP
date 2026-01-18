# Box Dimension Analysis for SQUIP Systems

## Overview

This analysis calculates optimal simulation box dimensions to achieve approximately 1.0 M concentration with 50 solute molecules.

## Calculation Method

1. **Target Concentration**: 1 M = 1 mol/L = 6.022 × 10²³ molecules/L
2. **Volume Calculation**: V = n_molecules / (concentration × N_A)
3. **Box Size**: For cubic box, side = V^(1/3)
4. **Water Filling**: Remaining volume filled with TIP3P water (ρ ≈ 997 kg/m³)
5. **Target System Size**: 15,000-20,000 total atoms

## System Specifications

### Glycine

- **Formula**: C2H5NO2
- **Molecular Weight**: 75.07 g/mol
- **Atoms per molecule**: 10
- **Number of molecules**: 50

### Gly-Gly

- **Formula**: C4H8N2O3
- **Molecular Weight**: 132.12 g/mol
- **Atoms per molecule**: 17
- **Number of molecules**: 50

## Box Size Analysis

### Glycine System

| Box Size (nm) | Water Molecules | Solute Atoms | Water Atoms | Total Atoms | Concentration (M) |
|---------------|-----------------|--------------|-------------|-------------|-------------------|
| 4.0 | 2,037 | 500 | 6,111 | 6,611 | 1.297 |
| 4.5 | 2,943 | 500 | 8,829 | 9,329 | 0.911 |
| 5.0 | 4,075 | 500 | 12,225 | 12,725 | 0.664 |
| 5.5 | 5,456 | 500 | 16,368 | 16,868 | 0.499 |
| 6.0 | 7,114 | 500 | 21,342 | 21,842 | 0.384 |
| 6.5 | 9,072 | 500 | 27,216 | 27,716 | 0.302 |

### Gly-Gly System

| Box Size (nm) | Water Molecules | Solute Atoms | Water Atoms | Total Atoms | Concentration (M) |
|---------------|-----------------|--------------|-------------|-------------|-------------------|
| 4.0 | 2,037 | 850 | 6,111 | 6,961 | 1.297 |
| 4.5 | 2,943 | 850 | 8,829 | 9,679 | 0.911 |
| 5.0 | 4,075 | 850 | 12,225 | 13,075 | 0.664 |
| 5.5 | 5,456 | 850 | 16,368 | 17,218 | 0.499 |
| 6.0 | 7,114 | 850 | 21,342 | 22,192 | 0.384 |
| 6.5 | 9,072 | 850 | 27,216 | 28,066 | 0.302 |

## Recommendations

### Glycine

**Recommended box size: 5.5 nm × 5.5 nm × 5.5 nm**

- Total atoms: 16,868
- Water molecules: 5,456
- Solute atoms: 500
- Actual concentration: 0.499 M
- Box volume: 166.38 nm³

### Gly-Gly

**Recommended box size: 5.5 nm × 5.5 nm × 5.5 nm**

- Total atoms: 17,218
- Water molecules: 5,456
- Solute atoms: 850
- Actual concentration: 0.499 M
- Box volume: 166.38 nm³

## Implementation Notes

1. **GROMACS Commands**: Use `gmx insert-molecules` with `-box` parameter
2. **Water Model**: TIP3P water will be added using `gmx solvate`
3. **Concentration**: Actual concentration may vary slightly based on final packing
4. **System Size**: Final atom count will depend on exact water placement
5. **Force Fields**: These dimensions apply to both CHARMM36m and AMBER ff19SB

## Next Steps

Proceed with Substep 1.3, part 2:
- Use `gmx insert-molecules` to create boxes with 50 solute molecules
- Apply recommended box dimensions from above
- Solvate with TIP3P water using `gmx solvate`
