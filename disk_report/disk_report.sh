#!/bin/bash

# Set threshold (e.g., 80%)
THRESHOLD=80

# Log file path
LOG_FILE="disk_report.log"

# Get current date and time
NOW=$(date "+%Y-%m-%d %H:%M:%S")

# Get disk usage (only root / partition)
USAGE=$(df / | grep / | awk '{print $5}' | sed 's/%//')

# Write report to log
echo "[$NOW] Disk Usage: $USAGE%" >> "$LOG_FILE"

# Check if usage exceeds threshold
if [ "$USAGE" -gt "$THRESHOLD" ]; then
    echo "[$NOW] ⚠️ Warning: Disk usage above $THRESHOLD%!" >> "$LOG_FILE"
fi

# Optional: Print to terminal
echo "Report written to $LOG_FILE"
#!/bash/bin

#!/bin/bash

# Threshold for warning
THRESHOLD=80

# Get disk usage of root directory
USAGE=$(df / | grep / | awk '{print $5}' | sed 's/%//')

echo "Current disk usage is $USAGE%"

# Compare with threshold
if [ "$USAGE" -ge "$THRESHOLD" ]; then
  echo "WARNING: Disk usage has exceeded ${THRESHOLD}%"
else
  echo "Disk usage is under control."
fi


