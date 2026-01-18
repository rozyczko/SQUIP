# Step 1: System Preparation - Implementation Plan

## Overview
This document provides a detailed implementation plan for **Step 1: System Preparation** from the SQUIP Proof of Concept workflow. The goal is to build solvated simulation boxes for glycine and glycine dipeptide (Gly-Gly) ready for MD simulations.

**Timeline**: Week 1  
**Target Systems**: Glycine (amino acid) and Gly-Gly (dipeptide)  
**Target Conditions**: 2 temperatures (300 K, 350 K) × 2 force fields (CHARMM36m, AMBER ff19SB)

---

## Substep 1.1: Obtain and Prepare Initial Molecular Structures

### Objective
Generate starting PDB files for glycine and Gly-Gly in their appropriate protonation states.

### Implementation Steps

1. **Source Initial Structures**
   - Download glycine structure from PDB or PubChem
   - Build Gly-Gly dipeptide structure using molecular editor or builder tools
   - Alternative: Use GROMACS `pdb2gmx` or AmberTools `tleap` to build from sequence

2. **Determine Protonation States**
   - pH: Assume physiological pH ~7 (or neutral aqueous solution)
   - Glycine: Zwitterionic form (NH3+, COO-)
   - Gly-Gly: N-terminus protonated (NH3+), C-terminus deprotonated (COO-)

3. **Validate Geometry**
   - Check bond lengths and angles are chemically reasonable
   - Ensure no steric clashes or unrealistic geometries
   - Save as clean PDB files: `glycine.pdb`, `gly-gly.pdb`

### Tools
- PyMOL, Avogadro, or ChimeraX for visualization and basic editing
- GROMACS `pdb2gmx` or AmberTools for building from scratch
- RDKit or OpenBabel for structure conversion if needed

### Deliverables
- `glycine.pdb` - Initial glycine structure
- `gly-gly.pdb` - Initial Gly-Gly dipeptide structure
- Documentation of protonation states chosen

---

## Substep 1.2: Generate Topology Files for Both Force Fields

### Objective
Create GROMACS topology files (.top) for each molecule using CHARMM36m and AMBER ff19SB force fields.

### Implementation Steps

1. **CHARMM36m Topologies**
   ```bash
   # For glycine
   gmx pdb2gmx -f glycine.pdb -o glycine_charmm.gro -p glycine_charmm.top -ff charmm36m -water tip3p
   
   # For Gly-Gly
   gmx pdb2gmx -f gly-gly.pdb -o gly-gly_charmm.gro -p gly-gly_charmm.top -ff charmm36m -water tip3p
   ```

2. **AMBER ff19SB Topologies**
   ```bash
   # For glycine
   gmx pdb2gmx -f glycine.pdb -o glycine_amber.gro -p glycine_amber.top -ff amber99sb-ildn -water tip3p
   # Note: May need to use AmberTools tleap for ff19SB, then convert with ParmEd
   
   # For Gly-Gly
   gmx pdb2gmx -f gly-gly.pdb -o gly-gly_amber.gro -p gly-gly_amber.top -ff amber99sb-ildn -water tip3p
   ```

3. **Handle Force Field Availability**
   - CHARMM36m: Typically available in GROMACS or via CHARMM-GUI
   - AMBER ff19SB: May require AmberTools → ParmEd conversion to GROMACS format
   - Document any modifications or special handling needed

### Tools
- GROMACS `pdb2gmx`
- AmberTools (tleap, ParmEd) if needed for ff19SB
- CHARMM-GUI as alternative for CHARMM36m setup

### Deliverables
- `glycine_charmm.top`, `glycine_charmm.gro`
- `glycine_amber.top`, `glycine_amber.gro`
- `gly-gly_charmm.top`, `gly-gly_charmm.gro`
- `gly-gly_amber.top`, `gly-gly_amber.gro`

---

## Substep 1.3: Build Solvated Boxes with ~50 Molecules

