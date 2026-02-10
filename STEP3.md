# Step 3: S(q,ω) Calculation with Dynasor - Implementation Plan

## Overview
This document provides a detailed implementation plan for **Step 3: S(q,ω) Calculation** from the SQUIP Proof of Concept workflow. The goal is to compute dynamic structure factors S(q,ω) from the production MD trajectories generated in Step 2 using the **Dynasor** library, enabling direct comparison with experimental QENS (Quasi-Elastic Neutron Scattering) data.

**Timeline**: Week 3-4  
**Input**: 8 production trajectories from Step 2 (20 ns each, 30 fs resolution)  
**Output**: S(q,ω) datasets, intermediate scattering functions F(q,t), linewidth analysis Γ(q), and comparison-ready spectra for all 8 systems

---

## Prerequisites

### Completed Systems from Step 2

| System | Force Field | Water Model | Temperature | Trajectory | Status |
|--------|-------------|-------------|-------------|------------|--------|
| Glycine | AMBER99SB-ILDN | TIP4P-Ew | 300 K | 20 ns @ 30 fs | ✅ Ready |
| Glycine | AMBER99SB-ILDN | TIP4P-Ew | 350 K | 20 ns @ 30 fs | ✅ Ready |
| Glycine | CHARMM27 | TIP3P | 300 K | 20 ns @ 30 fs | ✅ Ready |
| Glycine | CHARMM27 | TIP3P | 350 K | 20 ns @ 30 fs | ✅ Ready |
| Gly-Gly | AMBER99SB-ILDN | TIP4P-Ew | 300 K | 20 ns @ 30 fs | ✅ Ready |
| Gly-Gly | AMBER99SB-ILDN | TIP4P-Ew | 350 K | 20 ns @ 30 fs | ✅ Ready |
| Gly-Gly | CHARMM27 | TIP3P | 300 K | 20 ns @ 30 fs | ✅ Ready |
| Gly-Gly | CHARMM27 | TIP3P | 350 K | 20 ns @ 30 fs | ✅ Ready |

### Input Files Required (per system)

- `systems/{molecule}/{forcefield}/{temp}K/production/prod.xtc` — Production trajectory (30 fs resolution)
- `systems/{molecule}/{forcefield}/{temp}K/production/prod.tpr` — Run input (topology + parameters)
- `systems/{molecule}/{forcefield}/{temp}K/production/prod_center.xtc` — Centered, PBC-corrected trajectory
- `systems/{molecule}/{forcefield}/{temp}K/production/index.ndx` — Index file with atom groups

### System Specifications

| Property | AMBER (TIP4P-Ew) | CHARMM (TIP3P) |
|----------|------------------|----------------|
| Solute molecules | 50 | 50 |
| Total atoms | ~20,500-21,000 | ~15,500-16,500 |
| Box size | ~5.4 nm | ~5.4 nm |
| Trajectory frames | ~666,667 | ~666,667 |
| Frame interval | 30 fs (0.030 ps) | 30 fs (0.030 ps) |
| Trajectory length | 20 ns | 20 ns |

---

## Key Concepts for QENS Analysis

### Why Dynasor?

Dynasor computes total and partial dynamic structure factors S(q,ω) and intermediate scattering functions F(q,t) directly from MD trajectories. It supports:

- **Coherent and incoherent** dynamic structure factors
- **Multi-component systems** with partial correlation functions
- **Spherical q-point averaging** (ideal for isotropic liquid systems)
- **Neutron scattering length weighting** for direct QENS comparison
- **MDAnalysis-based trajectory reading** (supports GROMACS .xtc/.gro)

### Critical Limitation: Constant-Volume Trajectories

> **Important**: Dynasor requires **constant-volume** (NVT or NVE) trajectories. The concept of q-points becomes ambiguous if the simulation box changes (as in NPT simulations). Since our production runs use NPT ensemble, we must either:
> 1. Use the trajectory as-is (box fluctuations are typically < 0.1% for well-equilibrated aqueous systems and the effect is negligible)
> 2. Re-image the trajectory to a fixed reference box using `gmx trjconv`
>
> For the PoC, option 1 is acceptable given small box fluctuations. For publication-quality results, consider running short NVT production segments or re-imaging.

### QENS-Relevant Physics

- **Incoherent scattering**: Dominated by hydrogen atoms (σ_inc(H) = 80.27 barn >> σ_inc(other))
- **q-range**: 0.3–2.0 Å⁻¹ (typical backscattering/time-of-flight QENS instruments)
- **Energy transfers**: ±2 meV (quasielastic region — diffusion, rotations)
- **Timescales probed**: ~0.1–100 ps (diffusion, rotational relaxation, librations)

### Dynasor Units and Conventions

| Quantity | Dynasor Internal Unit | Conversion |
|----------|----------------------|------------|
| Length | Å | 1 nm = 10 Å |
| Time | fs | 1 ps = 1000 fs |
| q-points | rad/Å (Cartesian) | includes 2π factor |
| Angular frequency ω | rad/fs | × 658.21 → meV |
| Energy | meV (after conversion) | 1 meV = 0.2418 THz |

---

## Substep 3.1: Install Dynasor and Dependencies

### Objective
Set up the Python environment with Dynasor and all required analysis libraries.

### Implementation Steps

1. **Install Dynasor via pip or conda**
   ```bash
   # Option A: pip (recommended)
   pip install dynasor

   # Option B: conda-forge
   conda install -c conda-forge dynasor
   ```

2. **Install Additional Dependencies**
   ```bash
   pip install MDAnalysis    # For GROMACS trajectory reading
   pip install h5py          # For HDF5 output
   pip install scipy         # For fitting and signal processing
   pip install matplotlib    # For visualization
   ```

3. **Verify Installation**
   ```python
   import dynasor
   print(f"Dynasor version: {dynasor.__version__}")

   from dynasor import Trajectory, compute_dynamic_structure_factors
   from dynasor.qpoints import get_spherical_qpoints
   from dynasor.post_processing import (
       get_spherically_averaged_sample_binned,
       get_weighted_sample,
       NeutronScatteringLengths,
   )
   from dynasor.units import radians_per_fs_to_meV
   print("All imports successful")
   ```

4. **Verify MDAnalysis Can Read GROMACS Trajectories**
   ```python
   import MDAnalysis as mda

   # Quick test with one trajectory
   u = mda.Universe(
       'systems/glycine/amber99sb/300K/production/prod.tpr',
       'systems/glycine/amber99sb/300K/production/prod_center.xtc'
   )
   print(f"Atoms: {u.atoms.n_atoms}")
   print(f"Frames: {u.trajectory.n_frames}")
   print(f"Timestep: {u.trajectory.dt} ps")
   print(f"Box: {u.dimensions[:3]} Å")
   ```

### Deliverables
- Working Python environment with Dynasor ≥ 2.0
- Verified trajectory reading from GROMACS .xtc files
- `requirements.txt` updated with analysis dependencies

---

## Substep 3.2: Prepare Trajectories for Dynasor

### Objective
Convert production trajectories into a format and subset suitable for efficient Dynasor processing.

### Implementation Steps

1. **Create NVT-like Trajectory from NPT (Re-image to Fixed Box)**

   Since Dynasor requires constant-volume trajectories, re-image to the average box dimensions:

   ```bash
   # For each system, extract the average box from the trajectory
   # Then re-image to a fixed box using trjconv

   # Step 1: Get average box dimensions from production run
   echo "0" | gmx trjconv -f prod_center.xtc -s prod.tpr \
       -o prod_nvt_reimage.xtc -pbc mol -ur compact

   # Alternative: Use the first frame's box (NPT fluctuations are small)
   # The box size variation is typically < 0.1% for well-equilibrated systems
   ```

2. **Create GROMACS Index File for Atom Type Grouping**

   Dynasor needs atom type information to compute partial structure factors. Create an index file mapping atoms to element types:

   ```bash
   cd systems/glycine/amber99sb/300K/production

   # Create index groups by element type for Dynasor
   # Select hydrogen, carbon, nitrogen, oxygen separately
   cat > make_index.sh << 'SCRIPT'
   echo -e "a H*\nname 1 H\na C*\nname 2 C\na N*\nname 3 N\na O*\nname 4 O\nq" | \
       gmx make_ndx -f prod.tpr -o dynasor_elements.ndx
   SCRIPT
   bash make_index.sh
   ```

