#!/bin/bash

# Application control script: start, stop, restart
# Requires: run from project root, .env with APP_NAME

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load APP_NAME and LOG_DIR from .env
load_app_name() {
    if [ -f .env ]; then
        APP_NAME=$(grep -E "^APP_NAME=" .env 2>/dev/null | cut -d'=' -f2- | sed 's/^[[:space:]["'\'']*//;s/[[:space:]["'\'']*$//')
        LOG_DIR=$(grep -E "^LOG_DIR=" .env 2>/dev/null | cut -d'=' -f2- | sed 's/^[[:space:]["'\'']*//;s/[[:space:]["'\'']*$//')
    fi
    APP_NAME=${APP_NAME:-serv-fd}
    LOG_DIR=${LOG_DIR:-/var/log/serv-fd}
}

# PID file path: /var/run/<APP_NAME>/app.pid
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

# Resolve DEBUG the same way as Django: common.utils.env_util.load_env reads .env,
# then .env.dev | .env.test | .env.prod when RUN_ENV matches (overrides .env).
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

start() {
    load_app_name
    local pid_dir="/var/run/${APP_NAME}"
    local pid_file="${pid_dir}/app.pid"
    local django_log_path="${LOG_DIR}/django.log"

    if is_running; then
        echo "App is already running (PID: $(get_pid))"
        exit 1
    fi

    if [ ! -d "$pid_dir" ]; then
        mkdir -p "$pid_dir" || { echo "Error: cannot create $pid_dir (may need sudo)"; exit 1; }
    fi
    mkdir -p "$(dirname "$django_log_path")" || { echo "Error: cannot create log dir for $django_log_path"; exit 1; }

    maybe_collectstatic

    echo "Starting app (HOST/PORT/logging from .env via manage.py)..."
    echo "Django runserver output: $django_log_path"
    nohup python manage.py runserver >> "$django_log_path" 2>&1 &
    local pid=$!
    echo "$pid" > "$pid_file"
    echo "App started (PID: $pid)"
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

case "${1:-}" in
    start)   start ;;
    stop)    stop ;;
    restart) restart ;;
    status)  status ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
