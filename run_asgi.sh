#!/bin/bash

# Gunicorn + UvicornWorker (ASGI), same control model as run.sh:
#   nohup, PID under /var/run/<APP_NAME>/app.pid, HOST/PORT from .env (via load_env
#   rules aligned with manage.py), optional collectstatic when DEBUG=False.
# Requires: run from project root, .env with APP_NAME; gunicorn + uvicorn installed.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

ASGI_WORKERS=1

# Load APP_NAME and LOG_DIR from .env (light parse; same keys as run.sh)
load_app_name() {
    if [ -f .env ]; then
        APP_NAME=$(grep -E "^APP_NAME=" .env 2>/dev/null | cut -d'=' -f2- | sed 's/^[[:space:]["'\'']*//;s/[[:space:]["'\'']*$//')
        LOG_DIR=$(grep -E "^LOG_DIR=" .env 2>/dev/null | cut -d'=' -f2- | sed 's/^[[:space:]["'\'']*//;s/[[:space:]["'\'']*$//')
    fi
    APP_NAME=${APP_NAME:-serv-fd}
    LOG_DIR=${LOG_DIR:-/var/log/serv-fd}
}

get_pid_file() {
    load_app_name
    echo "/var/run/${APP_NAME}/app.pid"
}

get_pid() {
    local pid_file
    pid_file=$(get_pid_file)
    if [ -f "$pid_file" ]; then
        cat "$pid_file" 2>/dev/null || echo ""
    else
        echo ""
    fi
}

is_running() {
    local pid
    pid=$(get_pid)
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        return 0
    fi
    return 1
}

# Bind address HOST:PORT — same as manage.py runserver (load_env from project root)
_resolve_bind() {
    python -c "
from pathlib import Path
import os
import sys
root = Path(r'''${SCRIPT_DIR}''').resolve()
sys.path.insert(0, str(root))
from common.utils.env_util import load_env
load_env(root)
host = os.environ.get('HOST', '127.0.0.1')
port = os.environ.get('PORT', '8000')
print(f'{host}:{port}')
"
}

_collectstatic_action_from_env() {
    python -c "
from pathlib import Path
import sys
root = Path(r'''${SCRIPT_DIR}''').resolve()
sys.path.insert(0, str(root))
from common.utils.env_util import load_env
e = load_env(root)
print('collectstatic' if not e.bool('DEBUG', default=True) else 'skip')
"
}

maybe_collectstatic() {
    local action
    action=$(_collectstatic_action_from_env 2>/dev/null) || action=""
    if [ -z "$action" ]; then
        echo "Warning: could not resolve DEBUG (same rules as .env + RUN_ENV); skipping collectstatic."
        return 0
    fi
    if [ "$action" != "collectstatic" ]; then
        return 0
    fi
    echo "DEBUG=False: running collectstatic..."
    python manage.py collectstatic --noinput
}

_validate_workers() {
    local w="$1"
    if ! [[ "$w" =~ ^[1-9][0-9]*$ ]]; then
        echo "Error: workers must be a positive integer, got: $w"
        exit 1
    fi
}

start() {
    _validate_workers "$ASGI_WORKERS"
    load_app_name
    local pid_dir="/var/run/${APP_NAME}"
    local pid_file="${pid_dir}/app.pid"
    local log_path="${LOG_DIR}/gunicorn_asgi.log"

    if is_running; then
        echo "App is already running (PID: $(get_pid))"
        exit 1
    fi

    if [ ! -d "$pid_dir" ]; then
        mkdir -p "$pid_dir" || { echo "Error: cannot create $pid_dir (may need sudo)"; exit 1; }
    fi
    mkdir -p "$(dirname "$log_path")" || { echo "Error: cannot create log dir for $log_path"; exit 1; }

    maybe_collectstatic

    local bind
    bind=$(_resolve_bind) || { echo "Error: could not resolve bind address from .env"; exit 1; }

    echo "Starting Gunicorn ASGI (UvicornWorker), bind=$bind, workers=$ASGI_WORKERS"
    echo "Gunicorn output: $log_path"
    # Master PID is the backgrounded process (same as run.sh)
    nohup gunicorn service_foundation.asgi:application \
        -k uvicorn.workers.UvicornWorker \
        -w "$ASGI_WORKERS" \
        -b "$bind" \
        --chdir "$SCRIPT_DIR" \
        >> "$log_path" 2>&1 &
    local pid=$!
    echo "$pid" > "$pid_file"
    echo "App started (master PID: $pid)"
}

stop() {
    local pid
    pid=$(get_pid)
    local pid_file
    pid_file=$(get_pid_file)

    if [ -z "$pid" ]; then
        echo "App is not running (no PID file or empty)"
        [ -f "$pid_file" ] && rm -f "$pid_file"
        exit 0
    fi

    if ! kill -0 "$pid" 2>/dev/null; then
        echo "App process $pid not found (stale PID file), removing"
        rm -f "$pid_file"
        exit 0
    fi

    echo "Stopping app (PID: $pid)..."
    kill -TERM "$pid" 2>/dev/null || true
    local count=0
    while kill -0 "$pid" 2>/dev/null && [ $count -lt 15 ]; do
        sleep 1
        count=$((count + 1))
    done
    if kill -0 "$pid" 2>/dev/null; then
        echo "Force killing..."
        kill -KILL "$pid" 2>/dev/null || true
    fi
    rm -f "$pid_file"
    echo "App stopped"
}

restart() {
    stop
    sleep 2
    start
}

status() {
    if is_running; then
        echo "App is running (PID: $(get_pid))"
    else
        echo "App is not running"
        exit 1
    fi
}

print_usage() {
    echo "Usage: $0 {start|stop|restart|status} [workers]"
    echo "  workers: optional, default 1 (only used for start and restart)"
}

case "${1:-}" in
    start)   ASGI_WORKERS="${2:-1}"; start ;;
    stop)    stop ;;
    restart) ASGI_WORKERS="${2:-1}"; restart ;;
    status)  status ;;
    *)       print_usage; exit 1 ;;
esac