3. **Create Analysis-Ready Subtrajectories (if memory-limited)**

   For large trajectories, process in chunks:

   ```bash
   # Extract shorter windows for initial testing (e.g., first 1 ns)
   echo "0" | gmx trjconv -f prod_center.xtc -s prod.tpr \
       -o prod_test_1ns.xtc -e 1000  # 0 to 1000 ps

   # Extract 5 ns windows for production analysis
   for i in 0 1 2 3; do
       b=$((i * 5000))
       e=$(((i + 1) * 5000))
       echo "0" | gmx trjconv -f prod_center.xtc -s prod.tpr \
           -o prod_window_${i}.xtc -b $b -e $e
   done
   ```

4. **Extract First-Frame GRO for Reference Structure**

   Dynasor needs a reference structure (for the cell metric):

   ```bash
   echo "0" | gmx trjconv -f prod_center.xtc -s prod.tpr \
       -o prod_frame0.gro -dump 0
   ```

### Deliverables (per system)
- `dynasor_elements.ndx` — Index file with element-based atom groups
- `prod_frame0.gro` — Reference structure with box dimensions
- `prod_test_1ns.xtc` — Short test trajectory for initial validation
- `prod_window_{0-3}.xtc` — 5 ns analysis windows (optional)

---

## Substep 3.3: Compute Dynamic Structure Factors

### Objective
Calculate S(q,ω) and F(q,t) for all 8 systems using Dynasor, including both coherent and incoherent contributions.

### Key Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `q_max` | 2.5 rad/Å | Covers QENS range 0.3–2.0 Å⁻¹ with margin |
| `q_min` | 0.0 rad/Å | Include smallest accessible q |
| `max_points` | 5000 | Sufficient q-point sampling for spherical average |
| `dt` | 30 fs | Matches trajectory output frequency |
| `window_size` | 2000 | 60 ps time window → Δω ≈ 0.07 meV resolution |
| `window_step` | 200 | Step windows by 6 ps for good statistics |
| `calculate_incoherent` | `True` | Essential for QENS comparison (H dominates) |

### Parameter Rationale

**Window size (2000 frames = 60 ps)**:
- Frequency resolution: Δω = 2π / (window_size × dt) = 2π / (60000 fs) ≈ 1.047 × 10⁻⁴ rad/fs ≈ **0.069 meV**
- Maximum resolved frequency: ω_max = π / dt = π / 30 fs ≈ 0.1047 rad/fs ≈ **68.9 meV** (Nyquist)
- Suitable for resolving quasielastic linewidths Γ ~ 0.01–1 meV (diffusion, rotations)

**Number of windows**:
- Total frames: ~666,667 (20 ns / 30 fs)
- Windows: (666,667 − 2000) / 200 ≈ 3,323 overlapping windows
- Excellent averaging for converged correlation functions

### Implementation Steps

1. **Create the Main Analysis Script**

   ```python
   #!/usr/bin/env python3
   """
   compute_sqw.py - Compute S(q,w) for SQUIP production trajectories using Dynasor.

   Usage:
       python scripts/compute_sqw.py <molecule> <forcefield> <temperature>

   Example:
       python scripts/compute_sqw.py glycine amber99sb 300K
   """

   import os
   import sys
   import numpy as np
   import logging

   from dynasor import Trajectory, compute_dynamic_structure_factors
   from dynasor.qpoints import get_spherical_qpoints
   from dynasor.post_processing import (
       get_spherically_averaged_sample_binned,
       get_weighted_sample,
       NeutronScatteringLengths,
   )
   from dynasor.units import radians_per_fs_to_meV

   logging.basicConfig(level=logging.INFO,
                       format='%(asctime)s %(levelname)s: %(message)s')
   logger = logging.getLogger(__name__)


   def compute_sqw_for_system(molecule, forcefield, temperature,
                              q_max=2.5, max_q_points=5000,
                              window_size=2000, window_step=200,
                              frame_step=1, frame_stop=None,
                              output_dir=None):
       """
       Compute S(q,w) for a single SQUIP system.

       Parameters
       ----------
       molecule : str
           'glycine' or 'glygly'
       forcefield : str
           'amber99sb' or 'charmm27'
       temperature : str
           '300K' or '350K'
       q_max : float
           Maximum |q| in rad/Å
       max_q_points : int
           Maximum number of q-points for spherical sampling
       window_size : int
           Number of frames per correlation window
       window_step : int
           Step between consecutive windows (frames)
       frame_step : int
           Read every frame_step-th frame from trajectory
       frame_stop : int or None
           Stop reading at this frame (None = read all)
       output_dir : str or None
           Output directory (default: system's production dir)

       Returns
       -------
       sample_averaged : DynamicSample
           Spherically averaged dynamic structure factor sample
       """

       # Paths
       base = os.path.join('systems', molecule, forcefield, temperature, 'production')
       tpr_file = os.path.join(base, 'prod.tpr')
       xtc_file = os.path.join(base, 'prod_center.xtc')
       ndx_file = os.path.join(base, 'dynasor_elements.ndx')

       if output_dir is None:
           output_dir = os.path.join(base, 'analysis')
       os.makedirs(output_dir, exist_ok=True)

       # Verify inputs exist
       for f in [tpr_file, xtc_file]:
           if not os.path.exists(f):
               raise FileNotFoundError(f"Required file not found: {f}")

       logger.info(f"Processing {molecule}/{forcefield}/{temperature}")
       logger.info(f"  TPR: {tpr_file}")
       logger.info(f"  XTC: {xtc_file}")

       # ---------------------------------------------------------------
       # Step 1: Set up trajectory reader
       # ---------------------------------------------------------------
       # Use MDAnalysis format for GROMACS .xtc reading
       # atomic_indices from GROMACS index file maps atoms to element types
       traj_kwargs = dict(
           filename=xtc_file,
           trajectory_format='ase',  # or use MDAnalysis-based reading
           length_unit='nm',         # GROMACS uses nm
           time_unit='ps',           # GROMACS uses ps
           frame_step=frame_step,
       )

       # If index file exists, use it for atom type assignment
       if os.path.exists(ndx_file):
           traj_kwargs['atomic_indices'] = ndx_file
           logger.info(f"  Using index file: {ndx_file}")

       if frame_stop is not None:
           traj_kwargs['frame_stop'] = frame_stop

       traj = Trajectory(**traj_kwargs)
       logger.info(f"  Atoms: {traj.n_atoms}")
       logger.info(f"  Cell: {traj.cell}")

       # ---------------------------------------------------------------
       # Step 2: Generate spherical q-points
       # ---------------------------------------------------------------
       # Cell must be in Å for Dynasor (convert from nm if needed)
       q_points = get_spherical_qpoints(
           traj.cell,
           q_max=q_max,
           max_points=max_q_points,
       )
       logger.info(f"  Generated {len(q_points)} q-points (q_max={q_max} rad/Å)")

       # ---------------------------------------------------------------
       # Step 3: Compute dynamic structure factors
       # ---------------------------------------------------------------
       dt_fs = 30.0  # 30 fs frame interval (from production MDP: 15 steps × 2 fs)

       logger.info(f"  Computing S(q,w) with:")
       logger.info(f"    dt = {dt_fs} fs")
       logger.info(f"    window_size = {window_size} frames = {window_size * dt_fs / 1000:.1f} ps")
       logger.info(f"    window_step = {window_step} frames = {window_step * dt_fs / 1000:.1f} ps")
       logger.info(f"    Frequency resolution: {2 * np.pi / (window_size * dt_fs) * radians_per_fs_to_meV:.4f} meV")
       logger.info(f"    Nyquist frequency: {np.pi / dt_fs * radians_per_fs_to_meV:.1f} meV")

       sample_raw = compute_dynamic_structure_factors(
           traj,
           q_points=q_points,
           dt=dt_fs,
           window_size=window_size,
           window_step=window_step,
           calculate_incoherent=True,
       )

       # ---------------------------------------------------------------
       # Step 4: Spherical average over q-points
       # ---------------------------------------------------------------
       num_q_bins = 30  # Number of radial bins for spherical averaging
       sample_averaged = get_spherically_averaged_sample_binned(
           sample_raw, num_q_bins=num_q_bins
       )
       logger.info(f"  Spherically averaged into {num_q_bins} q-bins")

       # ---------------------------------------------------------------
       # Step 5: Apply neutron scattering weights (for QENS comparison)
       # ---------------------------------------------------------------
       # Determine atom types present in the sample
       atom_types_in_sample = list(sample_raw.particle_counts.keys())
       logger.info(f"  Atom types in sample: {atom_types_in_sample}")

       # Map GROMACS atom types to element symbols for neutron weighting
       # This mapping depends on the index file grouping
       neutron_weights = NeutronScatteringLengths(atom_types_in_sample)
       sample_neutron = get_weighted_sample(sample_averaged, neutron_weights)
       logger.info("  Applied neutron scattering length weighting")

       # ---------------------------------------------------------------
       # Step 6: Convert units and save
       # ---------------------------------------------------------------
       # Convert angular frequency to meV
       omega_meV = sample_averaged.omega * radians_per_fs_to_meV

       # Save raw sample
       prefix = f"{molecule}_{forcefield}_{temperature}"
       raw_file = os.path.join(output_dir, f"{prefix}_sqw_raw.npz")
       sample_raw.write_to_npz(raw_file)
       logger.info(f"  Saved raw sample: {raw_file}")

       # Save averaged sample
       avg_file = os.path.join(output_dir, f"{prefix}_sqw_averaged.npz")
       sample_averaged.write_to_npz(avg_file)
       logger.info(f"  Saved averaged sample: {avg_file}")

       # Save neutron-weighted sample
       neutron_file = os.path.join(output_dir, f"{prefix}_sqw_neutron.npz")
       sample_neutron.write_to_npz(neutron_file)
       logger.info(f"  Saved neutron-weighted sample: {neutron_file}")

       # Save key arrays as plain numpy for easy access
       np.savez(
           os.path.join(output_dir, f"{prefix}_sqw_arrays.npz"),
           q_norms=sample_averaged.q_norms,
           omega_rad_per_fs=sample_averaged.omega,
           omega_meV=omega_meV,
           time_fs=sample_averaged.time,
           Sqw_coh=sample_averaged.Sqw_coh,
           Sqw_incoh=sample_averaged.Sqw_incoh,
           Fqt_coh=sample_averaged.Fqt_coh,
           Fqt_incoh=sample_averaged.Fqt_incoh,
       )
       logger.info(f"  Saved analysis arrays: {prefix}_sqw_arrays.npz")

       logger.info(f"  ✅ {molecule}/{forcefield}/{temperature} complete")
       return sample_averaged


   def main():
       if len(sys.argv) == 4:
           molecule = sys.argv[1]
           forcefield = sys.argv[2]
           temperature = sys.argv[3]
           compute_sqw_for_system(molecule, forcefield, temperature)
       elif len(sys.argv) == 1:
           # Run all 8 systems
           for mol in ['glycine', 'glygly']:
               for ff in ['amber99sb', 'charmm27']:
                   for temp in ['300K', '350K']:
                       try:
                           compute_sqw_for_system(mol, ff, temp)
                       except Exception as e:
                           logger.error(f"Failed {mol}/{ff}/{temp}: {e}")
       else:
           print(__doc__)
           sys.exit(1)


   if __name__ == '__main__':
       main()
   ```

