#!/bin/bash
# process_trajectory.sh - Process a single production trajectory for QENS analysis
# Usage: ./process_trajectory.sh <production_dir>
#
# Creates:
#   - prod_center.xtc     - Centered, PBC-corrected trajectory
#   - prod_whole.xtc      - Molecules made whole (no broken bonds)
#   - prod_hydrogen.xtc   - Hydrogen-only trajectory for QENS
#   - index.ndx           - Index file with analysis groups

set -e

PROD_DIR="$1"

if [ -z "$PROD_DIR" ]; then
    echo "Usage: $0 <production_dir>"
    echo "Example: $0 systems/glycine/amber99sb/300K/production"
    exit 1
fi

cd "$PROD_DIR"

# Check required files
if [ ! -f "prod.xtc" ]; then
    echo "ERROR: prod.xtc not found in $PROD_DIR"
    exit 1
fi

if [ ! -f "prod.tpr" ]; then
    echo "ERROR: prod.tpr not found in $PROD_DIR"
    exit 1
fi

echo "Processing trajectory in: $PROD_DIR"
echo ""

# Step 1: Create index file with useful groups
echo "Step 1: Creating index file..."
if [ ! -f "index.ndx" ]; then
    # Create index with System, Protein/Solute, Water, and Hydrogen groups
    # Using automated selection - adjust if needed
    gmx make_ndx -f prod.tpr -o index.ndx << EOF
q
EOF
    echo "  Created: index.ndx"
else
    echo "  index.ndx already exists, skipping"
fi

# Step 2: Make molecules whole (fix broken molecules across PBC)
echo ""
echo "Step 2: Making molecules whole..."
if [ ! -f "prod_whole.xtc" ]; then
    echo "0" | gmx trjconv -f prod.xtc -s prod.tpr -o prod_whole.xtc -pbc whole
    echo "  Created: prod_whole.xtc"
else
    echo "  prod_whole.xtc already exists, skipping"
fi

# Step 3: Center on system and remove jumps
echo ""
echo "Step 3: Centering trajectory..."
if [ ! -f "prod_center.xtc" ]; then
    # Center on System (group 0), output System (group 0)
    echo "0 0" | gmx trjconv -f prod_whole.xtc -s prod.tpr -o prod_center.xtc \
        -center -pbc mol -ur compact
    echo "  Created: prod_center.xtc"
else
    echo "  prod_center.xtc already exists, skipping"
fi

# Step 4: Create hydrogen-only trajectory for QENS
echo ""
echo "Step 4: Extracting hydrogen atoms for QENS..."
if [ ! -f "prod_hydrogen.xtc" ]; then
    # First, create hydrogen index if not present
    if ! grep -q "Hydrogen" index.ndx 2>/dev/null; then
        echo "  Creating hydrogen index group..."
        gmx select -s prod.tpr -on hydrogen.ndx -select "name \"H*\""
    fi
    
    # Extract hydrogen atoms
    if [ -f "hydrogen.ndx" ]; then
        echo "0" | gmx trjconv -f prod_center.xtc -s prod.tpr -n hydrogen.ndx \
            -o prod_hydrogen.xtc
    else
        # Fallback: try selecting by atom type
        # Use "a H*" pattern in make_ndx
        gmx make_ndx -f prod.tpr -o hydrogen_temp.ndx << EOF
a H*
name 0 Hydrogen
q
EOF
        echo "Hydrogen" | gmx trjconv -f prod_center.xtc -s prod.tpr \
            -n hydrogen_temp.ndx -o prod_hydrogen.xtc
        rm -f hydrogen_temp.ndx
    fi
    echo "  Created: prod_hydrogen.xtc"
else
    echo "  prod_hydrogen.xtc already exists, skipping"
fi

# Step 5: Verify processed trajectories
echo ""
echo "Step 5: Verifying processed trajectories..."
for traj in prod_center.xtc prod_hydrogen.xtc; do
    if [ -f "$traj" ]; then
        # Get info
        INFO=$(gmx check -f "$traj" 2>&1 | grep -E "Last frame|Coords" | head -2)
        SIZE=$(ls -lh "$traj" | awk '{print $5}')
        echo "  $traj: $SIZE"
        echo "    $INFO"
    fi
done

# Step 6: Get file sizes summary
echo ""
echo "File sizes:"
ls -lh prod*.xtc 2>/dev/null | awk '{print "  " $9 ": " $5}'

echo ""
echo "Processing complete!"
