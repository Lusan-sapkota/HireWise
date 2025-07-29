#!/bin/bash
# HireWise Master Monitoring Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"

echo "🔍 HireWise Monitoring Suite"
echo "============================"

case "${1:-dashboard}" in
    "dashboard")
        echo "📊 Running monitoring dashboard..."
        python3 "$SCRIPT_DIR/dashboard.py"
        ;;
    "health")
        echo "🏥 Running health checks..."
        cd "$BASE_DIR" && python3 manage.py health_check
        ;;
    "performance")
        echo "⚡ Running performance monitoring..."
        duration=${2:-10}
        python3 "$SCRIPT_DIR/performance_monitor.py" $duration
        ;;
    "errors")
        echo "🚨 Running error tracking..."
        hours=${2:-1}
        python3 "$SCRIPT_DIR/error_tracker.py" $hours
        ;;
    "logs")
        echo "📋 Running log analysis..."
        bash "$SCRIPT_DIR/analyze_logs.sh"
        ;;
    "all")
        echo "🔄 Running all monitoring checks..."
        echo
        python3 "$SCRIPT_DIR/dashboard.py"
        echo
        cd "$BASE_DIR" && python3 manage.py health_check --format=text
        echo
        python3 "$SCRIPT_DIR/error_tracker.py" 1
        ;;
    *)
        echo "Usage: $0 {dashboard|health|performance|errors|logs|all}"
        echo
        echo "Commands:"
        echo "  dashboard    - Show monitoring dashboard (default)"
        echo "  health       - Run health checks"
        echo "  performance  - Run performance monitoring [duration_minutes]"
        echo "  errors       - Run error tracking [hours_back]"
        echo "  logs         - Analyze logs"
        echo "  all          - Run all monitoring checks"
        exit 1
        ;;
esac