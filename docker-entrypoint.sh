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

# Start mail servers (SMTP and IMAP) in background if enabled
if [ "${START_MAIL_SERVER:-true}" = "true" ]; then
    echo "Starting mail servers (SMTP/IMAP)..."
    # Start mail server in background
    # Use nohup and redirect output to log file
    nohup python manage.py start_mail_server >> ${LOG_DIR}/mail_server.log 2>&1 &
    MAIL_SERVER_PID=$!
    echo "Mail servers started with PID: $MAIL_SERVER_PID"
    
    # Wait a moment for mail servers to start
    sleep 2
    
    # Check if mail server process is still running
    if ! kill -0 $MAIL_SERVER_PID 2>/dev/null; then
        echo "Warning: Mail server process exited early. Check logs in ${LOG_DIR}/mail_server.log"
    else
        echo "Mail servers are running (SMTP: ${MAIL_SMTP_PORT:-25}, IMAP: ${MAIL_IMAP_PORT:-143})"
    fi
else
    echo "Mail servers disabled (START_MAIL_SERVER=false)"
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
    # Send SIGTERM to Django server if it's running
    if [ ! -z "$DJANGO_PID" ] && kill -0 $DJANGO_PID 2>/dev/null; then
        echo "Stopping Django server (PID: $DJANGO_PID)..."
        kill -TERM $DJANGO_PID 2>/dev/null || true
        wait $DJANGO_PID 2>/dev/null || true
    fi
    exit 0
}

# Set trap to cleanup on script exit
# When Docker sends SIGTERM, this will handle cleanup before exit
trap cleanup SIGTERM SIGINT

# Start Django development server in background (so we can manage it)
# Note: Using Django's runserver for container deployment
echo "Starting Django development server on ${HOST:-0.0.0.0}:${PORT:-8000}..."
python manage.py runserver ${HOST:-0.0.0.0}:${PORT:-8000} &
DJANGO_PID=$!

# Wait for Django server process (this will block until it exits)
# When Django exits, the cleanup function will be called via trap
wait $DJANGO_PID