2. **Run a Quick Test on One System**
   ```bash
   # Test with limited frames first (first 1 ns = ~33,333 frames)
   python scripts/compute_sqw.py glycine amber99sb 300K
   ```

3. **Run All 8 Systems**
   ```bash
   # Sequential execution
   python scripts/compute_sqw.py

   # Or run in parallel using GNU parallel
   parallel python scripts/compute_sqw.py {1} {2} {3} \
       ::: glycine glygly ::: amber99sb charmm27 ::: 300K 350K
   ```

### Estimated Computation Time

| System | Atoms | q-points | Est. Time (per window) | Total Windows | Est. Total |
|--------|-------|----------|------------------------|---------------|------------|
| AMBER TIP4P-Ew | ~20,500 | 5,000 | ~5-10 s | ~3,300 | ~5-9 hours |
| CHARMM TIP3P | ~16,000 | 5,000 | ~3-7 s | ~3,300 | ~3-6 hours |

**Total for all 8 systems**: ~30-60 CPU-hours (sequential)

### Deliverables (per system)
- `analysis/{mol}_{ff}_{temp}_sqw_raw.npz` — Full q-point S(q,ω) data
- `analysis/{mol}_{ff}_{temp}_sqw_averaged.npz` — Spherically averaged S(q,ω)
- `analysis/{mol}_{ff}_{temp}_sqw_neutron.npz` — Neutron-weighted S(q,ω)
- `analysis/{mol}_{ff}_{temp}_sqw_arrays.npz` — Plain numpy arrays for quick analysis

---

## Substep 3.4: Validate S(q,ω) Results

### Objective
Verify that computed S(q,ω) are physically reasonable and numerically converged.

### Implementation Steps

1. **Check S(q,ω) Symmetry and Sum Rules**

   ```python
   #!/usr/bin/env python3
   """validate_sqw.py - Validate computed S(q,w) results."""

   import numpy as np
   import matplotlib.pyplot as plt
   from dynasor.units import radians_per_fs_to_meV

   def validate_sqw(npz_path, label):
       """Validate a single S(q,w) dataset."""
       data = np.load(npz_path)
       q_norms = data['q_norms']
       omega_meV = data['omega_meV']
       Sqw_coh = data['Sqw_coh']
       Sqw_incoh = data['Sqw_incoh']
       Fqt_coh = data['Fqt_coh']
       Fqt_incoh = data['Fqt_incoh']
       time_fs = data['time_fs']

       print(f"\n{'='*60}")
       print(f"Validation: {label}")
       print(f"{'='*60}")

       # Check 1: S(q,w) should be non-negative
       min_Sqw = np.nanmin(Sqw_coh)
       print(f"  Min S_coh(q,w): {min_Sqw:.6f} {'✅' if min_Sqw >= -1e-6 else '⚠️ Negative!'}")

       if Sqw_incoh is not None:
           min_Sqw_inc = np.nanmin(Sqw_incoh)
           print(f"  Min S_incoh(q,w): {min_Sqw_inc:.6f} {'✅' if min_Sqw_inc >= -1e-6 else '⚠️ Negative!'}")

       # Check 2: F(q,t=0) should equal S(q) (static structure factor)
       Sq_from_Fqt = Fqt_coh[:, 0]
       print(f"  S(q) range from F(q,0): [{np.nanmin(Sq_from_Fqt):.4f}, {np.nanmax(Sq_from_Fqt):.4f}]")

       # Check 3: F_incoh(q, t=0) = 1 (normalized)
       if Fqt_incoh is not None:
           F_incoh_t0 = Fqt_incoh[:, 0]
           print(f"  F_incoh(q,0) range: [{np.nanmin(F_incoh_t0):.4f}, {np.nanmax(F_incoh_t0):.4f}]")
           print(f"  (should be ~1.0 for self-normalization)")

       # Check 4: q-range coverage
       q_valid = q_norms[~np.isnan(q_norms)]
       print(f"  q-range: [{np.min(q_valid):.3f}, {np.max(q_valid):.3f}] rad/Å")
       print(f"  Number of q-bins: {len(q_norms)}")

       # Check 5: Energy range
       print(f"  Energy range: [{np.min(omega_meV):.3f}, {np.max(omega_meV):.3f}] meV")
       print(f"  Energy resolution: {omega_meV[1] - omega_meV[0]:.4f} meV")

       # Check 6: Time range
       print(f"  Time range: [0, {np.max(time_fs):.0f}] fs = [0, {np.max(time_fs)/1000:.1f}] ps")

       return data

   # Run validation on all systems
   for mol in ['glycine', 'glygly']:
       for ff in ['amber99sb', 'charmm27']:
           for temp in ['300K', '350K']:
               prefix = f"{mol}_{ff}_{temp}"
               npz = f"systems/{mol}/{ff}/{temp}/production/analysis/{prefix}_sqw_arrays.npz"
               try:
                   validate_sqw(npz, prefix)
               except FileNotFoundError:
                   print(f"  ⏭ {prefix}: not yet computed")
   ```

