#!/bin/bash
set -e

# Create log directory
mkdir -p ${LOG_DIR}

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput || echo "Warning: collectstatic failed or no static files to collect"

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput || echo "Warning: migrations failed"

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn \
    --bind 0.0.0.0:8000 \
    --workers ${GUNICORN_WORKERS:-4} \
    --threads ${GUNICORN_THREADS:-2} \
    --timeout ${GUNICORN_TIMEOUT:-30} \
    --access-logfile ${LOG_DIR}/access.log \
    --error-logfile ${LOG_DIR}/error.log \
    service_foundation.wsgi:application

