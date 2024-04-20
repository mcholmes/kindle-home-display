#!/usr/bin/env sh

log() {
    
    if [[ $# -ne 2 ]]; then
        echo "Incorrect number of arguments. Usage: log [LEVEL] [MESSAGE]"
        exit 1
    fi
    
    level=$1
    message=$2
    timestamp="$(date +'%Y-%m-%d %H:%M:%S')"
    script_name="$(basename "$0")"

    echo "$timestamp | $script_name | $level | $message"
}

log_error() {
    log "ERROR" "$1"
}

log_warning() {
    log "WARNING" "$1"
}

log_info() {
    log "INFO" "$1"
}

log_debug() {
    log "DEBUG" "$1"
}