2. **Convergence Check: Window Size Sensitivity**

   ```python
   """Test convergence by comparing different window sizes."""

   window_sizes = [500, 1000, 2000, 4000]  # frames

   for ws in window_sizes:
       sample = compute_sqw_for_system(
           'glycine', 'amber99sb', '300K',
           window_size=ws,
           frame_stop=100000,  # Use first 3 ns for speed
           output_dir=f'convergence_test/ws_{ws}'
       )
   ```

3. **Convergence Check: Trajectory Length Sensitivity**

   ```python
   """Test convergence by comparing different trajectory lengths."""

   frame_stops = [33333, 100000, 333333, 666667]  # 1, 3, 10, 20 ns

   for fs in frame_stops:
       sample = compute_sqw_for_system(
           'glycine', 'amber99sb', '300K',
           frame_stop=fs,
           output_dir=f'convergence_test/frames_{fs}'
       )
   ```

### Validation Criteria

| Property | Criterion | Notes |
|----------|-----------|-------|
| S(q,ω) ≥ 0 | No significant negative values | Small numerical noise acceptable |
| F(q,t→0) = S(q) | Static structure factor recovered | Consistency check |
| F_incoh(q, t=0) ≈ 1 | Self-normalization | Per-particle normalization |
| Quasielastic peak | Centered at ω = 0 | Lorentzian-like for diffusion |
| Γ(q) ~ D·q² at low q | Diffusive behavior | Confirms physical dynamics |
| Converged with trajectory length | Stable results ≥ 10 ns | Within 5% of 20 ns result |

### Deliverables
- Validation report for all 8 systems
- Convergence analysis plots (window size, trajectory length)
- Confirmation of S(q,ω) integrity

---

## Substep 3.5: Extract Quasielastic Linewidths Γ(q)

### Objective
Fit the incoherent intermediate scattering function F_incoh(q,t) to extract quasielastic linewidths Γ(q), which characterize the timescale of diffusive and rotational dynamics.

### Theory

For simple diffusion, the incoherent intermediate scattering function decays as:

$$F_{\text{incoh}}(q, t) = A \cdot \exp(-\Gamma(q) \cdot t)$$

where $\Gamma(q) = D \cdot q^2$ at low q (Fickian diffusion), with $D$ being the translational diffusion coefficient.

For more complex dynamics (rotation + diffusion), a multi-exponential or stretched-exponential fit may be needed:

$$F_{\text{incoh}}(q, t) = A_1 \exp(-\Gamma_1 t) + A_2 \exp(-\Gamma_2 t) + \text{EISF}(q)$$

where EISF is the Elastic Incoherent Structure Factor (fraction of atoms in confined motion).

Equivalently, in the frequency domain, S_incoh(q,ω) is a sum of Lorentzians:

$$S_{\text{incoh}}(q, \omega) = \text{EISF}(q) \cdot \delta(\omega) + \frac{A}{\pi} \frac{\Gamma(q)}{\omega^2 + \Gamma(q)^2}$$

### Implementation Steps

1. **Fit F_incoh(q,t) in the Time Domain**

   ```python
   #!/usr/bin/env python3
   """extract_linewidths.py - Extract Γ(q) from F_incoh(q,t)."""

   import numpy as np
   from scipy.optimize import curve_fit
   import matplotlib.pyplot as plt


   def single_exponential(t, A, gamma):
       """Single exponential decay: A * exp(-gamma * t)."""
       return A * np.exp(-gamma * t)


   def double_exponential(t, A1, gamma1, A2, gamma2, C):
       """Double exponential + elastic: A1*exp(-g1*t) + A2*exp(-g2*t) + C."""
       return A1 * np.exp(-gamma1 * t) + A2 * np.exp(-gamma2 * t) + C


   def stretched_exponential(t, A, gamma, beta):
       """Stretched (KWW) exponential: A * exp(-(gamma*t)^beta)."""
       return A * np.exp(-(gamma * t) ** beta)


   def extract_linewidths(npz_path, fit_range_ps=(0.1, 30.0)):
       """
       Extract Γ(q) from F_incoh(q,t) using exponential fits.

       Parameters
       ----------
       npz_path : str
           Path to the S(q,ω) arrays npz file.
       fit_range_ps : tuple
           (t_min, t_max) in ps for fitting range.

       Returns
       -------
       q_norms : array
           q values in rad/Å.
       gamma_q : array
           Linewidths Γ(q) in meV.
       """
       data = np.load(npz_path)
       q_norms = data['q_norms']
       time_fs = data['time_fs']
       Fqt_incoh = data['Fqt_incoh']

       time_ps = time_fs / 1000.0  # Convert fs to ps

       # Fit range
       t_min, t_max = fit_range_ps
       mask = (time_ps >= t_min) & (time_ps <= t_max)
       t_fit = time_ps[mask]

       gamma_q = np.full(len(q_norms), np.nan)
       gamma_q_err = np.full(len(q_norms), np.nan)
       eisf = np.full(len(q_norms), np.nan)

       for iq in range(len(q_norms)):
           if np.isnan(q_norms[iq]):
               continue

           F_fit = Fqt_incoh[iq, mask]

           if np.any(np.isnan(F_fit)):
               continue

           try:
               # Try single exponential first
               popt, pcov = curve_fit(
                   single_exponential, t_fit, F_fit.real,
                   p0=[1.0, 0.1],
                   bounds=([0, 0], [2, 100]),
                   maxfev=10000,
               )
               gamma_q[iq] = popt[1]  # Γ in 1/ps
               gamma_q_err[iq] = np.sqrt(pcov[1, 1])
           except (RuntimeError, ValueError):
               pass

       # Convert Γ from 1/ps to meV: Γ(meV) = ℏ * Γ(1/ps) = 0.6582 * Γ(1/ps)
       hbar_meV_ps = 0.6582119514  # ℏ in meV·ps
       gamma_meV = gamma_q * hbar_meV_ps
       gamma_meV_err = gamma_q_err * hbar_meV_ps

       return q_norms, gamma_meV, gamma_meV_err, eisf


   def fit_diffusion_coefficient(q_norms, gamma_meV, q_max_fit=1.0):
       """
       Fit Γ(q) = D*q² at low q to extract diffusion coefficient.

       Parameters
       ----------
       q_norms : array
           q values in rad/Å.
       gamma_meV : array
           Linewidths in meV.
       q_max_fit : float
           Maximum q for linear fit (rad/Å).

       Returns
       -------
       D_cm2_per_s : float
           Diffusion coefficient in cm²/s.
       """
       valid = (~np.isnan(q_norms)) & (~np.isnan(gamma_meV)) & (q_norms < q_max_fit) & (q_norms > 0)

       if np.sum(valid) < 3:
           return np.nan

       q2 = q_norms[valid] ** 2  # (rad/Å)²
       G = gamma_meV[valid]      # meV

       # Γ = ℏ D q² → D = Γ / (ℏ q²)
       # Linear fit: Γ = slope * q²
       coeffs = np.polyfit(q2, G, 1)
       slope = coeffs[0]  # meV / (rad/Å)²

       # Convert to cm²/s
       # D = slope / ℏ, with ℏ = 0.6582 meV·ps
       # slope has units meV·Å²/rad² → D in Å²/ps
       # Then convert: 1 Å²/ps = 1e-16 cm² / 1e-12 s = 1e-4 cm²/s
       hbar = 0.6582119514  # meV·ps
       D_A2_per_ps = slope / hbar  # Å²/ps
       D_cm2_per_s = D_A2_per_ps * 1e-4  # cm²/s

       return D_cm2_per_s


   # Process all systems
   results = {}
   for mol in ['glycine', 'glygly']:
       for ff in ['amber99sb', 'charmm27']:
           for temp in ['300K', '350K']:
               prefix = f"{mol}_{ff}_{temp}"
               npz = f"systems/{mol}/{ff}/{temp}/production/analysis/{prefix}_sqw_arrays.npz"
               try:
                   q, gamma, gamma_err, eisf_vals = extract_linewidths(npz)
                   D = fit_diffusion_coefficient(q, gamma)
                   results[prefix] = {
                       'q': q, 'gamma': gamma, 'gamma_err': gamma_err,
                       'D': D
                   }
                   print(f"{prefix}: D = {D:.2e} cm²/s")
               except FileNotFoundError:
                   print(f"{prefix}: not yet computed")
   ```

