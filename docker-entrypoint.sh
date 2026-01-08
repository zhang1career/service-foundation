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

# Start Django development server
# Note: Using Django's runserver for container deployment
echo "Starting Django development server..."
exec python manage.py runserver ${HOST:-0.0.0.0}:${PORT:-8000}
