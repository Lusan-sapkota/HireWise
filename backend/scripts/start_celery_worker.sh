#!/bin/bash
# Start Celery worker for HireWise
echo "Starting Celery worker..."
celery -A hirewise worker --loglevel=info --concurrency=2
