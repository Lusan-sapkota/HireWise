#!/bin/bash
# HireWise Health Check Monitor

HEALTH_URL="http://localhost:8000/api/health/"
LOG_FILE="/tmp/hirewise-health.log"
ALERT_THRESHOLD=3

check_health() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local response=$(curl -s -w "%{http_code}" -o /tmp/health_response.json "$HEALTH_URL")
    local http_code="${response: -3}"
    
    if [ "$http_code" = "200" ]; then
        echo "[$timestamp] HEALTHY - HTTP $http_code" >> "$LOG_FILE"
        return 0
    else
        echo "[$timestamp] UNHEALTHY - HTTP $http_code" >> "$LOG_FILE"
        return 1
    fi
}

# Main monitoring loop
failure_count=0
while true; do
    if check_health; then
        failure_count=0
    else
        failure_count=$((failure_count + 1))
        
        if [ $failure_count -ge $ALERT_THRESHOLD ]; then
            echo "ALERT: HireWise health check failed $failure_count times"
            # Add notification logic here (email, Slack, etc.)
        fi
    fi
    
    sleep 60  # Check every minute
done