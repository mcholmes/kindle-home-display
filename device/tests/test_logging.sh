#!/usr/bin/env sh
# shellcheck source=src/logging.sh
. ./src/logging.sh

REFRESH_SCHEDULE=${REFRESH_SCHEDULE:-"2,32 8-17 * * MON-FRI"}

# Test log_info output
output=$(log_info "Starting dashboard with $REFRESH_SCHEDULE refresh..." 2>&1)
if ! echo "$output" | grep -q "INFO | Starting dashboard"; then
    echo "Error: log_info output format is incorrect: $output"
    exit 1
fi

# Test argument validation for log (should exit 1 when arguments != 2)
if (log 2>/dev/null); then
    echo "Error: log should exit with 1 when no arguments are provided"
    exit 1
fi

# Test argument validation for log_info (should exit 1 when arguments != 1)
if (log_info "too" "many" 2>/dev/null); then
    echo "Error: log_info should exit with 1 when too many arguments are provided"
    exit 1
fi

echo "test_logging.sh passed"
