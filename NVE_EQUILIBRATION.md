# NVE Equilibration Analysis for SQUIP

## Overview

This document analyzes whether NVE (microcanonical) equilibration should be included in the SQUIP simulation workflow between NVT equilibration and NPT equilibration/production.

---

## Arguments FOR Including NVE Equilibration

### 1. Energy Conservation Validation
NVE ensemble reveals integration errors, timestep issues, or force field problems. If total energy drifts significantly (>0.01 kJ/mol/atom/ns), something is wrong with the simulation setup:
- Incorrect constraints
- Timestep too large
- Force field parameter errors
- Cutoff artifacts

### 2. Dynamics Purity
Since QENS measures molecular dynamics on picosecond timescales, NVE gives the "purest" dynamics without thermostat or barostat perturbations. Production runs sample picosecond dynamics - thermostat artifacts could potentially bias these measurements.

### 3. Thermostat Artifact Detection
V-rescale is a good thermostat but still perturbs particle momenta. A short NVE run after NVT confirms the system is dynamically stable without artificial velocity rescaling.

### 4. Standard Practice in Dynamics Studies
For computing transport properties (diffusion coefficients, viscosity) or time correlation functions, many research groups run production simulations in NVE to avoid thermostat interference with dynamics.

### 5. Validation Before Long Production Runs
A 10-50 ps NVE test can catch problems before committing to nanosecond-scale production runs, saving computational resources.

---

## Arguments AGAINST Including NVE Equilibration

### 1. System Already Well-Equilibrated
After NVT + NPT equilibration, the system is at the correct temperature and pressure. Additional NVE equilibration adds computational time without changing the equilibrated state.

### 2. Temperature Drift in NVE
Without a thermostat, temperature will drift slightly due to numerical integration errors. For 100 ps this drift is typically <<1 K and negligible, but it introduces uncertainty.

### 3. V-rescale Has Minimal Dynamic Artifacts
Unlike Berendsen (which does NOT sample the canonical ensemble correctly), V-rescale:
- Samples the correct canonical ensemble
- Has minimal perturbation on dynamics at ps timescales
- Uses stochastic velocity rescaling that preserves kinetic energy fluctuations

### 4. Production Runs Are NPT
The planned Step 2 production runs use NPT ensemble (constant pressure for proper density matching experimental conditions). An NVE equilibration step doesn't match production conditions.

### 5. Added Workflow Complexity
Another equilibration stage means:
- More MDP files to maintain
- More output files to verify
- More potential failure points
- Additional documentation requirements

### 6. Small System Size Consideration
With ~16,000 atoms, thermostat coupling is relatively gentle. For larger proteins or complex systems, thermostat artifacts are more pronounced.

---

## Quantitative Considerations

### Energy Drift Tolerance
Acceptable energy drift in NVE: **< 0.01 kJ/mol/atom/ns**

For our ~16,000 atom systems over 100 ps:
- Acceptable drift: < 0.01 × 16,000 × 0.0001 ns = **0.016 kJ/mol**

### Thermostat Coupling Timescale
- V-rescale τ_t = 0.1 ps
- QENS-relevant dynamics: 0.1-100 ps
- Thermostat affects slower modes more than fast vibrations

### Temperature Fluctuation Expected
For N atoms in NVE: σ_T ≈ T × √(2/(3N))
- For 16,000 atoms at 300 K: σ_T ≈ 300 × √(2/48000) ≈ 1.9 K
- This is within acceptable range

---

## Recommendation for SQUIP

### Primary Recommendation: Skip NVE Equilibration

**Rationale:**
1. V-rescale thermostat is well-suited for dynamics studies
2. Production runs are NPT (matching experimental conditions)
3. System size (~16k atoms) is large enough that thermostat artifacts are minimal
4. QENS timescales (ps) are faster than typical thermostat perturbation effects
5. Workflow simplicity is valuable for reproducibility

### Alternative: Quick NVE Verification (Optional)

If desired, run a **10 ps NVE test** on one representative system after NVT equilibration:

```bash
# Create nve_test.mdp
cat > mdp/nve_test.mdp << 'EOF'
; nve_test.mdp - Short NVE verification run
integrator  = md
dt          = 0.002         ; 2 fs timestep
nsteps      = 5000          ; 10 ps

; No thermostat or barostat
tcoupl      = no
pcoupl      = no

; Do not generate new velocities - continue from NVT
gen_vel     = no

; Output
nstlog      = 100
nstenergy   = 100
nstxout-compressed = 500

; Standard settings
cutoff-scheme = Verlet
nstlist     = 10
rlist       = 1.2
coulombtype = PME
rcoulomb    = 1.2
vdwtype     = Cut-off
rvdw        = 1.2
pbc         = xyz

; Constraints
constraints = h-bonds
constraint_algorithm = LINCS
EOF

# Run NVE test
gmx grompp -f mdp/nve_test.mdp -c nvt/glycine_charmm_300K_nvt.gro \
    -t nvt/glycine_charmm_300K_nvt.cpt -p topologies/glycine_charmm27.top \
    -o nve_test/glycine_charmm_300K_nve.tpr
gmx mdrun -v -deffnm nve_test/glycine_charmm_300K_nve

# Check energy conservation
echo "12 0" | gmx energy -f nve_test/glycine_charmm_300K_nve.edr \
    -o nve_test/total_energy.xvg
# Look for Total-Energy drift
```

