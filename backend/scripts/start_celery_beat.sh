#!/bin/bash
# Start Celery beat scheduler for HireWise
echo "Starting Celery beat scheduler..."
celery -A hirewise beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
