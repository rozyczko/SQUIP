# Steps 1.4-1.7: Theoretical Implementation Plan

## Overview

This document provides a detailed implementation plan for completing the remaining substeps of Step 1: System Preparation. While we cannot execute these steps due to force field topology limitations, this plan documents the exact procedures that would be followed in a production environment.

---

## Substep 1.4: Add Counter-ions and Neutralize Systems

### Objective
Add Na+ and Cl- ions to neutralize the system charge and achieve electroneutrality.

### Prerequisites
- ✅ MDP file created: `mdp/ions.mdp`
- ❌ Proper topology files with force field parameters (currently blocked)
- ✅ Solvated structure files for all 4 combinations

### Implementation Procedure

#### Step 1: Generate TPR Files for Ion Addition

For each of the 4 systems, generate a TPR (run input) file:

```powershell
# Glycine + CHARMM
c:\util\gromacs\bin\gmx.exe grompp -f mdp/ions.mdp -c topologies/glycine_charmm_solvated.gro -p topologies/glycine_charmm.top -o topologies/glycine_charmm_ions.tpr

# Glycine + AMBER
c:\util\gromacs\bin\gmx.exe grompp -f mdp/ions.mdp -c topologies/glycine_amber_solvated.gro -p topologies/glycine_amber.top -o topologies/glycine_amber_ions.tpr

# Gly-Gly + CHARMM
c:\util\gromacs\bin\gmx.exe grompp -f mdp/ions.mdp -c topologies/glygly_charmm_solvated.gro -p topologies/glygly_charmm.top -o topologies/glygly_charmm_ions.tpr

# Gly-Gly + AMBER
c:\util\gromacs\bin\gmx.exe grompp -f mdp/ions.mdp -c topologies/glygly_amber_solvated.gro -p topologies/glygly_amber.top -o topologies/glygly_amber_ions.tpr
```

**Expected Output:**
- 4 TPR files created
- Warnings about using steep integrator with nsteps=0 (expected)
- System information printed (atom counts, box size, etc.)

#### Step 2: Add Counter-ions with genion

For each system, add ions to neutralize charge:

```powershell
# Glycine + CHARMM
# When prompted, select "SOL" (usually option 13 or similar) to replace water molecules
echo 13 | c:\util\gromacs\bin\gmx.exe genion -s topologies/glycine_charmm_ions.tpr -o topologies/glycine_charmm_neutral.gro -p topologies/glycine_charmm.top -pname NA -nname CL -neutral

# Glycine + AMBER
echo 13 | c:\util\gromacs\bin\gmx.exe genion -s topologies/glycine_amber_ions.tpr -o topologies/glycine_amber_neutral.gro -p topologies/glycine_amber.top -pname NA -nname CL -neutral

# Gly-Gly + CHARMM
echo 13 | c:\util\gromacs\bin\gmx.exe genion -s topologies/glygly_charmm_ions.tpr -o topologies/glygly_charmm_neutral.gro -p topologies/glygly_charmm.top -pname NA -nname CL -neutral

# Gly-Gly + AMBER
echo 13 | c:\util\gromacs\bin\gmx.exe genion -s topologies/glygly_amber_ions.tpr -o topologies/glygly_amber_neutral.gro -p topologies/glygly_amber.top -pname NA -nname CL -neutral
```

**Expected Ion Counts:**
Based on our simplified topologies (total charge ~-0.85 per GLY molecule):
- Glycine systems: ~42-43 Na+ ions needed (50 molecules × 0.85)
- Gly-Gly systems: Similar, depending on exact charge

**Files Created:**
- `*_neutral.gro` - Neutralized structure files
- Topology files automatically updated with ion counts

#### Step 3: Verify Neutrality

Create verification script:

```python
def verify_neutrality(top_file):
    """Parse topology and verify total charge = 0"""
    # Parse [ atoms ] section to sum charges
    # Parse [ molecules ] section to count each molecule type
    # Calculate: total_charge = sum(n_molecules × charge_per_molecule)
    # Assert: abs(total_charge) < 0.001
```