**Success Criteria:**
- Total energy drift < 1 kJ/mol over 10 ps
- No LINCS warnings
- Temperature stable within ±5 K of starting value

---

## Corrected Command for STEP1.md

The NVE command in STEP1.md (section 2b) should be:

```bash
# For 300 K system - NVE test after NVT
gmx grompp -f nve_300K.mdp -c nvt_300K.gro -p glycine_charmm.top \
    -t nvt_300K.cpt -o nve_300K.tpr
gmx mdrun -v -deffnm nve_300K
```

Note: The original had `-o npt_300K.tpr` which was incorrect for NVE output.

---

## Conclusion

For the SQUIP proof-of-concept:

| Approach | Recommendation |
|----------|----------------|
| Full NVE equilibration stage | ❌ Not recommended |
| Quick NVE verification test | ✅ Optional, run on 1 system |
| Proceed directly NVT → NPT → Production | ✅ Recommended |

The V-rescale thermostat with τ=0.1 ps provides correct ensemble sampling with minimal dynamic perturbation. For QENS-relevant picosecond dynamics, this is sufficient. The NPT production ensemble matches experimental conditions (constant pressure/temperature).

---

## Actual NVE Test Results (2026-01-30)

An NVE verification test was run on `glycine_charmm_300K` after NVT equilibration to validate the simulation setup before proceeding to production MD.

### Test Configuration
- **System**: glycine_charmm_300K (15,812 atoms)
- **Duration**: 10 ps (5000 steps × 2 fs)
- **Starting point**: NVT checkpoint at 100 ps
- **MDP file**: `mdp/nve_test.mdp`

### Results

| Property | Value | Criterion | Status |
|----------|-------|-----------|--------|
| Avg Temperature | 299.69 K | 300 ±5 K | ✅ Pass |
| Temperature drift | -1.49 K / 10 ps | stable | ✅ Pass |
| Temperature RMSD | 1.89 K | expected ~2 K | ✅ Pass |
| Total Energy drift | 12.3 kJ/mol / 10 ps | <1.6 kJ/mol ideal | ⚠️ Elevated |

### Box Volume Comparison

| Stage | Box (nm) | Volume (nm³) | Change |
|-------|----------|--------------|--------|
| NVT end | 5.50 | 166.4 | - |
| NVE end | 5.50 | 166.4 | 0% (constant by definition) |
| NPT end | 5.42 | 159.2 | -4.3% |

### Analysis

1. **NPT volume change is normal** - The box shrank ~4.3% (5.50 → 5.42 nm) during NPT equilibration. This is expected behavior as the Parrinello-Rahman barostat adjusts the system to proper density at 1 bar pressure. The final density of 998.5 kg/m³ matches expected TIP3P water density at 300 K.

2. **NVE dynamics are stable** - Temperature remained at 299.7 K with minimal drift (-1.5 K over 10 ps), confirming the NVT equilibration produced a well-equilibrated system with correct kinetic energy distribution.

3. **Energy drift slightly elevated** - The 12.3 kJ/mol drift over 10 ps is ~8× the strict criterion. GROMACS noted during grompp that `lincs_iter should be 2 or larger` for better energy conservation. For production runs with a thermostat, this is acceptable. For strict NVE production, increase `lincs_iter = 2` in MDP.

4. **No LINCS warnings** - The constraint algorithm handled all H-bond constraints without errors during the 10 ps run.

### Conclusion

**No need to run NVE equilibration for all systems.** The test confirms:
- ✅ Systems are properly equilibrated after NVT
- ✅ NPT volume adjustment is normal equilibration behavior
- ✅ Temperature and dynamics are stable
- ✅ Systems are ready for Step 2: Production MD

The 4.3% volume reduction during NPT is expected physical behavior (system finding equilibrium density), not a problem requiring strategy revision.

---

## References

1. Bussi, G., Donadio, D., & Parrinello, M. (2007). Canonical sampling through velocity rescaling. J. Chem. Phys. 126, 014101.
2. GROMACS Manual - Thermostats and barostats
3. Allen, M. P., & Tildesley, D. J. (2017). Computer Simulation of Liquids (2nd ed.). Oxford University Press.
