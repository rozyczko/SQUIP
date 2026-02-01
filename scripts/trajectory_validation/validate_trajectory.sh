#!/bin/bash
# validate_trajectory.sh - Validate a single production trajectory
# Usage: ./validate_trajectory.sh <production_dir> <output_prefix>

set -e

PROD_DIR="$1"
OUTPUT_PREFIX="$2"

if [ -z "$PROD_DIR" ] || [ -z "$OUTPUT_PREFIX" ]; then
    echo "Usage: $0 <production_dir> <output_prefix>"
    exit 1
fi

echo "Validating: $PROD_DIR"

# Check required files
for f in prod.xtc prod.edr prod.log prod.tpr; do
    if [ ! -f "$PROD_DIR/$f" ]; then
        echo "ERROR: Missing $f"
        exit 1
    fi
done

cd "$PROD_DIR"
REPORT="${OUTPUT_PREFIX}_report.txt"

echo "Trajectory Validation Report" > "$REPORT"
echo "Directory: $PROD_DIR" >> "$REPORT"
echo "Date: $(date)" >> "$REPORT"
echo "========================================" >> "$REPORT"

# 1. Check trajectory completeness
echo "" >> "$REPORT"
echo "1. TRAJECTORY COMPLETENESS" >> "$REPORT"
echo "----------------------------------------" >> "$REPORT"
gmx check -f prod.xtc 2>&1 | grep -E "Last frame|Coords|Step|Reading frame" | tail -5 >> "$REPORT"

# Get last time
LAST_TIME=$(gmx check -f prod.xtc 2>&1 | grep "Last frame" | awk '{print $4}')
echo "Last time: $LAST_TIME ps" >> "$REPORT"

# Check if >= 19900 ps (19.9 ns)
if (( $(echo "$LAST_TIME >= 19900" | bc -l) )); then
    echo "Status: PASS (>= 19.9 ns)" >> "$REPORT"
else
    echo "Status: FAIL (< 19.9 ns)" >> "$REPORT"
fi

# 2. Check frame spacing
echo "" >> "$REPORT"
echo "2. FRAME SPACING (should be 10 fs = 0.010 ps)" >> "$REPORT"
echo "----------------------------------------" >> "$REPORT"

# Get first 5 frame times
gmx dump -f prod.xtc 2>&1 | grep "time=" | head -5 >> "$REPORT" 2>/dev/null || echo "Could not extract frame times" >> "$REPORT"

# 3. Extract thermodynamic properties
echo "" >> "$REPORT"
echo "3. THERMODYNAMIC PROPERTIES" >> "$REPORT"
echo "----------------------------------------" >> "$REPORT"

# Temperature (item 16 in gmx energy)
echo "16 0" | gmx energy -f prod.edr -o "${OUTPUT_PREFIX}_temperature.xvg" 2>/dev/null
T_AVG=$(grep -v "^[#@]" "${OUTPUT_PREFIX}_temperature.xvg" | awk '{sum+=$2; n++} END {print sum/n}')
T_STD=$(grep -v "^[#@]" "${OUTPUT_PREFIX}_temperature.xvg" | awk -v avg="$T_AVG" '{sum+=($2-avg)^2; n++} END {print sqrt(sum/n)}')
echo "Temperature: $T_AVG +/- $T_STD K" >> "$REPORT"

# Pressure (item 18)
echo "18 0" | gmx energy -f prod.edr -o "${OUTPUT_PREFIX}_pressure.xvg" 2>/dev/null
P_AVG=$(grep -v "^[#@]" "${OUTPUT_PREFIX}_pressure.xvg" | awk '{sum+=$2; n++} END {print sum/n}')
P_STD=$(grep -v "^[#@]" "${OUTPUT_PREFIX}_pressure.xvg" | awk -v avg="$P_AVG" '{sum+=($2-avg)^2; n++} END {print sqrt(sum/n)}')
echo "Pressure: $P_AVG +/- $P_STD bar" >> "$REPORT"

# Density (item 24)
echo "24 0" | gmx energy -f prod.edr -o "${OUTPUT_PREFIX}_density.xvg" 2>/dev/null
D_AVG=$(grep -v "^[#@]" "${OUTPUT_PREFIX}_density.xvg" | awk '{sum+=$2; n++} END {print sum/n}')
D_STD=$(grep -v "^[#@]" "${OUTPUT_PREFIX}_density.xvg" | awk -v avg="$D_AVG" '{sum+=($2-avg)^2; n++} END {print sqrt(sum/n)}')
echo "Density: $D_AVG +/- $D_STD kg/m³" >> "$REPORT"

# Total Energy (item 12)
echo "12 0" | gmx energy -f prod.edr -o "${OUTPUT_PREFIX}_total_energy.xvg" 2>/dev/null
E_AVG=$(grep -v "^[#@]" "${OUTPUT_PREFIX}_total_energy.xvg" | awk '{sum+=$2; n++} END {print sum/n}')
echo "Total Energy: $E_AVG kJ/mol" >> "$REPORT"

# 4. Check for warnings
echo "" >> "$REPORT"
echo "4. WARNINGS AND ERRORS" >> "$REPORT"
echo "----------------------------------------" >> "$REPORT"
WARNINGS=$(grep -ci "warning\|error\|LINCS" prod.log 2>/dev/null || echo "0")
echo "Total warnings/errors found: $WARNINGS" >> "$REPORT"

if [ "$WARNINGS" -gt 0 ]; then
    echo "" >> "$REPORT"
    echo "Warning details:" >> "$REPORT"
    grep -i "warning\|error\|LINCS" prod.log | head -20 >> "$REPORT"
fi

# 5. Performance summary
echo "" >> "$REPORT"
echo "5. PERFORMANCE" >> "$REPORT"
echo "----------------------------------------" >> "$REPORT"
grep -E "Performance:|Wall t|Core t" prod.log | tail -5 >> "$REPORT"

# 6. File sizes
echo "" >> "$REPORT"
echo "6. FILE SIZES" >> "$REPORT"
echo "----------------------------------------" >> "$REPORT"
ls -lh prod.xtc prod.edr prod.log prod.gro 2>/dev/null >> "$REPORT"

echo "" >> "$REPORT"
echo "========================================" >> "$REPORT"
echo "Validation complete" >> "$REPORT"

echo "  Report saved: $REPORT"
echo "  Temperature: $T_AVG K"
echo "  Pressure: $P_AVG bar"
echo "  Density: $D_AVG kg/m³"
