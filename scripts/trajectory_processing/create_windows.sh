#!/bin/bash
# create_windows.sh - Create time-windowed subtrajectories for ensemble averaging
# Usage: ./create_windows.sh <production_dir> [window_size_ns] [step_ns]
#
# Default: 1 ns windows with no overlap
# Creates prod_window_0ns.xtc, prod_window_1ns.xtc, etc.

set -e

PROD_DIR="$1"
WINDOW_NS="${2:-1}"      # Window size in ns (default: 1 ns)
STEP_NS="${3:-$WINDOW_NS}"  # Step between windows (default: non-overlapping)

if [ -z "$PROD_DIR" ]; then
    echo "Usage: $0 <production_dir> [window_size_ns] [step_ns]"
    echo ""
    echo "Arguments:"
    echo "  production_dir  - Directory containing prod.xtc and prod.tpr"
    echo "  window_size_ns  - Size of each window in ns (default: 1)"
    echo "  step_ns         - Step between windows in ns (default: window_size)"
    echo ""
    echo "Examples:"
    echo "  $0 systems/glycine/amber99sb/300K/production"
    echo "  $0 systems/glycine/amber99sb/300K/production 2     # 2 ns windows"
    echo "  $0 systems/glycine/amber99sb/300K/production 2 1   # 2 ns windows, 1 ns overlap"
    exit 1
fi

cd "$PROD_DIR"

# Check required files
if [ ! -f "prod.xtc" ] && [ ! -f "prod_center.xtc" ]; then
    echo "ERROR: No trajectory found (prod.xtc or prod_center.xtc)"
    exit 1
fi

# Prefer centered trajectory if available
if [ -f "prod_center.xtc" ]; then
    INPUT_XTC="prod_center.xtc"
    echo "Using centered trajectory: $INPUT_XTC"
else
    INPUT_XTC="prod.xtc"
    echo "Using raw trajectory: $INPUT_XTC"
fi

# Get trajectory duration
LAST_TIME=$(gmx check -f "$INPUT_XTC" 2>&1 | grep "Last frame" | awk '{print $4}')
LAST_NS=$(echo "scale=2; $LAST_TIME / 1000" | bc)
echo "Trajectory duration: $LAST_NS ns"

# Create windows directory
mkdir -p windows
echo ""
echo "Creating ${WINDOW_NS} ns windows with ${STEP_NS} ns step..."
echo ""

WINDOW_PS=$(echo "$WINDOW_NS * 1000" | bc)
STEP_PS=$(echo "$STEP_NS * 1000" | bc)
LAST_TIME_INT=$(printf "%.0f" "$LAST_TIME")

COUNT=0
START=0

while (( $(echo "$START + $WINDOW_PS <= $LAST_TIME_INT" | bc -l) )); do
    END=$((START + WINDOW_PS))
    WINDOW_FILE="windows/window_${COUNT}.xtc"
    
    if [ ! -f "$WINDOW_FILE" ]; then
        echo "  Window $COUNT: ${START}-${END} ps ($(echo "scale=1; $START/1000" | bc)-$(echo "scale=1; $END/1000" | bc) ns)"
        echo "0" | gmx trjconv -f "$INPUT_XTC" -s prod.tpr -b $START -e $END \
            -o "$WINDOW_FILE" 2>/dev/null
    else
        echo "  Window $COUNT: exists, skipping"
    fi
    
    START=$((START + STEP_PS))
    COUNT=$((COUNT + 1))
done

echo ""
echo "Created $COUNT windows in: $PROD_DIR/windows/"
ls -lh windows/*.xtc 2>/dev/null | head -10
if [ "$COUNT" -gt 10 ]; then
    echo "  ... and $((COUNT - 10)) more"
fi