Run for all 4 systems and confirm electroneutrality.

### Deliverables (Theoretical)
- 4 neutralized structure files (`*_neutral.gro`)
- 4 updated topology files with ion counts
- Verification report confirming total charge = 0 for all systems

---

## Substep 1.5: Energy Minimization

### Objective
Remove steric clashes and relax the initial structure to a local energy minimum.

### MDP File: `mdp/em.mdp`

```
; em.mdp - Steepest descent energy minimization
; Used to relax the system and remove bad contacts

integrator  = steep         ; Steepest descent minimization
nsteps      = 50000         ; Maximum number of minimization steps
emtol       = 1000.0        ; Stop when max force < 1000 kJ/mol/nm
emstep      = 0.01          ; Initial step size (nm)

; Output control
nstlog      = 100           ; Frequency to write to log file
nstenergy   = 100           ; Frequency to write energies

; Neighbor searching
cutoff-scheme = Verlet
nstlist     = 10            ; Frequency to update neighbor list
ns_type     = grid
rlist       = 1.2           ; Cutoff for short-range neighbor list (nm)

; Electrostatics
coulombtype = PME           ; Particle Mesh Ewald for long-range
rcoulomb    = 1.2           ; Coulomb cutoff (nm)
pme_order   = 4             ; Cubic interpolation
fourierspacing = 0.12       ; Grid spacing for FFT

; Van der Waals
vdwtype     = Cut-off
rvdw        = 1.2           ; VdW cutoff (nm)

; Periodic boundary conditions
pbc         = xyz           ; 3D periodic boundary conditions
```

### Implementation

```powershell
# For each system:
# 1. Generate TPR file
# 2. Run minimization
# 3. Check convergence

# Glycine + CHARMM
c:\util\gromacs\bin\gmx.exe grompp -f mdp/em.mdp -c topologies/glycine_charmm_neutral.gro -p topologies/glycine_charmm.top -o em/glycine_charmm_em.tpr
c:\util\gromacs\bin\gmx.exe mdrun -v -deffnm em/glycine_charmm_em

# Glycine + AMBER
c:\util\gromacs\bin\gmx.exe grompp -f mdp/em.mdp -c topologies/glycine_amber_neutral.gro -p topologies/glycine_amber.top -o em/glycine_amber_em.tpr
c:\util\gromacs\bin\gmx.exe mdrun -v -deffnm em/glycine_amber_em

# Gly-Gly + CHARMM
c:\util\gromacs\bin\gmx.exe grompp -f mdp/em.mdp -c topologies/glygly_charmm_neutral.gro -p topologies/glygly_charmm.top -o em/glygly_charmm_em.tpr
c:\util\gromacs\bin\gmx.exe mdrun -v -deffnm em/glygly_charmm_em

# Gly-Gly + AMBER
c:\util\gromacs\bin\gmx.exe grompp -f mdp/em.mdp -c topologies/glygly_amber_neutral.gro -p topologies/glygly_amber.top -o em/glygly_amber_em.tpr
c:\util\gromacs\bin\gmx.exe mdrun -v -deffnm em/glygly_amber_em
```

### Verification

```powershell
# Extract potential energy for each system
c:\util\gromacs\bin\gmx.exe energy -f em/glycine_charmm_em.edr -o em/glycine_charmm_potential.xvg
# Select "Potential" from menu (option 10)

# Check final maximum force in log file
Get-Content em/glycine_charmm_em.log | Select-String "Fmax"
```

**Success Criteria:**
- Maximum force (Fmax) < 1000 kJ/mol/nm
- Potential energy decreases monotonically
- "converged to Fmax" message in log
- Typically converges in 1,000-5,000 steps for well-solvated systems

### Deliverables (Theoretical)
- 4 minimized structures (`*_em.gro`)
- 4 energy files (`*_em.edr`)
- Energy vs step plots showing convergence
- Log files confirming Fmax < 1000 kJ/mol/nm

**Estimated Runtime:** ~1-2 hours total (30 minutes per system on modern hardware)

---

