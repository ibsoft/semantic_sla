#!/bin/bash

# Set variables
APP_NAME="run:app"  # The entry point of your app
HOST="0.0.0.0"
PORT="8008"
WORKERS=4
PID_FILE="gunicorn.pid"

# Function to start gunicorn
start_gunicorn() {
    echo "Starting Gunicorn..."
    # Check if Gunicorn is already running
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") > /dev/null 2>&1; then
        echo "Gunicorn is already running."
    else
        if [ "$2" == "background" ]; then
            gunicorn -w $WORKERS -b $HOST:$PORT $APP_NAME --pid $PID_FILE &
            echo "Gunicorn started in the background with PID $(cat $PID_FILE)."
        else
            gunicorn -w $WORKERS -b $HOST:$PORT $APP_NAME --pid $PID_FILE
            echo "Gunicorn started in the foreground with PID $(cat $PID_FILE)."
        fi
    fi
}

# Function to stop gunicorn
stop_gunicorn() {
    echo "Stopping Gunicorn..."
    # Check if Gunicorn is running
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        # Check if the process is still running
        if kill -0 $PID > /dev/null 2>&1; then
            kill $PID
            rm -f "$PID_FILE"
            echo "Gunicorn stopped (PID: $PID)."
        else
            echo "Gunicorn is not running."
            rm -f "$PID_FILE"
        fi
    else
        echo "No PID file found. Gunicorn may not be running."
    fi
}

# Function to show usage (check if gunicorn is running and show stats)
show_usage() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") > /dev/null 2>&1; then
        echo "Gunicorn is running with PID $(cat "$PID_FILE")"
        # Show usage (you can adjust this as needed)
        ps -p $(cat "$PID_FILE") -o %cpu,%mem,etime,cmd
    else
        echo "Gunicorn is not running."
    fi
}

# Show script usage
usage() {
    echo "Usage: $0 {start|stop|usage} [background]"
    echo "   start       Start Gunicorn (optional: 'background' to run in the background)"
    echo "   stop        Stop the running Gunicorn server"
    echo "   usage       Show usage statistics for Gunicorn"
    exit 1
}

# Main logic
case "$1" in
    start)
        start_gunicorn "$@"
        ;;
    stop)
        stop_gunicorn
        ;;
    usage)
        show_usage
        ;;
    *)
        usage
        ;;
esac
