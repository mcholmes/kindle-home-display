#!/usr/bin/env sh
set -eu

DEBUG=${DEBUG:-false}
[ "$DEBUG" = true ] && set -x

DIR="$(dirname "$0")"

# Set up logging
LOG_FILE="$DIR/logs/dash.log"
mkdir -p "$(dirname "$LOG_FILE")"

if [ "$DEBUG" = true ]; then
  "$DIR/dash.sh"
else
  # Run in background & log to file instead of console
  "$DIR/dash.sh" >>"$LOG_FILE" 2>&1 &
fi