#!/usr/bin/env sh
# Fetch a new dashboard image, make sure to output it to "$1".
# For example:
# "$(dirname "$0")/../xh" -d -q -o "$1" get https://raw.githubusercontent.com/pascalw/kindle-dash/master/example/example.png
# cat /mnt/us/documents/dashboard.png >"$1"
if error_msg=$(curl -sS "$DASHBOARD_URL" -o "$1.tmp" 2>&1); then
    mv "$1.tmp" "$1"
    exit 0
else
    echo "$error_msg"
    exit 1
fi
