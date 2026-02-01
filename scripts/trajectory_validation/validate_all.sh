#!/bin/bash
# validate_all.sh - Master script to validate all production trajectories
# Usage: ./validate_all.sh [base_dir]

set -e

BASE_DIR="${1:-.}"
SCRIPT_DIR="$(dirname "$0")"

echo "========================================"
echo "  SQUIP Production Trajectory Validation"
echo "========================================"
echo "Base directory: $BASE_DIR"
echo "Date: $(date)"
echo ""

# Define systems
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

# Create output directory
REPORT_DIR="$BASE_DIR/validation_reports"
mkdir -p "$REPORT_DIR"

# Summary file
SUMMARY="$REPORT_DIR/validation_summary.txt"
echo "SQUIP Production Validation Summary" > "$SUMMARY"
echo "Generated: $(date)" >> "$SUMMARY"
echo "========================================" >> "$SUMMARY"
echo "" >> "$SUMMARY"

# Validate each system
for sys in "${SYSTEMS[@]}"; do
    PROD_DIR="$BASE_DIR/systems/$sys"
    
    echo ""
    echo "----------------------------------------"
    echo "Validating: $sys"
    echo "----------------------------------------"
    
    if [ ! -f "$PROD_DIR/prod.xtc" ]; then
        echo "  SKIP: prod.xtc not found"
        echo "$sys: MISSING" >> "$SUMMARY"
        continue
    fi
    
    # Run validation
    bash "$SCRIPT_DIR/validate_trajectory.sh" "$PROD_DIR" "$REPORT_DIR/${sys//\//_}"
    
    # Check result
    if [ $? -eq 0 ]; then
        echo "$sys: PASS" >> "$SUMMARY"
    else
        echo "$sys: FAIL" >> "$SUMMARY"
    fi
done

echo ""
echo "========================================"
echo "Validation Complete"
echo "========================================"
echo ""
cat "$SUMMARY"
echo ""
echo "Detailed reports in: $REPORT_DIR"
