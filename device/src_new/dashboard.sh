#!/usr/bin/env sh

APP="$(basename "$0" .sh)" # this file's name, without .sh extension
DIR="$(dirname "$0")"

ENV_FILE="$DIR/local/env.sh"
LOG_FILE="$DIR/logs/$APP.log"

mkdir -p "$(dirname "$LOG_FILE")"

# shellcheck disable=SC1090
[ -f "$ENV_FILE" ] && . "$ENV_FILE"

# if [ "$DEBUG" = true ]; then
#   # don't run in background. Will also set -x in dash.sh
#   "$DIR/dash.sh" >>"$LOG_FILE" 2>&1
# else
#   "$DIR/dash.sh" >>"$LOG_FILE" 2>&1 &
# fi

# Define functions for start and stop commands
start() {
    local debug=false
    local once=false
    local no_sleep=false

    # Parse options
    while [[ "$#" -gt 0 ]]; do
        case "$1" in
            --debug)
                set -x
                debug=true
                ;;
            --once)
                once=true
                ;;
            --no-sleep)
                no_sleep=true
                ;;   
            *)
                echo "Unknown option: $1"
                echo "Use $0 --help to see usage"
                exit 1
                ;;
        esac
        shift
    done

    # Start your application here, using the parsed options as needed
    echo "Starting application..."
    echo "Debug mode: $debug"
    echo "Run once: $once"
    echo "No sleep: $no_sleep"
}
  
stop() {
    # Finds and kills this 
    pid=$(pgrep -f "$(basename "$0")")

    if [ -z "$pid" ]; then
        echo "No matching processes found to kill."
    else
        echo "Killing: $pid"
        kill "$pid"
    fi
}

#TODO: remove; for testing only
infinite_loop() {
    while true; do
        sleep 10
    done
}

help() {
    echo "Usage: $0 <start|stop> [options]"
    echo "Options for start:"
    echo "  --debug        Run in debug mode"
    echo "  --once         Run once and exit"
    echo "  --no-sleep     Do not suspend the device to memory between iterations"
    echo "  --help, -h     Show this help message"    
}

# Parse the command
case "$1" in
    loop)
        infinite_loop
        ;;
    start)
        shift
        start "$@"
        ;;
    stop)
        stop
        ;;
    -h|--help)
        help
        exit 0
        ;;
    *)
        help
        exit 1
        ;;
esac




