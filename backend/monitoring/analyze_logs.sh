#!/bin/bash
# HireWise Log Analysis Script

LOG_DIR="/home/*/Documents/HireWise/backend/logs"
REPORT_FILE="/tmp/hirewise-log-report.txt"

echo "HireWise Log Analysis Report - $(date)" > $REPORT_FILE
echo "=========================================" >> $REPORT_FILE

# Error count in last 24 hours
echo "Errors in last 24 hours:" >> $REPORT_FILE
find $LOG_DIR -name "*.log" -mtime -1 -exec grep -c "ERROR" {} + | awk '{sum+=$1} END {print "Total errors: " sum}' >> $REPORT_FILE

# Warning count in last 24 hours
echo "Warnings in last 24 hours:" >> $REPORT_FILE
find $LOG_DIR -name "*.log" -mtime -1 -exec grep -c "WARNING" {} + | awk '{sum+=$1} END {print "Total warnings: " sum}' >> $REPORT_FILE

# Top error messages
echo "Top error messages:" >> $REPORT_FILE
find $LOG_DIR -name "*.log" -mtime -1 -exec grep "ERROR" {} + | sort | uniq -c | sort -nr | head -10 >> $REPORT_FILE

# Security events
echo "Security events:" >> $REPORT_FILE
find $LOG_DIR -name "security.log" -mtime -1 -exec wc -l {} + >> $REPORT_FILE

echo "Report generated at: $(date)" >> $REPORT_FILE
cat $REPORT_FILE