2. **Extract Diffusion Coefficients and Compare**

   ```python
   """Compare diffusion coefficients across systems."""

   print("\nDiffusion Coefficient Summary")
   print("=" * 70)
   print(f"{'System':<35} {'D (cm²/s)':<15} {'D (10⁻⁵ cm²/s)':<15}")
   print("-" * 70)

   # Expected values from literature:
   # Water self-diffusion: D ≈ 2.3 × 10⁻⁵ cm²/s at 300 K
   # Glycine in water: D ≈ 1.0 × 10⁻⁵ cm²/s at 300 K
   # TIP3P water: D ≈ 5.0 × 10⁻⁵ cm²/s (known to over-predict)
   # TIP4P-Ew water: D ≈ 2.4 × 10⁻⁵ cm²/s (much better)

   for key, val in results.items():
       D = val['D']
       print(f"{key:<35} {D:.2e}     {D*1e5:.2f}")
   ```

### Deliverables
- Γ(q) linewidth data for all 8 systems
- Diffusion coefficients D from Γ(q) = D·q² fits
- Comparison tables across force fields and temperatures

---

## Substep 3.6: Visualization and Comparison Plots

### Objective
Generate publication-quality S(q,ω) heatmaps, F(q,t) decay curves, and Γ(q) dispersion plots for all systems.

### Implementation Steps

1. **S(q,ω) Heatmap Plots**

   ```python
   #!/usr/bin/env python3
   """plot_sqw.py - Generate S(q,w) visualization for all systems."""

   import numpy as np
   import matplotlib.pyplot as plt
   from matplotlib.colors import LogNorm


   def plot_sqw_heatmap(npz_path, title, output_path, energy_max=5.0):
       """Plot S(q,ω) as a heatmap."""
       data = np.load(npz_path)
       q_norms = data['q_norms']
       omega_meV = data['omega_meV']
       Sqw_incoh = data['Sqw_incoh']

       fig, ax = plt.subplots(figsize=(8, 5), dpi=150)

       # Plot only positive frequencies up to energy_max
       mask_w = (omega_meV >= 0) & (omega_meV <= energy_max)
       mask_q = ~np.isnan(q_norms)

       im = ax.pcolormesh(
           q_norms[mask_q], omega_meV[mask_w],
           Sqw_incoh[np.ix_(mask_q, mask_w)].T,
           cmap='hot_r', shading='auto',
       )
       ax.set_xlabel(r'$|q|$ (rad/Å)', fontsize=12)
       ax.set_ylabel(r'$\hbar\omega$ (meV)', fontsize=12)
       ax.set_title(title, fontsize=13)
       plt.colorbar(im, ax=ax, label=r'$S_{\mathrm{incoh}}(q, \omega)$')
       fig.tight_layout()
       fig.savefig(output_path, dpi=150, bbox_inches='tight')
       plt.close(fig)
       print(f"  Saved: {output_path}")


   # Generate heatmaps for all systems
   for mol in ['glycine', 'glygly']:
       for ff in ['amber99sb', 'charmm27']:
           for temp in ['300K', '350K']:
               prefix = f"{mol}_{ff}_{temp}"
               npz = f"systems/{mol}/{ff}/{temp}/production/analysis/{prefix}_sqw_arrays.npz"
               title = f"S_incoh(q,ω) — {mol} / {ff} / {temp}"
               output = f"systems/{mol}/{ff}/{temp}/production/analysis/{prefix}_sqw_heatmap.png"
               try:
                   plot_sqw_heatmap(npz, title, output)
               except FileNotFoundError:
                   print(f"  ⏭ {prefix}: not yet computed")
   ```

2. **F(q,t) Decay Curves at Selected q-values**

   ```python
   def plot_fqt_decay(npz_path, title, output_path, q_targets=[0.5, 1.0, 1.5]):
       """Plot F_incoh(q,t) decay at selected q-values."""
       data = np.load(npz_path)
       q_norms = data['q_norms']
       time_fs = data['time_fs']
       Fqt_incoh = data['Fqt_incoh']
       time_ps = time_fs / 1000.0

       fig, ax = plt.subplots(figsize=(7, 5), dpi=150)

       for q_target in q_targets:
           # Find closest q-bin
           valid = ~np.isnan(q_norms)
           idx = np.nanargmin(np.abs(q_norms - q_target))

           if np.isnan(q_norms[idx]):
               continue

           label = f"|q| = {q_norms[idx]:.2f} rad/Å"
           ax.plot(time_ps, Fqt_incoh[idx, :].real, label=label, alpha=0.8)

       ax.set_xlabel('Time (ps)', fontsize=12)
       ax.set_ylabel(r'$F_{\mathrm{incoh}}(q, t)$', fontsize=12)
       ax.set_title(title, fontsize=13)
       ax.set_xlim([0, 30])  # Show first 30 ps
       ax.legend(fontsize=10)
       ax.set_yscale('log')
       fig.tight_layout()
       fig.savefig(output_path, dpi=150, bbox_inches='tight')
       plt.close(fig)
   ```

3. **Γ(q) Dispersion Plot (Key QENS Observable)**

   ```python
   def plot_gamma_q(results, output_path):
       """Plot Γ(q) vs q² for all systems on one figure."""
       fig, axes = plt.subplots(1, 2, figsize=(14, 6), dpi=150,
                                sharey=True)

       colors = {'amber99sb': 'tab:blue', 'charmm27': 'tab:orange'}
       markers = {'300K': 'o', '350K': 's'}

       for mol_idx, mol in enumerate(['glycine', 'glygly']):
           ax = axes[mol_idx]

           for ff in ['amber99sb', 'charmm27']:
               for temp in ['300K', '350K']:
                   key = f"{mol}_{ff}_{temp}"
                   if key not in results:
                       continue
                   r = results[key]
                   q = r['q']
                   gamma = r['gamma']
                   valid = (~np.isnan(q)) & (~np.isnan(gamma)) & (q > 0)

                   label = f"{ff} {temp} (D={r['D']:.1e})"
                   ax.scatter(q[valid]**2, gamma[valid],
                              c=colors[ff], marker=markers[temp],
                              alpha=0.7, s=40, label=label)

                   # Plot D*q² line
                   if not np.isnan(r['D']):
                       q2_line = np.linspace(0, 4, 100)
                       hbar = 0.6582119514
                       gamma_line = r['D'] * 1e4 * hbar * q2_line  # meV
                       ax.plot(q2_line, gamma_line, c=colors[ff],
                               ls='--', alpha=0.5)

           ax.set_xlabel(r'$q^2$ (rad²/Å²)', fontsize=12)
           ax.set_title(mol.capitalize(), fontsize=13)
           ax.legend(fontsize=8)
           ax.set_xlim([0, 4])

       axes[0].set_ylabel(r'$\Gamma(q)$ (meV)', fontsize=12)
       fig.suptitle('Quasielastic Linewidth Dispersion', fontsize=14, y=1.02)
       fig.tight_layout()
       fig.savefig(output_path, dpi=150, bbox_inches='tight')
       plt.close(fig)
   ```

