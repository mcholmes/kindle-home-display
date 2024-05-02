#!/usr/bin/env sh

log() {

    if [[ $# -ne 2 ]]; then
        echo "Incorrect number of arguments; expected 2 but got $#. Usage: log [LEVEL] [MESSAGE]"
    
        if [[ $# -gt 0 ]]; then
            echo "Arguments given: $*"
        fi
        exit 1
    fi
    
    level=$1
    message=$2
    timestamp="$(date +'%Y-%m-%d %H:%M:%S')"
    script_name="$(basename "$0")"

    echo "$timestamp | $script_name | $level | $message"
}

check_args() {
    if [[ $# -ne 1 ]]; then
        echo "Incorrect number of arguments; expected 2 but got $#. Usage: [log_error|log_warning|log_info|log_debug] [MESSAGE]"
        if [[ $# -gt 1 ]]; then
            echo "Arguments given: $*"
        fi
    exit 1
    fi
}

log_error() {
    check_args "$@"
    log "ERROR" "$1"
}

log_warning() {
    check_args "$@"
    log "WARNING" "$1"
}

log_info() {
    check_args "$@"
    log "INFO" "$1"
}

log_debug() {
    check_args "$@"
    log "DEBUG" "$1"
}