### Objective
Create simulation boxes containing ~50 solute molecules (glycine or Gly-Gly) to achieve ~1 M concentration, solvated with TIP3P water.

### Implementation Steps

1. **Calculate Box Dimensions**
   - Target: 1 M aqueous solution (~50 molecules)
   - Estimate box size for 15,000-20,000 total atoms
   - Typical box size: ~5-6 nm cubic box for this system size

2. **Insert Multiple Molecules**
   ```bash
   # Use gmx insert-molecules to add 50 solute molecules
   gmx insert-molecules -ci glycine_charmm.gro -nmol 50 -box 6 6 6 -o glycine_50mol.gro
   ```

3. **Solvate with TIP3P Water**
   ```bash
   # Add water molecules to fill the box
   gmx solvate -cp glycine_50mol.gro -cs spc216.gro -o glycine_solvated.gro -p glycine_charmm.top
   ```

4. **Verify System Size**
   - Check total atom count is in 15,000-20,000 range
   - Adjust box size if needed to meet target
   - Document actual concentration achieved

5. **Repeat for All Combinations**
   - Glycine + CHARMM36m
   - Glycine + AMBER ff19SB
   - Gly-Gly + CHARMM36m
   - Gly-Gly + AMBER ff19SB

### Tools
- GROMACS `insert-molecules`
- GROMACS `solvate`
- GROMACS `editconf` for box adjustments

### Deliverables
- Solvated structure files (.gro) for all 4 combinations
- Updated topology files (.top) with correct water molecule counts
- System statistics: box dimensions, atom counts, actual concentrations

---

## Substep 1.4: Add Counter-ions and Neutralize Systems

### Objective
Add Na+ and Cl- ions to neutralize the system charge and achieve electroneutrality.

### Implementation Steps

1. **Create Ion Addition MDP File**
   ```mdp
   ; ions.mdp - minimal parameters for ion addition
   integrator  = steep
   nsteps      = 0
   ```

2. **Generate TPR File for Ion Addition**
   ```bash
   gmx grompp -f ions.mdp -c glycine_solvated.gro -p glycine_charmm.top -o ions.tpr
   ```

3. **Add Counter-ions**
   ```bash
   # Add ions to neutralize (replace SOL molecules)
   gmx genion -s ions.tpr -o glycine_neutral.gro -p glycine_charmm.top -pname NA -nname CL -neutral
   ```

4. **Verify Neutrality**
   - Check topology file for ion counts
   - Confirm total charge = 0
   - Document ion numbers added

5. **Repeat for All Systems**
   - All 4 molecule/force-field combinations

### Tools
- GROMACS `grompp`
- GROMACS `genion`

### Deliverables
- Neutralized structure files (.gro) for all 4 combinations
- Final topology files with ion counts
- Charge verification report

---

## Substep 1.5: Energy Minimization

### Objective
Remove steric clashes and relax the initial structure to a local energy minimum.

### Implementation Steps

1. **Create Energy Minimization MDP File**
   ```mdp
   ; em.mdp - steepest descent minimization
   integrator  = steep
   nsteps      = 50000
   emtol       = 1000.0  ; kJ/mol/nm
   emstep      = 0.01    ; nm
   
   cutoff-scheme = Verlet
   nstlist       = 10
   ns_type       = grid
   rlist         = 1.2
   
   coulombtype   = PME
   rcoulomb      = 1.2
   
   vdwtype       = Cut-off
   rvdw          = 1.2
   
   pbc           = xyz
   ```

2. **Run Energy Minimization**
   ```bash
   # Generate TPR file
   gmx grompp -f em.mdp -c glycine_neutral.gro -p glycine_charmm.top -o em.tpr
   
   # Run minimization
   gmx mdrun -v -deffnm em
   ```

3. **Verify Convergence**
   - Check that maximum force < 1000 kJ/mol/nm
   - Plot energy vs. step to confirm convergence
   - Inspect `em.log` for any warnings

4. **Repeat for All Systems**
   - All 4 molecule/force-field combinations at this stage