4. **Temperature Comparison: S(q,ω) Slices**

   ```python
   def plot_temperature_comparison(mol, ff, output_path, q_target=1.0):
       """Compare S(q,ω) at 300 K and 350 K for same system."""
       fig, axes = plt.subplots(1, 2, figsize=(12, 5), dpi=150)

       for idx, temp in enumerate(['300K', '350K']):
           prefix = f"{mol}_{ff}_{temp}"
           npz = f"systems/{mol}/{ff}/{temp}/production/analysis/{prefix}_sqw_arrays.npz"
           data = np.load(npz)

           q_norms = data['q_norms']
           omega_meV = data['omega_meV']
           Sqw_incoh = data['Sqw_incoh']

           # Find closest q-bin to target
           iq = np.nanargmin(np.abs(q_norms - q_target))

           ax = axes[idx]
           mask = (omega_meV >= -3) & (omega_meV <= 3)
           ax.plot(omega_meV[mask], Sqw_incoh[iq, mask], 'b-', lw=1.5)
           ax.set_xlabel(r'$\hbar\omega$ (meV)', fontsize=12)
           ax.set_ylabel(r'$S_{\mathrm{incoh}}(q, \omega)$', fontsize=12)
           ax.set_title(f"{mol} / {ff} / {temp}\n|q| = {q_norms[iq]:.2f} rad/Å",
                        fontsize=11)
           ax.axvline(0, color='gray', ls=':', alpha=0.5)

       fig.tight_layout()
       fig.savefig(output_path, dpi=150, bbox_inches='tight')
       plt.close(fig)
   ```

5. **Force Field Comparison Plot**

   ```python
   def plot_forcefield_comparison(mol, temp, output_path, q_target=1.0):
       """Compare S(q,ω) between AMBER and CHARMM for same molecule/temp."""
       fig, ax = plt.subplots(figsize=(7, 5), dpi=150)

       for ff, color, label in [('amber99sb', 'tab:blue', 'AMBER99SB-ILDN / TIP4P-Ew'),
                                 ('charmm27', 'tab:orange', 'CHARMM27 / TIP3P')]:
           prefix = f"{mol}_{ff}_{temp}"
           npz = f"systems/{mol}/{ff}/{temp}/production/analysis/{prefix}_sqw_arrays.npz"
           data = np.load(npz)

           q_norms = data['q_norms']
           omega_meV = data['omega_meV']
           Sqw_incoh = data['Sqw_incoh']

           iq = np.nanargmin(np.abs(q_norms - q_target))
           mask = (omega_meV >= -3) & (omega_meV <= 3)
           ax.plot(omega_meV[mask], Sqw_incoh[iq, mask],
                   color=color, lw=1.5, label=label)

       ax.set_xlabel(r'$\hbar\omega$ (meV)', fontsize=12)
       ax.set_ylabel(r'$S_{\mathrm{incoh}}(q, \omega)$', fontsize=12)
       ax.set_title(f"{mol} / {temp} — Force Field Comparison\n"
                    f"|q| ≈ {q_target} rad/Å", fontsize=12)
       ax.legend(fontsize=10)
       ax.axvline(0, color='gray', ls=':', alpha=0.5)
       fig.tight_layout()
       fig.savefig(output_path, dpi=150, bbox_inches='tight')
       plt.close(fig)
   ```

### Deliverables
- S(q,ω) heatmaps for all 8 systems
- F(q,t) decay curves at key q-values
- Γ(q) dispersion plots
- Temperature comparison panels
- Force field comparison panels

---

## Substep 3.7: Neutron Scattering Weight Application and QENS-Ready Output

### Objective
Apply proper neutron scattering cross-sections to compute QENS-comparable S(q,ω) and prepare output in standard formats.

### Neutron Scattering Cross-Sections

| Element | σ_coh (barn) | σ_incoh (barn) | b_coh (fm) | b_incoh (fm) |
|---------|-------------|----------------|------------|---------------|
| H | 1.758 | **80.27** | -3.739 | 25.274 |
| D (²H) | 5.592 | 2.05 | 6.671 | 4.04 |
| C | 5.551 | 0.001 | 6.646 | 0.0 |
| N | 11.01 | 0.50 | 9.36 | 2.0 |
| O | 4.232 | 0.0008 | 5.803 | 0.0 |

**Key insight**: Hydrogen dominates incoherent QENS signal (σ_incoh(H) = 80.27 barn).

### Implementation Steps

1. **Apply Neutron Weighting via Dynasor Post-Processing**

   ```python
   from dynasor.post_processing import NeutronScatteringLengths, get_weighted_sample

   def apply_neutron_weights(sample_averaged, atom_types):
       """
       Apply neutron scattering lengths to compute QENS-comparable S(q,ω).

       Parameters
       ----------
       sample_averaged : DynamicSample
           Spherically averaged sample with partial structure factors.
       atom_types : list of str
           Atom type labels matching the Dynasor sample (e.g., ['H', 'C', 'N', 'O']).

       Returns
       -------
       sample_neutron : DynamicSample
           Neutron-weighted sample.
       """
       neutron_weights = NeutronScatteringLengths(atom_types)

       # Display scattering parameters
       print("Neutron scattering parameters:")
       print(neutron_weights.parameters)

       sample_neutron = get_weighted_sample(sample_averaged, neutron_weights)
       return sample_neutron
   ```

2. **Separate Solute and Solvent Contributions**

   For QENS comparison, it's valuable to decompose the signal:

   ```python
   def compute_solute_only_sqw(molecule, forcefield, temperature):
       """
       Compute S(q,ω) using only solute hydrogen atoms.

       This is most directly comparable to experimental QENS of the solute,
       especially if the experimental setup uses D2O as solvent.
       """
       base = f"systems/{molecule}/{forcefield}/{temperature}/production"

       # Create solute-only index in GROMACS NDX format
       # Group solute H atoms separately from water H atoms
       ndx_content = create_solute_hydrogen_index(
           f"{base}/prod.tpr", molecule
       )

       # Run Dynasor only on solute atoms
       traj = Trajectory(
           f"{base}/prod_center.xtc",
           trajectory_format='ase',
           atomic_indices=ndx_content,
           length_unit='nm',
           time_unit='ps',
       )

       q_points = get_spherical_qpoints(traj.cell, q_max=2.5, max_points=5000)

       sample = compute_dynamic_structure_factors(
           traj, q_points, dt=30.0,
           window_size=2000, window_step=200,
           calculate_incoherent=True,
       )

       return get_spherically_averaged_sample_binned(sample, num_q_bins=30)
   ```

3. **Export to HDF5 for Database Integration**

   ```python
   import h5py

   def export_to_hdf5(npz_path, hdf5_path, metadata):
       """
       Export S(q,ω) data to HDF5 with metadata for database storage.

       Parameters
       ----------
       npz_path : str
           Path to the computed S(q,ω) numpy arrays.
       hdf5_path : str
           Output HDF5 file path.
       metadata : dict
           System metadata (molecule, forcefield, temperature, etc.).
       """
       data = np.load(npz_path)

       with h5py.File(hdf5_path, 'w') as f:
           # Metadata
           meta = f.create_group('metadata')
           for key, val in metadata.items():
               meta.attrs[key] = val

           # Axes
           axes = f.create_group('axes')
           axes.create_dataset('q_norms', data=data['q_norms'])
           axes.attrs['q_units'] = 'rad/Angstrom'
           axes.create_dataset('omega_meV', data=data['omega_meV'])
           axes.attrs['omega_units'] = 'meV'
           axes.create_dataset('time_fs', data=data['time_fs'])
           axes.attrs['time_units'] = 'fs'

           # Structure factors
           sqw = f.create_group('structure_factors')
           sqw.create_dataset('Sqw_coh', data=data['Sqw_coh'])
           sqw.create_dataset('Sqw_incoh', data=data['Sqw_incoh'])

           # Intermediate scattering functions
           fqt = f.create_group('intermediate_scattering')
           fqt.create_dataset('Fqt_coh', data=data['Fqt_coh'])
           fqt.create_dataset('Fqt_incoh', data=data['Fqt_incoh'])

       print(f"Exported: {hdf5_path}")


   # Export all systems
   for mol in ['glycine', 'glygly']:
       for ff in ['amber99sb', 'charmm27']:
           for temp in ['300K', '350K']:
               prefix = f"{mol}_{ff}_{temp}"
               npz = f"systems/{mol}/{ff}/{temp}/production/analysis/{prefix}_sqw_arrays.npz"
               hdf5 = f"systems/{mol}/{ff}/{temp}/production/analysis/{prefix}_sqw.h5"
               metadata = {
                   'molecule': mol,
                   'forcefield': ff,
                   'temperature_K': int(temp.replace('K', '')),
                   'water_model': 'TIP4P-Ew' if ff == 'amber99sb' else 'TIP3P',
                   'concentration_M': 0.5,
                   'n_solute': 50,
                   'trajectory_length_ns': 20,
                   'frame_interval_fs': 30,
                   'project': 'SQUIP PoC',
               }
               try:
                   export_to_hdf5(npz, hdf5, metadata)
               except FileNotFoundError:
                   pass
   ```

