#!/bin/bash
# check_warnings.sh - Scan log files for LINCS warnings and errors
# Usage: ./check_warnings.sh <prod.log>

LOG_FILE="$1"

if [ -z "$LOG_FILE" ]; then
    echo "Usage: $0 <prod.log>"
    exit 1
fi

if [ ! -f "$LOG_FILE" ]; then
    echo "ERROR: File not found: $LOG_FILE"
    exit 1
fi

echo "Scanning: $LOG_FILE"
echo "========================================"

# Count warnings
LINCS_WARN=$(grep -ci "LINCS warning" "$LOG_FILE" 2>/dev/null || echo 0)
SHAKE_WARN=$(grep -ci "SHAKE" "$LOG_FILE" 2>/dev/null || echo 0)
ERRORS=$(grep -ci "error" "$LOG_FILE" 2>/dev/null || echo 0)
WARNINGS=$(grep -ci "warning" "$LOG_FILE" 2>/dev/null || echo 0)

echo "LINCS warnings: $LINCS_WARN"
echo "SHAKE warnings: $SHAKE_WARN"
echo "Errors:         $ERRORS"
echo "General warnings: $WARNINGS"
echo ""

# Show LINCS details if any
if [ "$LINCS_WARN" -gt 0 ]; then
    echo "LINCS warning details:"
    echo "----------------------------------------"
    grep -i "LINCS warning" "$LOG_FILE" | head -10
    
    # Check for relative constraint deviation
    grep -A2 "relative constraint deviation" "$LOG_FILE" | head -20
    echo ""
fi

# Check for fatal errors
FATAL=$(grep -ci "fatal" "$LOG_FILE" 2>/dev/null || echo 0)
if [ "$FATAL" -gt 0 ]; then
    echo "FATAL ERRORS DETECTED:"
    echo "----------------------------------------"
    grep -i "fatal" "$LOG_FILE"
    echo ""
fi

# Check simulation completed
FINISHED=$(grep -c "Finished mdrun" "$LOG_FILE" 2>/dev/null || echo 0)
if [ "$FINISHED" -eq 1 ]; then
    echo "✓ Simulation completed successfully"
else
    echo "✗ Simulation may not have completed (no 'Finished mdrun' found)"
fi

# Extract performance
echo ""
echo "Performance:"
echo "----------------------------------------"
grep -E "Performance:|ns/day" "$LOG_FILE" | tail -2

# Summary
echo ""
echo "========================================"
if [ "$LINCS_WARN" -lt 10 ] && [ "$FATAL" -eq 0 ] && [ "$FINISHED" -eq 1 ]; then
    echo "✓ PASS: No critical issues"
    exit 0
elif [ "$LINCS_WARN" -lt 100 ] && [ "$FATAL" -eq 0 ]; then
    echo "⚠ WARNING: Some LINCS warnings, but simulation completed"
    exit 0
else
    echo "✗ FAIL: Critical issues detected"
    exit 1
fi
