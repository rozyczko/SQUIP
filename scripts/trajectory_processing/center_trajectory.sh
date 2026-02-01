#!/bin/bash
# center_trajectory.sh - Center trajectory and fix PBC artifacts
# Usage: ./center_trajectory.sh <production_dir> [center_group] [output_group]
#
# Default: Center on System (0), output System (0)

set -e

PROD_DIR="$1"
CENTER_GROUP="${2:-0}"   # Group to center on (default: System)
OUTPUT_GROUP="${3:-0}"   # Group to output (default: System)

if [ -z "$PROD_DIR" ]; then
    echo "Usage: $0 <production_dir> [center_group] [output_group]"
    echo ""
    echo "Group options:"
    echo "  0 = System (all atoms)"
    echo "  1 = Protein (if defined)"
    echo "  Use 'gmx make_ndx -f prod.tpr' to see available groups"
    exit 1
fi

cd "$PROD_DIR"

if [ ! -f "prod.xtc" ]; then
    echo "ERROR: prod.xtc not found"
    exit 1
fi

if [ ! -f "prod.tpr" ]; then
    echo "ERROR: prod.tpr not found"
    exit 1
fi

echo "Centering trajectory..."
echo "  Center group: $CENTER_GROUP"
echo "  Output group: $OUTPUT_GROUP"
echo ""

# Step 1: Make molecules whole (fix broken molecules across PBC)
if [ ! -f "prod_whole.xtc" ]; then
    echo "Step 1: Making molecules whole..."
    echo "$OUTPUT_GROUP" | gmx trjconv -f prod.xtc -s prod.tpr -o prod_whole.xtc -pbc whole
else
    echo "Step 1: prod_whole.xtc exists, skipping"
fi

# Step 2: Center and cluster
if [ ! -f "prod_center.xtc" ]; then
    echo ""
    echo "Step 2: Centering on group $CENTER_GROUP..."
    echo "$CENTER_GROUP $OUTPUT_GROUP" | gmx trjconv -f prod_whole.xtc -s prod.tpr \
        -o prod_center.xtc -center -pbc mol -ur compact
else
    echo "Step 2: prod_center.xtc exists, skipping"
fi

# Verify
echo ""
echo "Verification:"
for f in prod.xtc prod_whole.xtc prod_center.xtc; do
    if [ -f "$f" ]; then
        SIZE=$(ls -lh "$f" | awk '{print $5}')
        echo "  $f: $SIZE"
    fi
done

echo ""
echo "Done! Output: prod_center.xtc"