### Tools
- GROMACS `grompp`, `mdrun`
- Analysis: `gmx energy` for potential energy plotting

### Deliverables
- `em.gro` - minimized structure for each system
- `em.edr` - energy file
- Energy convergence plots
- Verification that all systems converged successfully

---

## Substep 1.6: NVT Equilibration (Temperature Equilibration)

### Objective
Equilibrate the system at target temperature (300 K or 350 K) while keeping volume constant.

### Implementation Steps

1. **Create NVT Equilibration MDP File**
   ```mdp
   ; nvt.mdp - NVT equilibration
   integrator  = md
   dt          = 0.002    ; 2 fs
   nsteps      = 50000    ; 100 ps
   
   tcoupl      = V-rescale
   tc-grps     = Protein Non-Protein  ; or System
   tau_t       = 0.1 0.1
   ref_t       = 300 300  ; or 350 350 for high-T runs
   
   pcoupl      = no
   
   gen_vel     = yes
   gen_temp    = 300  ; or 350
   gen_seed    = -1
   
   cutoff-scheme = Verlet
   nstlist       = 10
   rlist         = 1.2
   
   coulombtype   = PME
   rcoulomb      = 1.2
   
   vdwtype       = Cut-off
   rvdw          = 1.2
   
   pbc           = xyz
   
   constraints   = h-bonds
   constraint_algorithm = LINCS
   ```

2. **Run NVT Equilibration for Both Temperatures**
   ```bash
   # For 300 K
   gmx grompp -f nvt_300K.mdp -c em.gro -p glycine_charmm.top -o nvt_300K.tpr
   gmx mdrun -v -deffnm nvt_300K
   
   # For 350 K
   gmx grompp -f nvt_350K.mdp -c em.gro -p glycine_charmm.top -o nvt_350K.tpr
   gmx mdrun -v -deffnm nvt_350K
   ```

3. **Verify Temperature Equilibration**
   ```bash
   # Extract and plot temperature
   gmx energy -f nvt_300K.edr -o temperature_300K.xvg
   # Select temperature from the menu
   ```
   - Temperature should stabilize around target value
   - Check for reasonable fluctuations (±5-10 K)

4. **Repeat for All Systems**
   - Now expanding to 8 systems: 2 molecules × 2 force fields × 2 temperatures

### Tools
- GROMACS `grompp`, `mdrun`, `energy`
- Plotting tools (xmgrace, Python matplotlib)

### Deliverables
- `nvt_300K.gro` and `nvt_350K.gro` for each molecule/force-field combination
- Temperature equilibration plots
- Verification report for all 8 systems

---

## Substep 1.7: NPT Equilibration (Pressure and Density Equilibration)

### Objective
Equilibrate the system at target pressure (1 bar) to achieve proper density before production runs.

### Implementation Steps

1. **Create NPT Equilibration MDP File**
   ```mdp
   ; npt.mdp - NPT equilibration
   integrator  = md
   dt          = 0.002    ; 2 fs
   nsteps      = 50000    ; 100 ps
   
   tcoupl      = V-rescale
   tc-grps     = Protein Non-Protein
   tau_t       = 0.1 0.1
   ref_t       = 300 300  ; or 350 350
   
   pcoupl      = Parrinello-Rahman
   pcoupltype  = isotropic
   tau_p       = 2.0
   ref_p       = 1.0
   compressibility = 4.5e-5
   
   gen_vel     = no  ; Continue from NVT
   
   cutoff-scheme = Verlet
   nstlist       = 10
   rlist         = 1.2
   
   coulombtype   = PME
   rcoulomb      = 1.2
   
   vdwtype       = Cut-off
   rvdw          = 1.2
   
   pbc           = xyz
   
   constraints   = h-bonds
   constraint_algorithm = LINCS
   ```

2. **Run NPT Equilibration**
   ```bash
   # For 300 K system
   gmx grompp -f npt_300K.mdp -c nvt_300K.gro -p glycine_charmm.top -t nvt_300K.cpt -o npt_300K.tpr
   gmx mdrun -v -deffnm npt_300K
   ```

