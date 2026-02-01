#!/bin/bash
# process_all.sh - Master script to process all 8 production trajectories
# Usage: ./process_all.sh [base_dir]

set -e

BASE_DIR="${1:-systems}"
SCRIPT_DIR="$(dirname "$0")"

echo "=============================================="
echo "TRAJECTORY PROCESSING FOR QENS ANALYSIS"
echo "Substep 2.5 - Processing all 8 systems"
echo "=============================================="
echo "Base directory: $BASE_DIR"
echo "Started: $(date)"
echo ""

# Define all systems
SYSTEMS=(
    "glycine/amber99sb/300K"
    "glycine/amber99sb/350K"
    "glycine/charmm27/300K"
    "glycine/charmm27/350K"
    "glygly/amber99sb/300K"
    "glygly/amber99sb/350K"
    "glygly/charmm27/300K"
    "glygly/charmm27/350K"
)

# Track results
PROCESSED=0
FAILED=0
SKIPPED=0

for sys in "${SYSTEMS[@]}"; do
    PROD_DIR="$BASE_DIR/$sys/production"
    
    echo "----------------------------------------------"
    echo "Processing: $sys"
    echo "----------------------------------------------"
    
    # Check if production files exist
    if [ ! -f "$PROD_DIR/prod.xtc" ]; then
        echo "  SKIPPED: prod.xtc not found"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi
    
    if [ ! -f "$PROD_DIR/prod.tpr" ]; then
        echo "  SKIPPED: prod.tpr not found"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi
    
    # Run processing script for this system
    if "$SCRIPT_DIR/process_trajectory.sh" "$PROD_DIR"; then
        echo "  SUCCESS"
        PROCESSED=$((PROCESSED + 1))
    else
        echo "  FAILED"
        FAILED=$((FAILED + 1))
    fi
    
    echo ""
done

echo "=============================================="
echo "SUMMARY"
echo "=============================================="
echo "Processed: $PROCESSED/8"
echo "Failed:    $FAILED/8"
echo "Skipped:   $SKIPPED/8"
echo "Finished:  $(date)"
echo "=============================================="

if [ "$FAILED" -eq 0 ] && [ "$PROCESSED" -eq 8 ]; then
    echo "All systems processed successfully!"
    exit 0
else
    echo "Some systems failed or were skipped"
    exit 1
fi
