#!/usr/bin/env sh
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$DIR/../src/local/env.sh"

. "$ENV_FILE"

# Assert variables are exported correctly
if [ -z "$DASHBOARD_URL" ]; then
    echo "Error: DASHBOARD_URL is not set"
    exit 1
fi

if [ "$DASHBOARD_URL" != "http://192.168.3.137:8000/dashboard" ]; then
    echo "Error: DASHBOARD_URL has unexpected value: $DASHBOARD_URL"
    exit 1
fi

if [ "$TIMEZONE" != "Europe/London" ]; then
    echo "Error: TIMEZONE has unexpected value: $TIMEZONE"
    exit 1
fi

echo "test_env.sh passed"
