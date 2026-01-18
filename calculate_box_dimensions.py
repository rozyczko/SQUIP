"""
Calculate box dimensions for solvated systems
Target: 1 M aqueous solution with ~50 molecules
"""

import math

def calculate_box_dimensions(n_molecules, concentration_M):
    """
    Calculate cubic box dimensions for a given concentration
    
    Parameters:
    -----------
    n_molecules : int
        Number of solute molecules
    concentration_M : float
        Target concentration in mol/L (M)
    
    Returns:
    --------
    dict with volume (nm³) and box side length (nm)
    """
    # Avogadro's number
    N_A = 6.022e23  # molecules/mol
    
    # Convert concentration to molecules/nm³
    # 1 M = 1 mol/L = 1 mol / 1000 cm³
    # 1 cm³ = 10⁷ nm³
    conc_molecules_per_nm3 = concentration_M * N_A / (1000 * 1e21)  # molecules/nm³
    
    # Calculate volume needed
    volume_nm3 = n_molecules / conc_molecules_per_nm3
    
    # Calculate side length for cubic box
    side_length_nm = volume_nm3 ** (1/3)
    
    return {
        'volume_nm3': volume_nm3,
        'side_length_nm': side_length_nm,
        'volume_L': volume_nm3 * 1e-24,  # Convert nm³ to L
    }

def estimate_total_atoms(n_solute, atoms_per_solute, box_side_nm):
    """
    Estimate total number of atoms in solvated system
    
    Parameters:
    -----------
    n_solute : int
        Number of solute molecules
    atoms_per_solute : int
        Atoms per solute molecule
    box_side_nm : float
        Box side length in nm
    
    Returns:
    --------
    dict with atom counts
    """
    # Water density at 300K: approximately 33.4 molecules/nm³
    # (calculated from 997 kg/m³ bulk water)
    water_molecules_per_nm3 = 33.4
    
    # Box volume
    box_volume_nm3 = box_side_nm ** 3
    
    # Total water molecules that would fit (rough estimate)
    # Assuming solute takes negligible volume for first approximation
    n_water_total = int(box_volume_nm3 * water_molecules_per_nm3)
    
    # Subtract approximate volume for solute molecules
    # Rough estimate: each solute molecule displaces ~2-3 water molecules
    water_displaced = n_solute * 2
    n_water = n_water_total - water_displaced
    
    # Total atoms
    atoms_per_water = 3  # H2O
    solute_atoms = n_solute * atoms_per_solute
    water_atoms = n_water * atoms_per_water
    total_atoms = solute_atoms + water_atoms
    
    return {
        'n_solute_molecules': n_solute,
        'n_water_molecules': n_water,
        'solute_atoms': solute_atoms,
        'water_atoms': water_atoms,
        'total_atoms': total_atoms,
        'box_volume_nm3': box_volume_nm3
    }

