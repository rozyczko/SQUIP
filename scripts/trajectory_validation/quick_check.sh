#!/bin/bash
# quick_check.sh - Fast pass/fail check for a production run
# Usage: ./quick_check.sh <production_dir>
# Returns: 0 = PASS, 1 = FAIL

PROD_DIR="$1"

if [ -z "$PROD_DIR" ]; then
    echo "Usage: $0 <production_dir>"
    exit 1
fi

echo "Quick check: $PROD_DIR"

ERRORS=0

# 1. Check files exist
for f in prod.xtc prod.edr prod.log prod.tpr; do
    if [ ! -f "$PROD_DIR/$f" ]; then
        echo "✗ Missing: $f"
        ERRORS=$((ERRORS + 1))
    fi
done

# 2. Check simulation completed
if [ -f "$PROD_DIR/prod.log" ]; then
    if grep -q "Finished mdrun" "$PROD_DIR/prod.log"; then
        echo "✓ Simulation completed"
    else
        echo "✗ Simulation incomplete"
        ERRORS=$((ERRORS + 1))
    fi
fi

# 3. Check trajectory length
if [ -f "$PROD_DIR/prod.xtc" ]; then
    LAST_TIME=$(gmx check -f "$PROD_DIR/prod.xtc" 2>&1 | grep "Last frame" | awk '{print $4}')
    if [ -n "$LAST_TIME" ]; then
        # Check if >= 19000 ps (19 ns, allowing some margin)
        if (( $(echo "$LAST_TIME >= 19000" | bc -l) )); then
            echo "✓ Trajectory length: $LAST_TIME ps"
        else
            echo "✗ Trajectory too short: $LAST_TIME ps (expected >= 19000)"
            ERRORS=$((ERRORS + 1))
        fi
    fi
fi

# 4. Check for fatal errors
if [ -f "$PROD_DIR/prod.log" ]; then
    FATAL=$(grep -ci "fatal" "$PROD_DIR/prod.log" 2>/dev/null || echo 0)
    if [ "$FATAL" -gt 0 ]; then
        echo "✗ Fatal errors: $FATAL"
        ERRORS=$((ERRORS + 1))
    fi
    
    # Check LINCS warnings (allow up to 100)
    LINCS=$(grep -ci "LINCS warning" "$PROD_DIR/prod.log" 2>/dev/null || echo 0)
    if [ "$LINCS" -gt 100 ]; then
        echo "⚠ Excessive LINCS warnings: $LINCS"
        # Don't fail, just warn
    fi
fi

# 5. Check trajectory file size (should be > 50 GB for 20 ns)
if [ -f "$PROD_DIR/prod.xtc" ]; then
    SIZE=$(stat --printf="%s" "$PROD_DIR/prod.xtc" 2>/dev/null || stat -f%z "$PROD_DIR/prod.xtc" 2>/dev/null)
    SIZE_GB=$(echo "scale=1; $SIZE / 1073741824" | bc)
    if (( $(echo "$SIZE_GB >= 50" | bc -l) )); then
        echo "✓ Trajectory size: ${SIZE_GB} GB"
    else
        echo "⚠ Small trajectory: ${SIZE_GB} GB (expected ~100+ GB)"
    fi
fi

# Summary
echo ""
if [ "$ERRORS" -eq 0 ]; then
    echo "STATUS: PASS"
    exit 0
else
    echo "STATUS: FAIL ($ERRORS errors)"
    exit 1
fi