## Substep 1.6: NVT Equilibration (Temperature Equilibration)

### Objective
Equilibrate the system at target temperature (300 K or 350 K) while keeping volume constant.

### MDP Files

#### `mdp/nvt_300K.mdp`

```
; nvt_300K.mdp - NVT equilibration at 300 K
; Constant Number, Volume, and Temperature

integrator  = md            ; Leap-frog MD
dt          = 0.002         ; 2 fs time step
nsteps      = 50000         ; 100 ps (50000 * 0.002)

; Output control
nstlog      = 500           ; Log every 1 ps
nstenergy   = 500           ; Energy every 1 ps
nstxout-compressed = 1000   ; Coordinates every 2 ps

; Neighbor searching
cutoff-scheme = Verlet
nstlist     = 10
rlist       = 1.2

; Electrostatics
coulombtype = PME
rcoulomb    = 1.2
pme_order   = 4
fourierspacing = 0.12

; Van der Waals
vdwtype     = Cut-off
rvdw        = 1.2

; Temperature coupling
tcoupl      = V-rescale     ; Modified Berendsen thermostat
tc-grps     = System        ; Single coupling group
tau_t       = 0.1           ; Time constant (ps)
ref_t       = 300           ; Target temperature (K)

; Pressure coupling
pcoupl      = no            ; No pressure coupling in NVT

; Velocity generation
gen_vel     = yes           ; Generate velocities
gen_temp    = 300           ; Generate at 300 K
gen_seed    = -1            ; Random seed

; Periodic boundary conditions
pbc         = xyz

; Constraints
constraints = h-bonds       ; Constrain H-bonds
constraint_algorithm = LINCS
```

#### `mdp/nvt_350K.mdp`

Same as above but with:
```
ref_t       = 350           ; Target temperature (K)
gen_temp    = 350           ; Generate at 350 K
```

### Implementation

Now we expand to 8 systems (4 base systems × 2 temperatures):

```powershell
# Glycine + CHARMM at 300K
c:\util\gromacs\bin\gmx.exe grompp -f mdp/nvt_300K.mdp -c em/glycine_charmm_em.gro -p topologies/glycine_charmm.top -o nvt/glycine_charmm_300K_nvt.tpr
c:\util\gromacs\bin\gmx.exe mdrun -v -deffnm nvt/glycine_charmm_300K_nvt

# Glycine + CHARMM at 350K
c:\util\gromacs\bin\gmx.exe grompp -f mdp/nvt_350K.mdp -c em/glycine_charmm_em.gro -p topologies/glycine_charmm.top -o nvt/glycine_charmm_350K_nvt.tpr
c:\util\gromacs\bin\gmx.exe mdrun -v -deffnm nvt/glycine_charmm_350K_nvt

# [Repeat for other 3 base systems at both temperatures]
```

### Verification

```powershell
# Extract temperature for each system
c:\util\gromacs\bin\gmx.exe energy -f nvt/glycine_charmm_300K_nvt.edr -o nvt/glycine_charmm_300K_temperature.xvg
# Select "Temperature" from menu

# Plot and verify:
# - Temperature stabilizes around target (300 K or 350 K)
# - Fluctuations are ±5-10 K (normal for ~16,000 atoms)
# - No drift over the 100 ps equilibration
```

**Success Criteria:**
- Average temperature within ±2 K of target
- Temperature plot shows stabilization (not continuous drift)
- System energy equilibrates (not continuously increasing/decreasing)

### Deliverables (Theoretical)
- 8 NVT-equilibrated structures (`*_nvt.gro`)
- 8 checkpoint files (`*_nvt.cpt`) for continuing to NPT
- 8 energy files (`*_nvt.edr`)
- Temperature vs time plots for all 8 systems
- Verification report confirming temperature equilibration

**Estimated Runtime:** ~4 hours total (30 minutes per system on modern hardware)

---

## Substep 1.7: NPT Equilibration (Pressure and Density Equilibration)

### Objective
Equilibrate the system at target pressure (1 bar) to achieve proper density before production runs.

### MDP Files