def main():
    """Main calculation and report generation"""
    
    print("=" * 70)
    print("BOX DIMENSION CALCULATIONS FOR SQUIP SYSTEMS")
    print("=" * 70)
    print()
    
    # System parameters
    target_concentration = 1.0  # M
    n_molecules = 50
    
    # Molecule data
    molecules = {
        'Glycine': {
            'atoms': 10,
            'formula': 'C2H5NO2',
            'molecular_weight': 75.07  # g/mol
        },
        'Gly-Gly': {
            'atoms': 17,
            'formula': 'C4H8N2O3',
            'molecular_weight': 132.12  # g/mol
        }
    }
    
    results = {}
    
    for mol_name, mol_data in molecules.items():
        print(f"\n{mol_name} System")
        print("-" * 70)
        
        # Calculate box dimensions
        box_calc = calculate_box_dimensions(n_molecules, target_concentration)
        
        print(f"Target concentration: {target_concentration} M")
        print(f"Number of {mol_name} molecules: {n_molecules}")
        print(f"Atoms per molecule: {mol_data['atoms']}")
        print(f"\nCalculated box parameters:")
        print(f"  Volume needed: {box_calc['volume_nm3']:.2f} nm³ ({box_calc['volume_L']:.6e} L)")
        print(f"  Cubic box side: {box_calc['side_length_nm']:.3f} nm")
        
        # Try different box sizes and estimate atom counts
        test_sizes = [4.0, 4.5, 5.0, 5.5, 6.0, 6.5]
        
        print(f"\nAtom count estimates for different box sizes:")
        print(f"{'Box (nm)':>10} {'Water Mol':>12} {'Total Atoms':>12} {'Actual Conc (M)':>16}")
        print("-" * 70)
        
        for box_size in test_sizes:
            atom_est = estimate_total_atoms(n_molecules, mol_data['atoms'], box_size)
            
            # Calculate actual concentration
            volume_L = box_size**3 * 1e-24  # nm³ to L
            actual_conc = (n_molecules / 6.022e23) / volume_L
            
            print(f"{box_size:10.1f} {atom_est['n_water_molecules']:12d} "
                  f"{atom_est['total_atoms']:12d} {actual_conc:16.3f}")
            
            if box_size not in results:
                results[box_size] = {}
            results[box_size][mol_name] = atom_est
    
    # Find optimal box size (closest to 15,000-20,000 atoms)
    print("\n" + "=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)
    
    target_min, target_max = 15000, 20000
    
    for mol_name in molecules.keys():
        print(f"\n{mol_name}:")
        best_box = None
        best_diff = float('inf')
        
        for box_size in test_sizes:
            total = results[box_size][mol_name]['total_atoms']
            if target_min <= total <= target_max:
                diff = abs(total - (target_min + target_max) / 2)
                if diff < best_diff:
                    best_diff = diff
                    best_box = box_size
        
        if best_box:
            stats = results[best_box][mol_name]
            volume_L = best_box**3 * 1e-24
            actual_conc = (n_molecules / 6.022e23) / volume_L
            print(f"  Recommended box size: {best_box} nm")
            print(f"  Total atoms: {stats['total_atoms']:,}")
            print(f"  Water molecules: {stats['n_water_molecules']:,}")
            print(f"  Actual concentration: {actual_conc:.3f} M")
        else:
            print(f"  No box size in tested range meets target atom count")
            print(f"  Consider adjusting target or box size range")
    
    # Write results to markdown file
    write_markdown_report(molecules, results, test_sizes, n_molecules, target_concentration)
    
    print("\n" + "=" * 70)
    print("Report saved to BOX_ANALYSIS.md")
    print("=" * 70)

def write_markdown_report(molecules, results, test_sizes, n_molecules, target_concentration):
    """Write detailed analysis to markdown file"""
    
    with open('BOX_ANALYSIS.md', 'w', encoding='utf-8') as f:
        f.write("# Box Dimension Analysis for SQUIP Systems\n\n")
        f.write("## Overview\n\n")
        f.write("This analysis calculates optimal simulation box dimensions to achieve ")
        f.write(f"approximately {target_concentration} M concentration with {n_molecules} solute molecules.\n\n")
        
        f.write("## Calculation Method\n\n")
        f.write("1. **Target Concentration**: 1 M = 1 mol/L = 6.022 × 10²³ molecules/L\n")
        f.write("2. **Volume Calculation**: V = n_molecules / (concentration × N_A)\n")
        f.write("3. **Box Size**: For cubic box, side = V^(1/3)\n")
        f.write("4. **Water Filling**: Remaining volume filled with TIP3P water (ρ ≈ 997 kg/m³)\n")
        f.write("5. **Target System Size**: 15,000-20,000 total atoms\n\n")
        
        f.write("## System Specifications\n\n")
        
        for mol_name, mol_data in molecules.items():
            f.write(f"### {mol_name}\n\n")
            f.write(f"- **Formula**: {mol_data['formula']}\n")
            f.write(f"- **Molecular Weight**: {mol_data['molecular_weight']} g/mol\n")
            f.write(f"- **Atoms per molecule**: {mol_data['atoms']}\n")
            f.write(f"- **Number of molecules**: {n_molecules}\n\n")
        
        f.write("## Box Size Analysis\n\n")
        
        for mol_name in molecules.keys():
            f.write(f"### {mol_name} System\n\n")
            f.write("| Box Size (nm) | Water Molecules | Solute Atoms | Water Atoms | Total Atoms | Concentration (M) |\n")
            f.write("|---------------|-----------------|--------------|-------------|-------------|-------------------|\n")
            
            for box_size in test_sizes:
                stats = results[box_size][mol_name]
                volume_L = box_size**3 * 1e-24
                actual_conc = (n_molecules / 6.022e23) / volume_L
                
                f.write(f"| {box_size:.1f} | {stats['n_water_molecules']:,} | ")
                f.write(f"{stats['solute_atoms']:,} | {stats['water_atoms']:,} | ")
                f.write(f"{stats['total_atoms']:,} | {actual_conc:.3f} |\n")
            
            f.write("\n")
        
        f.write("## Recommendations\n\n")
        
        target_min, target_max = 15000, 20000
        
        for mol_name, mol_data in molecules.items():
            best_box = None
            best_diff = float('inf')
            
            for box_size in test_sizes:
                total = results[box_size][mol_name]['total_atoms']
                if target_min <= total <= target_max:
                    diff = abs(total - (target_min + target_max) / 2)
                    if diff < best_diff:
                        best_diff = diff
                        best_box = box_size
            
            if best_box:
                stats = results[best_box][mol_name]
                volume_L = best_box**3 * 1e-24
                actual_conc = (n_molecules / 6.022e23) / volume_L
                
                f.write(f"### {mol_name}\n\n")
                f.write(f"**Recommended box size: {best_box} nm × {best_box} nm × {best_box} nm**\n\n")
                f.write("- Total atoms: {:,}\n".format(stats['total_atoms']))
                f.write("- Water molecules: {:,}\n".format(stats['n_water_molecules']))
                f.write("- Solute atoms: {:,}\n".format(stats['solute_atoms']))
                f.write(f"- Actual concentration: {actual_conc:.3f} M\n")
                f.write(f"- Box volume: {best_box**3:.2f} nm³\n\n")
        
        f.write("## Implementation Notes\n\n")
        f.write("1. **GROMACS Commands**: Use `gmx insert-molecules` with `-box` parameter\n")
        f.write("2. **Water Model**: TIP3P water will be added using `gmx solvate`\n")
        f.write("3. **Concentration**: Actual concentration may vary slightly based on final packing\n")
        f.write("4. **System Size**: Final atom count will depend on exact water placement\n")
        f.write("5. **Force Fields**: These dimensions apply to both CHARMM36m and AMBER ff19SB\n\n")
        
        f.write("## Next Steps\n\n")
        f.write("Proceed with Substep 1.3, part 2:\n")
        f.write("- Use `gmx insert-molecules` to create boxes with 50 solute molecules\n")
        f.write("- Apply recommended box dimensions from above\n")
        f.write("- Solvate with TIP3P water using `gmx solvate`\n")

if __name__ == "__main__":
    main()