3. **Verify Pressure and Density Equilibration**
   ```bash
   # Extract pressure
   gmx energy -f npt_300K.edr -o pressure_300K.xvg
   
   # Extract density
   gmx energy -f npt_300K.edr -o density_300K.xvg
   ```
   - Pressure should fluctuate around 1 bar (±100 bar fluctuations normal)
   - Density should stabilize (typical aqueous: ~1000 kg/m³)

4. **Repeat for All 8 Systems**
   - 2 molecules × 2 force fields × 2 temperatures

### Tools
- GROMACS `grompp`, `mdrun`, `energy`
- Plotting tools

### Deliverables
- `npt_300K.gro` and `npt_350K.gro` for each molecule/force-field combination (8 total)
- Pressure equilibration plots
- Density equilibration plots
- Final equilibrated structures ready for production MD

---

## Step 1 Summary and Checklist

### Expected Outputs (8 Fully Prepared Systems)

1. **Glycine + CHARMM36m** at 300 K and 350 K
2. **Glycine + AMBER ff19SB** at 300 K and 350 K
3. **Gly-Gly + CHARMM36m** at 300 K and 350 K
4. **Gly-Gly + AMBER ff19SB** at 300 K and 350 K

### Files per System
- Equilibrated structure: `npt_[temp]K.gro`
- Checkpoint file: `npt_[temp]K.cpt`
- Topology: `system.top`
- All MDP files used
- Equilibration analysis plots (temperature, pressure, density)

### Verification Checklist
- [ ] All systems contain ~50 solute molecules
- [ ] System sizes are 15,000-20,000 atoms
- [ ] All systems are electrically neutral
- [ ] Energy minimization converged (Fmax < 1000 kJ/mol/nm)
- [ ] Temperature equilibration successful (T within ±5 K of target)
- [ ] Pressure equilibration successful (P fluctuating around 1 bar)
- [ ] Density stabilized to reasonable values
- [ ] No warnings or errors in GROMACS log files
- [ ] Documentation complete for all parameter choices

### Directory Structure Recommendation
```
SQUIP/
├── systems/
│   ├── glycine/
│   │   ├── charmm36m/
│   │   │   ├── 300K/
│   │   │   │   ├── initial/
│   │   │   │   ├── minimization/
│   │   │   │   ├── nvt/
│   │   │   │   └── npt/
│   │   │   └── 350K/
│   │   │       └── [same structure]
│   │   └── amber_ff19sb/
│   │       └── [same structure]
│   └── gly-gly/
│       └── [same structure as glycine]
└── scripts/
    ├── build_system.sh
    ├── run_minimization.sh
    ├── run_nvt.sh
    ├── run_npt.sh
    └── verify_equilibration.py
```

### Estimated Time and Resources
- **Walltime**: Each equilibration ~1-2 hours on modern hardware
- **Total for Step 1**: ~16-24 hours for all 8 systems (can be parallelized)
- **Storage**: ~5-10 GB for all equilibration trajectories and files
- **Compute**: Can run on local workstation or small cluster allocation

---

## Next Steps

Once all 8 systems are equilibrated and verified, proceed to:
- **Step 2**: Production MD simulations (10-20 ns with 10 fs sampling)

## Notes and Considerations

1. **Force Field Installation**: Ensure both CHARMM36m and AMBER ff19SB are properly installed in GROMACS or available via conversion tools.

2. **Parallelization**: Systems can be prepared in parallel since they are independent.

3. **Checkpoint Files**: Keep checkpoint files (.cpt) from each equilibration stage for reproducibility and continuation.

4. **Quality Control**: Implement automated checks for equilibration quality before moving to production runs.

5. **Documentation**: Keep detailed notes on any issues encountered and solutions applied for reproducibility.

6. **Trajectory Retention**: Decide whether to keep full equilibration trajectories or just final structures/checkpoints (storage consideration).
