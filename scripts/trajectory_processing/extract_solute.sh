#!/bin/bash
# extract_solute.sh - Extract solute-only trajectory (no water)
# Usage: ./extract_solute.sh <production_dir>
#
# Useful for visualization and solute-focused analysis

set -e

PROD_DIR="$1"

if [ -z "$PROD_DIR" ]; then
    echo "Usage: $0 <production_dir>"
    exit 1
fi

cd "$PROD_DIR"

# Check input
if [ ! -f "prod.tpr" ]; then
    echo "ERROR: prod.tpr not found"
    exit 1
fi

# Use centered trajectory if available
if [ -f "prod_center.xtc" ]; then
    INPUT_XTC="prod_center.xtc"
else
    INPUT_XTC="prod.xtc"
fi

if [ ! -f "$INPUT_XTC" ]; then
    echo "ERROR: No trajectory found"
    exit 1
fi

echo "Creating solute-only trajectory..."
echo "Input: $INPUT_XTC"

# Create index file with non-Water group
if [ ! -f "solute.ndx" ]; then
    echo "Creating solute index..."
    # Try to create non-Water selection
    gmx make_ndx -f prod.tpr -o solute.ndx << EOF
! a SOL* & ! a TIP* & ! a WAT* & ! a HOH*
name 0 Solute
q
EOF
    
    # If that failed, try another approach
    if [ $? -ne 0 ]; then
        gmx select -s prod.tpr -on solute.ndx \
            -select 'not resname SOL TIP3 TIP4 HOH WAT'
    fi
fi

# Extract solute
if [ ! -f "prod_solute.xtc" ]; then
    echo "Extracting solute atoms..."
    if [ -f "solute.ndx" ]; then
        echo "Solute" | gmx trjconv -f "$INPUT_XTC" -s prod.tpr -n solute.ndx \
            -o prod_solute.xtc 2>/dev/null || \
        echo "0" | gmx trjconv -f "$INPUT_XTC" -s prod.tpr -n solute.ndx \
            -o prod_solute.xtc
    fi
else
    echo "prod_solute.xtc already exists"
fi

# Verify
if [ -f "prod_solute.xtc" ]; then
    echo ""
    echo "Output: prod_solute.xtc"
    gmx check -f prod_solute.xtc 2>&1 | grep -E "Coords|Last frame"
    ls -lh prod_solute.xtc
fi