### Deliverables
- Neutron-weighted S(q,ω) for all 8 systems
- Solute-only S(q,ω) (for D₂O comparison scenarios)
- HDF5 exports ready for database integration (Step 5)

---

## Substep 3.8: Master Analysis Script

### Objective
Create a single orchestration script that runs the complete Step 3 pipeline for all systems.

### Implementation

```python
#!/usr/bin/env python3
"""
run_step3_analysis.py - Master script for Step 3: S(q,ω) calculation.

Runs the complete Dynasor analysis pipeline for all 8 SQUIP systems.

Usage:
    python scripts/run_step3_analysis.py [--test] [--systems glycine/amber99sb/300K]
"""

import argparse
import os
import sys
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('step3_analysis.log'),
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)


def get_all_systems():
    """Return list of all system tuples."""
    systems = []
    for mol in ['glycine', 'glygly']:
        for ff in ['amber99sb', 'charmm27']:
            for temp in ['300K', '350K']:
                systems.append((mol, ff, temp))
    return systems


def run_analysis(systems, test_mode=False):
    """Run complete Step 3 analysis."""

    # Import analysis modules
    from compute_sqw import compute_sqw_for_system
    from extract_linewidths import extract_linewidths, fit_diffusion_coefficient
    from plot_sqw import (
        plot_sqw_heatmap,
        plot_fqt_decay,
        plot_gamma_q,
        plot_temperature_comparison,
        plot_forcefield_comparison,
    )
    from export_hdf5 import export_to_hdf5

    frame_stop = 33333 if test_mode else None  # 1 ns for test, full for production
    results = {}

    # Phase 1: Compute S(q,ω) for all systems
    logger.info("="*60)
    logger.info("Phase 1: Computing S(q,ω) for all systems")
    logger.info("="*60)

    for mol, ff, temp in systems:
        t0 = time.time()
        try:
            compute_sqw_for_system(mol, ff, temp, frame_stop=frame_stop)
            dt = time.time() - t0
            logger.info(f"  {mol}/{ff}/{temp}: completed in {dt/60:.1f} min")
        except Exception as e:
            logger.error(f"  {mol}/{ff}/{temp}: FAILED - {e}")

    # Phase 2: Extract linewidths and diffusion coefficients
    logger.info("="*60)
    logger.info("Phase 2: Extracting linewidths Γ(q)")
    logger.info("="*60)

    for mol, ff, temp in systems:
        prefix = f"{mol}_{ff}_{temp}"
        npz = f"systems/{mol}/{ff}/{temp}/production/analysis/{prefix}_sqw_arrays.npz"
        try:
            q, gamma, gamma_err, eisf = extract_linewidths(npz)
            D = fit_diffusion_coefficient(q, gamma)
            results[prefix] = {'q': q, 'gamma': gamma, 'gamma_err': gamma_err, 'D': D}
            logger.info(f"  {prefix}: D = {D:.2e} cm²/s")
        except Exception as e:
            logger.error(f"  {prefix}: FAILED - {e}")

    # Phase 3: Generate plots
    logger.info("="*60)
    logger.info("Phase 3: Generating plots")
    logger.info("="*60)

    os.makedirs('analysis/plots', exist_ok=True)

    for mol, ff, temp in systems:
        prefix = f"{mol}_{ff}_{temp}"
        base = f"systems/{mol}/{ff}/{temp}/production/analysis"
        npz = f"{base}/{prefix}_sqw_arrays.npz"
        try:
            plot_sqw_heatmap(npz, prefix, f"analysis/plots/{prefix}_heatmap.png")
            plot_fqt_decay(npz, prefix, f"analysis/plots/{prefix}_fqt.png")
        except Exception as e:
            logger.warning(f"  Plot failed for {prefix}: {e}")

    # Cross-system comparison plots
    if results:
        plot_gamma_q(results, 'analysis/plots/gamma_q_all.png')

    for mol in ['glycine', 'glygly']:
        for ff in ['amber99sb', 'charmm27']:
            try:
                plot_temperature_comparison(
                    mol, ff, f'analysis/plots/{mol}_{ff}_temp_compare.png')
            except Exception as e:
                logger.warning(f"  Temperature comparison failed: {e}")

        for temp in ['300K', '350K']:
            try:
                plot_forcefield_comparison(
                    mol, temp, f'analysis/plots/{mol}_{temp}_ff_compare.png')
            except Exception as e:
                logger.warning(f"  FF comparison failed: {e}")

    # Phase 4: Export to HDF5
    logger.info("="*60)
    logger.info("Phase 4: Exporting to HDF5")
    logger.info("="*60)

    for mol, ff, temp in systems:
        prefix = f"{mol}_{ff}_{temp}"
        npz = f"systems/{mol}/{ff}/{temp}/production/analysis/{prefix}_sqw_arrays.npz"
        hdf5 = f"systems/{mol}/{ff}/{temp}/production/analysis/{prefix}_sqw.h5"
        metadata = {
            'molecule': mol,
            'forcefield': ff,
            'temperature_K': int(temp.replace('K', '')),
            'water_model': 'TIP4P-Ew' if ff == 'amber99sb' else 'TIP3P',
            'concentration_M': 0.5,
            'n_solute': 50,
            'trajectory_length_ns': 20,
            'frame_interval_fs': 30,
        }
        try:
            export_to_hdf5(npz, hdf5, metadata)
        except Exception as e:
            logger.warning(f"  HDF5 export failed for {prefix}: {e}")

    # Phase 5: Summary report
    logger.info("="*60)
    logger.info("Step 3 Analysis Complete — Summary")
    logger.info("="*60)

    print("\nDiffusion Coefficients:")
    print(f"{'System':<35} {'D (10⁻⁵ cm²/s)':<20}")
    print("-" * 55)
    for key in sorted(results.keys()):
        D = results[key]['D']
        print(f"{key:<35} {D*1e5:.3f}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run Step 3 S(q,ω) analysis')
    parser.add_argument('--test', action='store_true',
                        help='Test mode: use first 1 ns only')
    parser.add_argument('--systems', nargs='+',
                        help='Specific systems (e.g., glycine/amber99sb/300K)')
    args = parser.parse_args()

    if args.systems:
        systems = [tuple(s.split('/')) for s in args.systems]
    else:
        systems = get_all_systems()

    run_analysis(systems, test_mode=args.test)
```

### Deliverables
- `scripts/run_step3_analysis.py` — Master orchestration script
- `step3_analysis.log` — Full analysis log

---

## Step 3 Summary and Checklist

### Expected Outputs

For each of 8 systems:
- `analysis/{prefix}_sqw_raw.npz` — Full S(q,ω) data
- `analysis/{prefix}_sqw_averaged.npz` — Spherically averaged data
- `analysis/{prefix}_sqw_neutron.npz` — Neutron-weighted data
- `analysis/{prefix}_sqw_arrays.npz` — Quick-access numpy arrays
- `analysis/{prefix}_sqw.h5` — HDF5 export for database

Global outputs:
- `analysis/plots/` — All comparison and visualization plots
- `step3_analysis.log` — Analysis log
- Diffusion coefficient table for all systems

### Verification Checklist

**S(q,ω) Quality:**
- [ ] All 8 systems computed without errors
- [ ] S(q,ω) is non-negative (within numerical noise)
- [ ] F(q,t=0) recovers static structure factor S(q)
- [ ] F_incoh(q,t=0) ≈ 1 (proper normalization)
- [ ] q-range covers 0.3–2.0 rad/Å
- [ ] Energy resolution ≤ 0.1 meV

