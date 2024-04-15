#!/usr/bin/env sh

set -eu

APP="$(basename "$0" .sh)" # this file's name, without .sh extension
DIR="$(dirname "$0")"

ENV_FILE="$DIR/local/env.sh"

# [ -f "$ENV_FILE" ] && . "$ENV_FILE"

stop() {
    # Finds and kills this process.
    # Will only work if not suspending device to RAM .
    pid=$(pgrep -f "$(basename "$0")")

    if [ -z "$pid" ]; then
        echo "No matching processes found to kill."
    else
        echo "Killing: $pid"
        kill "$pid"
    fi
}

show_help() {
    local help_text="Usage: $0 [-h|--help] [COMMAND] [OPTIONS]
    
    Commands
        once    runs the program once
        start   runs the program in an infinite loop according to cron schedule
        stop    kills the program, if looping
        
    Options
        -l, --log-dir [dir]     Specify where to log the output; uses current directory if not specified.
        -n, --no-sleep          Don't optimise power-saving or suspend the device to memory
        -d, --debug             Print every script line to console before executing (i.e. -x)
        -h, --help              Show this help message"

    echo "$help_text"
}

# Variables to store option values
command=""
log_dir=""
no_sleep=false
debug=false


parse_args() {
    # Check if no arguments are provided
    if [[ $# -eq 0 ]]; then
        show_help
        exit 1
    fi

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --help|-h)
                show_help
                exit 0
                ;;
            --log-dir|-l)
                shift
                if [[ $# -eq 0 ]]; then
                    echo "Error: no log dir provided. use $1 path/to/dir."
                    exit 1
                fi
                log_dir=$1
                ;;
            --no-sleep|-n)
                no_sleep=true
                ;;
            --debug)
                debug=true
                ;;
            once|start|stop)
                command=$1
                ;;
            *)
                echo "Invalid usage. Use --help or -h to see the available commands and options."
                break
                ;;
        esac
        shift
    done
}

parse_args "$@"

# Debug mode
if [[ "$debug" ]]; then set -x; fi

# Handle logging
log_file="$DIR/$APP.log"
if [[ -n "$log_dir" ]]; then
    log_file="$log_dir/$APP.log"
    mkdir -p "$log_dir"
    echo "Logging output to $log_file"
fi

if [[ "$command" = "stop" ]]; then
    # TODO: stop() will kill this script. When the loop is started, will it be from another file instead?
    echo "stopping..."
fi

if [[ "$no_sleep" = true ]]; then
    echo "Not optimizing power-saving or suspending device to memory."
fi