#### `mdp/npt_300K.mdp`

```
; npt_300K.mdp - NPT equilibration at 300 K and 1 bar
; Constant Number, Pressure, and Temperature

integrator  = md
dt          = 0.002
nsteps      = 50000         ; 100 ps

; Output control
nstlog      = 500
nstenergy   = 500
nstxout-compressed = 1000

; Neighbor searching
cutoff-scheme = Verlet
nstlist     = 10
rlist       = 1.2

; Electrostatics
coulombtype = PME
rcoulomb    = 1.2
pme_order   = 4
fourierspacing = 0.12

; Van der Waals
vdwtype     = Cut-off
rvdw        = 1.2

; Temperature coupling
tcoupl      = V-rescale
tc-grps     = System
tau_t       = 0.1
ref_t       = 300

; Pressure coupling
pcoupl      = Parrinello-Rahman    ; Barostat
pcoupltype  = isotropic            ; Uniform scaling
tau_p       = 2.0                  ; Time constant (ps)
ref_p       = 1.0                  ; Target pressure (bar)
compressibility = 4.5e-5           ; Water compressibility (bar^-1)

; Velocity generation
gen_vel     = no            ; Continue from NVT

; Periodic boundary conditions
pbc         = xyz

; Constraints
constraints = h-bonds
constraint_algorithm = LINCS
```

#### `mdp/npt_350K.mdp`

Same as above but with `ref_t = 350`

### Implementation

```powershell
# For each of the 8 systems:
# Use -t flag to continue from NVT checkpoint

# Glycine + CHARMM at 300K
c:\util\gromacs\bin\gmx.exe grompp -f mdp/npt_300K.mdp -c nvt/glycine_charmm_300K_nvt.gro -t nvt/glycine_charmm_300K_nvt.cpt -p topologies/glycine_charmm.top -o npt/glycine_charmm_300K_npt.tpr
c:\util\gromacs\bin\gmx.exe mdrun -v -deffnm npt/glycine_charmm_300K_npt

# Glycine + CHARMM at 350K
c:\util\gromacs\bin\gmx.exe grompp -f mdp/npt_350K.mdp -c nvt/glycine_charmm_350K_nvt.gro -t nvt/glycine_charmm_350K_nvt.cpt -p topologies/glycine_charmm.top -o npt/glycine_charmm_350K_npt.tpr
c:\util\gromacs\bin\gmx.exe mdrun -v -deffnm npt/glycine_charmm_350K_npt

# [Repeat for other 6 systems]
```

### Verification

```powershell
# Extract pressure for each system
c:\util\gromacs\bin\gmx.exe energy -f npt/glycine_charmm_300K_npt.edr -o npt/glycine_charmm_300K_pressure.xvg
# Select "Pressure"

# Extract density
c:\util\gromacs\bin\gmx.exe energy -f npt/glycine_charmm_300K_npt.edr -o npt/glycine_charmm_300K_density.xvg
# Select "Density"
```

**Success Criteria:**
- Average pressure: 1.0 ± 0.5 bar (large fluctuations ±50-100 bar are normal)
- Density stabilizes around 1000-1050 kg/m³ for aqueous systems
- Box volume shows small fluctuations around equilibrium value
- No continuous drift in density

**Expected Densities:**
- 300 K systems: ~1000-1010 kg/m³
- 350 K systems: ~970-990 kg/m³ (density decreases with temperature)

### Deliverables (Theoretical)
- 8 fully equilibrated structures (`*_npt.gro`) **← READY FOR PRODUCTION MD**
- 8 checkpoint files (`*_npt.cpt`)
- 8 energy files (`*_npt.edr`)
- Pressure vs time plots for all 8 systems
- Density vs time plots for all 8 systems
- Box volume vs time plots
- Final verification report

**Estimated Runtime:** ~4 hours total (30 minutes per system)

---

## Final Step 1 Summary

### Complete System Inventory

After completing all substeps, you would have 8 fully prepared systems:

| System | Force Field | Temperature | Atoms | Status |
|--------|-------------|-------------|-------|--------|
| Glycine | CHARMM27 | 300 K | ~15,850 | Ready for Production |
| Glycine | CHARMM27 | 350 K | ~15,850 | Ready for Production |
| Glycine | AMBER99SB-ILDN | 300 K | ~15,865 | Ready for Production |
| Glycine | AMBER99SB-ILDN | 350 K | ~15,865 | Ready for Production |
| Gly-Gly | CHARMM27 | 300 K | ~15,860 | Ready for Production |
| Gly-Gly | CHARMM27 | 350 K | ~15,860 | Ready for Production |
| Gly-Gly | AMBER99SB-ILDN | 300 K | ~15,845 | Ready for Production |
| Gly-Gly | AMBER99SB-ILDN | 350 K | ~15,845 | Ready for Production |

### Directory Structure

```
SQUIP/
├── structures/
│   ├── glycine_zw.pdb
│   └── GlyGly_zw.pdb
├── topologies/
│   ├── glycine_charmm.top
│   ├── glycine_amber.top
│   ├── glygly_charmm.top
│   ├── glygly_amber.top
│   ├── *_neutral.gro
│   └── *_solvated.gro
├── mdp/
│   ├── ions.mdp
│   ├── em.mdp
│   ├── nvt_300K.mdp
│   ├── nvt_350K.mdp
│   ├── npt_300K.mdp
│   └── npt_350K.mdp
├── em/
│   ├── *_em.gro
│   ├── *_em.edr
│   └── *_em.log
├── nvt/
│   ├── *_nvt.gro
│   ├── *_nvt.cpt
│   └── *_nvt.edr
├── npt/
│   ├── *_npt.gro  ← PRODUCTION READY
│   ├── *_npt.cpt
│   └── *_npt.edr
└── analysis/
    ├── temperature_plots/
    ├── pressure_plots/
    ├── density_plots/
    └── verification_report.md
```

### Verification Checklist

Before proceeding to Step 2 (Production MD), verify:

- [ ] All 8 systems have converged energy minimization (Fmax < 1000)
- [ ] All 8 systems have stable temperature (within ±2 K of target)
- [ ] All 8 systems have stable pressure (average ~1 bar)
- [ ] All 8 systems have stable density (no drift over last 50 ps)
- [ ] All systems are electrically neutral (total charge = 0)
- [ ] All topology files are consistent with structure files
- [ ] All checkpoint files are present for production continuation
- [ ] No errors or warnings in any log files

### Total Time and Resources

**Computational Time:**
- Energy minimization: ~2 hours (4 systems)
- NVT equilibration: ~4 hours (8 systems)
- NPT equilibration: ~4 hours (8 systems)
- **Total: ~10 hours** (can be parallelized if resources available)

**Storage:**
- Structures: ~50 MB
- Trajectories (if saved): ~5-10 GB
- Energy files: ~100 MB
- Total: ~10-11 GB

**Human Time:**
- Setup and monitoring: ~3-4 hours
- Analysis and verification: ~2-3 hours
- **Total: ~6-7 hours**

---

## Next Steps: Step 2 - Production MD

Once all 8 systems are equilibrated, they would be ready for:

**Step 2: Production MD Simulations (10-20 ns)**
- Duration: 10-20 ns per system
- Trajectory saving: Every 10 fs (critical for QENS-relevant timescales)
- Ensemble: NPT
- Total simulation time: 80-160 ns across all 8 systems

See STEP1.md for the complete workflow plan.

---

## Conclusion

This theoretical implementation plan demonstrates that the SQUIP workflow is:
- **Technically sound** - Standard GROMACS procedures
- **Computationally feasible** - ~10 hours for equilibration
- **Properly scaled** - Systems in 15,000-20,000 atom range
- **Well-structured** - Clear progression through equilibration stages

The only barrier to execution is obtaining proper force field topology files, which in production would be generated using:
1. CHARMM-GUI (recommended)
2. Proper pdb2gmx with correctly formatted PDB files
3. Manual topology building tools

The methodology and system parameters documented here directly inform the full SQUIP implementation.
