#!/bin/bash
set -e

# Create log directory
mkdir -p ${LOG_DIR}

# Collect static files (required for WhiteNoise when DEBUG=False)
echo "Collecting static files..."
if python manage.py collectstatic --noinput; then
    echo "Static files collected successfully."
else
    echo "Warning: collectstatic failed - check that app static dirs exist (e.g. app_console/static/)"
fi

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput || echo "Warning: migrations failed"

# Start SMTP+IMAP when APP_MAILSERVER_ENABLED=true (same as run.sh / run_asgi.sh).
if python -c "
import os, sys
os.chdir('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'service_foundation.settings')
import django
django.setup()
from django.conf import settings
sys.exit(0 if settings.APP_MAILSERVER_ENABLED else 1)
" 2>/dev/null; then
    echo "Starting mail servers (SMTP/IMAP)..."
    nohup python -m app_mailserver >> ${LOG_DIR}/mail_server.log 2>&1 &
    MAIL_SERVER_PID=$!
    echo "Mail servers started with PID: $MAIL_SERVER_PID"

    sleep 2

    if ! kill -0 $MAIL_SERVER_PID 2>/dev/null; then
        echo "Warning: Mail server process exited early. Check logs in ${LOG_DIR}/mail_server.log"
    else
        echo "Mail servers are running (SMTP: ${MAIL_SMTP_PORT:-25}, IMAP: ${MAIL_IMAP_PORT:-143})"
    fi
else
    echo "Mail servers skipped (APP_MAILSERVER_ENABLED=false)"
    MAIL_SERVER_PID=""
fi

# Function to cleanup on exit
cleanup() {
    echo "Shutting down services..."
    # Send SIGTERM to mail server if it's running
    if [ ! -z "$MAIL_SERVER_PID" ] && kill -0 $MAIL_SERVER_PID 2>/dev/null; then
        echo "Stopping mail servers (PID: $MAIL_SERVER_PID)..."
        kill -TERM $MAIL_SERVER_PID 2>/dev/null || true
        # Wait a moment for graceful shutdown
        sleep 2
        # Force kill if still running
        if kill -0 $MAIL_SERVER_PID 2>/dev/null; then
            echo "Force killing mail servers..."
            kill -KILL $MAIL_SERVER_PID 2>/dev/null || true
        fi
        wait $MAIL_SERVER_PID 2>/dev/null || true
    fi
    # Send SIGTERM to Gunicorn (ASGI) if it's running
    if [ ! -z "$GUNICORN_PID" ] && kill -0 $GUNICORN_PID 2>/dev/null; then
        echo "Stopping Gunicorn (PID: $GUNICORN_PID)..."
        kill -TERM $GUNICORN_PID 2>/dev/null || true
        wait $GUNICORN_PID 2>/dev/null || true
    fi
    exit 0
}

# Set trap to cleanup on script exit
# When Docker sends SIGTERM, this will handle cleanup before exit
trap cleanup SIGTERM SIGINT

# HTTP: Gunicorn + UvicornWorker (ASGI), same stack as run_asgi.sh
# Bind and GUNICORN_WORKERS from .env / .env.<RUN_ENV> via load_env (precedence matches Django)
# Default HOST/PORT: 0.0.0.0:8000 (container listen), default workers: 1
{
  IFS= read -r ASGI_BIND
  IFS= read -r GUNICORN_WORKERS
} < <(python -c "
from pathlib import Path
import os
import sys
root = Path('/app')
sys.path.insert(0, str(root))
from common.utils.env_util import load_env
load_env(root)
h = os.environ.get('HOST', '0.0.0.0')
p = os.environ.get('PORT', '8000')
w = os.environ.get('GUNICORN_WORKERS', '1')
print(h + ':' + p)
print(w)
")
echo "Starting Gunicorn (ASGI, UvicornWorker) on ${ASGI_BIND}, workers=${GUNICORN_WORKERS}..."
gunicorn service_foundation.asgi:application \
  -k uvicorn.workers.UvicornWorker \
  -w "${GUNICORN_WORKERS}" \
  -b "${ASGI_BIND}" \
  --chdir /app \
  &
GUNICORN_PID=$!

# Wait for Gunicorn (this will block until it exits; trap handles SIGTERM to mail + Gunicorn)
wait $GUNICORN_PID