**Physical Validation:**
- [ ] Quasielastic peak centered at ω = 0
- [ ] F_incoh(q,t) shows exponential-like decay
- [ ] Γ(q) ~ D·q² at low q (diffusive limit)
- [ ] D(300 K) < D(350 K) (higher T → faster diffusion)
- [ ] Diffusion coefficients within reasonable range (10⁻⁶ to 10⁻⁴ cm²/s)

**Convergence:**
- [ ] Results stable with window_size ≥ 1000 frames
- [ ] Results converged with trajectory length ≥ 10 ns
- [ ] Sufficient q-point sampling (≥ 3000 points)

**Force Field Comparison:**
- [ ] Quantifiable differences between AMBER and CHARMM S(q,ω)
- [ ] TIP4P-Ew shows different dynamics than TIP3P (expected)

**Output Files:**
- [ ] All .npz files generated and loadable
- [ ] All .h5 files generated with correct metadata
- [ ] All plots generated and visually inspected

### Directory Structure After Step 3

```
SQUIP/
├── scripts/
│   ├── compute_sqw.py
│   ├── extract_linewidths.py
│   ├── validate_sqw.py
│   ├── plot_sqw.py
│   ├── export_hdf5.py
│   └── run_step3_analysis.py
├── analysis/
│   └── plots/
│       ├── glycine_amber99sb_300K_heatmap.png
│       ├── glycine_amber99sb_300K_fqt.png
│       ├── gamma_q_all.png
│       ├── glycine_amber99sb_temp_compare.png
│       ├── glycine_300K_ff_compare.png
│       └── [... more plots ...]
├── systems/
│   ├── glycine/
│   │   ├── amber99sb/
│   │   │   ├── 300K/
│   │   │   │   └── production/
│   │   │   │       ├── analysis/
│   │   │   │       │   ├── glycine_amber99sb_300K_sqw_raw.npz
│   │   │   │       │   ├── glycine_amber99sb_300K_sqw_averaged.npz
│   │   │   │       │   ├── glycine_amber99sb_300K_sqw_neutron.npz
│   │   │   │       │   ├── glycine_amber99sb_300K_sqw_arrays.npz
│   │   │   │       │   └── glycine_amber99sb_300K_sqw.h5
│   │   │   │       ├── dynasor_elements.ndx
│   │   │   │       ├── prod.xtc
│   │   │   │       ├── prod_center.xtc
│   │   │   │       └── prod.tpr
│   │   │   └── 350K/
│   │   │       └── production/
│   │   │           └── [same structure]
│   │   └── charmm27/
│   │       └── [same structure]
│   └── glygly/
│       └── [same structure as glycine]
└── step3_analysis.log
```

---

## Resource Estimates

### Computational Resources

| Resource | Requirement | Notes |
|----------|-------------|-------|
| CPU cores | 4-8 per analysis | Dynasor uses OpenMP |
| RAM | ~8-16 GB per system | Depends on trajectory chunk size |
| Storage | ~5-10 GB per system (analysis output) | Plus existing trajectory files |
| Walltime | ~4-8 hours per system (CPU) | 30-60 hours total sequential |

### Memory Optimization

For memory-constrained systems, use `frame_step` to reduce the number of frames loaded:

```python
# Use every 2nd frame → effective dt = 60 fs, Nyquist = 34.5 meV
traj = Trajectory(..., frame_step=2)
sample = compute_dynamic_structure_factors(traj, q_points, dt=30.0, ...)
# Note: dt stays at 30 fs (the original spacing), frame_step handles subsampling
```

---

## Troubleshooting

### Common Issues

1. **"NPT trajectory not supported"**
   - Dynasor requires constant-volume trajectories
   - Solution: Re-image trajectory to fixed box (see Substep 3.2)
   - For PoC: NPT box fluctuations are typically < 0.1%, acceptable for analysis

2. **Memory errors with large trajectories**
   - 20 ns @ 30 fs = ~666,667 frames × 20,000 atoms = large memory footprint
   - Solution: Use `frame_step=2` or process trajectory windows separately
   - Then average results using `get_sample_averaged_over_independent_runs()`

3. **Atom type mapping errors**
   - Dynasor needs element-level atom types for neutron weighting
   - GROMACS uses force-field-specific names (e.g., "OW", "HW1", "CA")
   - Solution: Use NDX file or `atom_type_map` parameter to map back to elements

4. **Negative S(q,ω) values**
   - Small negative values near zero are numerical noise — acceptable
   - Large negative values indicate windowing/FFT artifacts
   - Solution: Increase `window_size`, use Filon integration, or apply windowing function

5. **Flat or noisy Γ(q)**
   - Insufficient trajectory length or too few q-points
   - Solution: Use full 20 ns trajectory, increase `max_q_points`

---

## Notes and Considerations

1. **NPT vs NVT for Dynasor**: Our production runs are NPT, while Dynasor formally requires NVT. For well-equilibrated aqueous systems at ambient conditions, NPT box fluctuations are negligible (~0.01 nm on a 5.4 nm box). This is acceptable for PoC; for publication, consider short NVT production segments or explicit re-imaging.

2. **Incoherent vs Coherent**: For QENS, the **incoherent** dynamic structure factor dominates due to hydrogen's enormous incoherent cross-section (80.27 barn). Always compute with `calculate_incoherent=True`.

3. **Solute vs Solvent Signal**: Experimental QENS often uses D₂O to suppress water signal. To mimic this, compute S(q,ω) including only solute atoms, or weight water hydrogen with deuterium cross-sections.

4. **Window Size Trade-off**: Larger `window_size` gives better energy resolution but fewer windows for averaging. For QENS: 2000 frames (60 ps) gives ~0.07 meV resolution, which is comparable to backscattering spectrometers like BASIS or IN16B.

5. **q-point Sampling**: For isotropic liquids, spherical averaging over many q-points is essential. 5000 q-points with 30 radial bins typically gives smooth S(q,ω) curves.

6. **Unit Conversions**: Dynasor works internally in Å and fs. GROMACS uses nm and ps. Always specify `length_unit='nm'` and `time_unit='ps'` when reading GROMACS trajectories.

7. **Trajectory Output Frequency**: Our 30 fs output gives a Nyquist frequency of ~69 meV, well above the QENS-relevant range (< 10 meV). The 20 fs output version would give ~82 meV Nyquist — marginal improvement for the quasielastic region.

---

## Next Steps

After completing Step 3:

- **Step 4**: Experimental Comparison
  - Find published QENS data for glycine/Gly-Gly solutions
  - Match q-grid and energy resolution
  - Apply instrument resolution convolution to computed S(q,ω)
  - Overlay MD vs. experiment
  - Compute residual metrics

- **Step 5**: Database Schema Design
  - Populate SQLite + HDF5 database with S(q,ω) datasets
  - Store metadata, provenance, and analysis parameters
  - Create query interface for retrieving results

---

## References

1. Fransson, E., Slabber, M., Erhart, P., & Ekborg-Tanner, P. (2023). "dynasor — A Tool for Extracting Dynamical Structure Factors and Current Correlation Functions from Molecular Dynamics Simulations." *Advanced Theory and Simulations*, 2100191. [doi: 10.1002/adts.202100191](https://doi.org/10.1002/adts.202100191)
2. Dynasor Documentation: [https://dynasor.materialsmodeling.org/](https://dynasor.materialsmodeling.org/)
3. Bée, M. (1988). *Quasielastic Neutron Scattering*. Adam Hilger.
4. Bellissent-Funel, M.-C. et al. (2016). "Water Determines the Structure and Dynamics of Proteins." *Chem. Rev.* 116, 7673-7697.
5. NIST Neutron Scattering Lengths: [https://www.ncnr.nist.gov/resources/n-lengths/list.html](https://www.ncnr.nist.gov/resources/n-lengths/list.html)
6. Magazù, S. et al. (2011). "Mean Square Displacements from Elastic Incoherent Neutron Scattering." *J. Phys. Chem. B* 115, 7736-7743.
