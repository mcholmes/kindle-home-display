#!/usr/bin/env sh
test_ip=$1

DIR="$(dirname "$0")"

source "$DIR/logging.sh"

if [ -z "$test_ip" ]; then
    log_error -l ERROR "No test ip specified"
    exit 1
fi

wait_wlan_connected() {
  # shellcheck disable=SC2046
  return $(lipc-get-prop com.lab126.wifid cmState | grep CONNECTED | wc -l)
}

wait_wlan_ready() {
  # shellcheck disable=SC2046
  return $(lipc-get-prop com.lab126.wifid cmState | grep -e READY -e PENDING -e CONNECTED | wc -l)
}

wait_for_wifi() {
    max_retry=30
    counter=0

    ping -c 1 "$test_ip" >/dev/null 2>&1

    # shellcheck disable=SC2181
    while [ $? -ne 0 ]; do
        [ $counter -eq $max_retry ] && log_error "Couldn't connect to Wi-Fi" && exit 1
        counter=$((counter + 1))

        sleep 1
        ping -c 1 "$test_ip" >/dev/null 2>&1
    done
}

wait_for_wifi
log_info "Wi-Fi connected"