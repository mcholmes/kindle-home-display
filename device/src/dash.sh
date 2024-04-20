#!/usr/bin/env sh
DEBUG=${DEBUG:-false}
[[ "$DEBUG" = true ]] && set -x

source logging.sh

DIR="$(dirname "$0")"

# Source environment variables
ENV_FILE="$DIR/local/env.sh"
[ -f "$ENV_FILE" ] && . "$ENV_FILE"

DASH_PNG="$DIR/dash.png"
FETCH_DASHBOARD_CMD="$DIR/local/fetch-dashboard.sh"
LOW_BATTERY_CMD="$DIR/local/low-battery.sh"

# REFRESH_SCHEDULE=${REFRESH_SCHEDULE:-"2,32 8-17 * * MON-FRI"}
FULL_DISPLAY_REFRESH_RATE=${FULL_DISPLAY_REFRESH_RATE:-0}
SLEEP_SCREEN_INTERVAL=${SLEEP_SCREEN_INTERVAL:-3600}
RTC=/sys/class/rtc/rtc1/wakealarm # for paperwhite 3
# RTC=/sys/devices/platform/mxc_rtc.0/wakeup_enable # for earlier kindle devices

LOW_BATTERY_REPORTING=${LOW_BATTERY_REPORTING:-false}
LOW_BATTERY_THRESHOLD_PERCENT=${LOW_BATTERY_THRESHOLD_PERCENT:-10}

num_refresh=0

optimise_power() {
  log_info "Optimising power usage."
  initctl stop framework >/dev/null 2>&1
  initctl stop webreader >/dev/null 2>&1
  echo powersave >/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
  lipc-set-prop com.lab126.powerd preventScreenSaver 1
}

display_sleep_screen() {
  log_info "Preparing sleep"

  /usr/sbin/eips -f -g "$DIR/sleeping.png"

  # Give screen time to refresh
  sleep 2

  # Ensure a full screen refresh is triggered after wake from sleep
  num_refresh=$FULL_DISPLAY_REFRESH_RATE
}

refresh_dashboard() {
  "$DIR/wait-for-wifi.sh" "$WIFI_TEST_IP"

  "$FETCH_DASHBOARD_CMD" "$DASH_PNG"
  fetch_status=$?

  if [ "$fetch_status" -ne 0 ]; then
    log_error "Not updating screen, fetch-dashboard returned $fetch_status"
    return 1
  fi

  if [ "$num_refresh" -eq "$FULL_DISPLAY_REFRESH_RATE" ]; then
    num_refresh=0

    # trigger a full refresh once in every 4 refreshes, to keep the screen clean
    log_info "Refreshing: full"
    /usr/sbin/eips -f -g "$DASH_PNG" >/dev/null
  else
    log_info "Refreshing: partial"
    /usr/sbin/eips -g "$DASH_PNG" >/dev/null
  fi

  num_refresh=$((num_refresh + 1))
}

log_battery_stats() {
  battery_level=$(gasgauge-info -c)
  log_info "Battery level: $battery_level."

  if [ "$LOW_BATTERY_REPORTING" = true ]; then
    battery_level_numeric=${battery_level%?}
    if [ "$battery_level_numeric" -le "$LOW_BATTERY_THRESHOLD_PERCENT" ]; then
      "$LOW_BATTERY_CMD" "$battery_level_numeric"
    fi
  fi
}

rtc_sleep() {
  duration=$1

  if [ "$DEBUG" = true ]; then
    sleep "$duration"
  else
    content=$(cat "$RTC")  # Read the content of the file
    if [ -z "$content" ] || [ "$content" -eq 0 ]; then  # Check if content is empty or zero
      echo -n "$duration" >"$RTC"
      echo "mem" >/sys/power/state
    else
      log_error "Couldn't use RTC; it contained $content."
      exit 1
    fi
  fi  
}

main_loop() {
  while true; do
    log_battery_stats

    next_wakeup_secs=$("$DIR/next-wakeup" --schedule="$REFRESH_SCHEDULE" --timezone="$TIMEZONE")

    if [ "$next_wakeup_secs" -gt "$SLEEP_SCREEN_INTERVAL" ]; then
      action="sleep"
      display_sleep_screen
    else
      action="suspend"
      refresh_dashboard
    fi

    # take a bit of time before going to sleep, so this process can be aborted
    sleep 10

    log_info "Going to $action, next wakeup in ${next_wakeup_secs}s"

    rtc_sleep "$next_wakeup_secs"
  done
}

# Running on loop. If DEBUG is true then it won't suspend the device between iterations.
if [ $# -eq 0 ]; then
  
  # Check parameters are set for loop
  if [ -z "$TIMEZONE" ] || [ -z "$REFRESH_SCHEDULE" ]; then
    echo "Missing required configuration. Timezone: ${TIMEZONE:-(not set)}, Schedule: ${REFRESH_SCHEDULE:-(not set)}."
    echo "Set this on command line or in $ENV_FILE."
    exit 1
  fi

  # Check RTC file exists
  if [ ! -e "$RTC" ]; then
    echo "Can't find the wake alarm at $RTC."
    exit 1
  fi

  log_info "Starting dashboard with $REFRESH_SCHEDULE refresh..."

  optimise_power
  main_loop

# Run once; no powersave
elif [ $# -eq 1 ] && [ "$1" = "--once" ]; then
  "$FETCH_DASHBOARD_CMD" "$DASH_PNG"
  /usr/sbin/eips -f -g "$DASH_PNG"
else
  echo "Invalid usage. To loop, use zero arguments. To run once, use --once."
  exit 1
fi