#!/usr/bin/env sh

# This page is useful for low-level kindle operations: https://wiki.mobileread.com/wiki/Kindle_Touch_Hacking


DEBUG=${DEBUG:-false}
[[ "$DEBUG" = true ]] && set -x

DIR="$(dirname "$0")"

source "$DIR/logging.sh"

# Source environment variables
ENV_FILE="$DIR/local/env.sh"
[ -f "$ENV_FILE" ] && . "$ENV_FILE"

DASH_PNG="$DIR/dash.png"
FETCH_DASHBOARD_CMD="$DIR/local/fetch-dashboard.sh"
LOW_BATTERY_CMD="$DIR/local/low-battery.sh"

# REFRESH_SCHEDULE=${REFRESH_SCHEDULE:-"2,32 8-17 * * MON-FRI"}
FULL_DISPLAY_REFRESH_RATE=${FULL_DISPLAY_REFRESH_RATE:-0}
SLEEP_SCREEN_INTERVAL=${SLEEP_SCREEN_INTERVAL:-3600}


LOW_BATTERY_REPORTING=${LOW_BATTERY_REPORTING:-false}
LOW_BATTERY_THRESHOLD_PERCENT=${LOW_BATTERY_THRESHOLD_PERCENT:-10}


DEVICE_TYPE=PW3
num_refresh=0

#===================== End of configuration =====================#

# https://github.com/mattzzw/kindle-gphotos/blob/master/kindle-gphotos.sh
# https://github.com/mattzzw/kindle-clock/blob/master/kindle-clock.sh
FBROTATE=""
BACKLIGHT=""
RTC=""
case $DEVICE_TYPE in
    "K4")
        FBROTATE="echo 14 2 > /proc/eink_fb/update_display"
        BACKLIGHT="/dev/null"
        # No RTC?
        ;;
    "PW2")
        FBROTATE="echo -n 0 > /sys/devices/platform/mxc_epdc_fb/graphics/fb0/rotate"
        BACKLIGHT="/sys/devices/system/fl_tps6116x/fl_tps6116x0/fl_intensity"
        RTC=/sys/devices/platform/mxc_rtc.0/wakeup_enable
        ;;
    "PW3")
        FBROTATE="echo 0 > /sys/devices/platform/imx_epdc_fb/graphics/fb0/rotate"
        BACKLIGHT="/sys/devices/platform/imx-i2c.0/i2c-0/0-003c/max77696-bl.0/backlight/max77696-bl/brightness"
        RTC=/sys/class/rtc/rtc1/wakealarm
        ;;
    *)
        echo "Unrecognised device $DEVICE_TYPE. Must be K4, PW2 or PW3."
        ;;
esac

optimise_power() {
  log_info "Optimising power usage."
  
  echo powersave >/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor # put CPU into low-power mode
  echo -n 0 > $BACKLIGHT # disable light. min=0, max=3280 (corresponding to 25 on the GUI slider)
  
  case $DEVICE_TYPE in
    "K4")
        /etc/init.d/framework stop
        /etc/init.d/pmond stop
        /etc/init.d/phd stop
        /etc/init.d/cmd stop
        /etc/initd./tmd stop
        /etc/init.d/browserd stop
        /etc/init.d/webreaderd stop
        /etc/init.d/lipc-daemon stop
        /etc/init.d/powerd stop
        ;;
    "PW2" | "PW3")
        # TODO: which of these need doing? what about framework & webreader?
        # TODO: use initctl stop instead of stop?
        
        # The framework job sends a SIGTERM on stop, trap it so we don't get killed if we were launched by KUAL
        # https://www.mobileread.com/forums/showpost.php?p=2639195&postcount=5
        trap "" SIGTERM
        stop lab126_gui # main interface. #TODO: should this be framework instead?
        usleep 1250000 # so we don't start before the blank screen
        trap - SIGTERM
        
        stop webreader
        
        # OTA update related processes
        # https://www.mobileread.com/forums/showpost.php?p=2422385&postcount=6
        # https://www.mobileread.com/forums/showpost.php?p=2008593&postcount=13
        stop otaupd # over-the-air update
        stop phd # phone home
        stop tmd # transfer manager
        stop todo

        # # Don't know if I should stop these...
        # stop x 
        # stop mcsd
        # stop archive
        # stop dynconfig
        # stop dpmd 
        # stop appmgrd # application manager
        # stop stackdumpd
        ;;
    *)
        echo "Unrecognised device $DEVICE_TYPE. Must be K4, PW2 or PW3."
        ;;
  esac
  sleep 2
  
  ### turn off 270 degree rotation of framebuffer device. TODO: what is this? from kindle-clock
  # eval $FBROTATE
  
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

  # Re-enable wifi
  lipc-set-prop com.lab126.cmd wirelessEnable 1
  "$DIR/wait-for-wifi.sh" "$WIFI_TEST_IP"

  # Get image
  "$FETCH_DASHBOARD_CMD" "$DASH_PNG"
  fetch_status=$?

  if [ "$fetch_status" -ne 0 ]; then
    log_error "Not updating screen, fetch-dashboard returned $fetch_status"
    /usr/sbin/eips "Error retrieving dashboard!"
    return 1
  fi

  if [ "$num_refresh" -eq "$FULL_DISPLAY_REFRESH_RATE" ]; then
    # trigger a full refresh once in every 4 refreshes, to keep the screen clean
    num_refresh=0
    log_info "Refreshing: full"
    /usr/sbin/eips -f -g "$DASH_PNG" >/dev/null
  else
    log_info "Refreshing: partial"
    /usr/sbin/eips -g "$DASH_PNG" >/dev/null
  fi

  num_refresh=$((num_refresh + 1))

  # Disable wifi
  lipc-set-prop com.lab126.cmd wirelessEnable 0
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
    # lipc-set-prop -i com.lab126.powerd rtcWakeup "$duration" # doesn't seem to work. see https://www.mobileread.com/forums/showpost.php?p=3221077&postcount=7

    if [ $duration -lt 5 ]; then
        duration=60
    fi
    
    rtcwake -d /dev/rtc1 -m mem -s $duration
    
    # echo -n "$duration" >"$RTC"
    # echo "mem" >/sys/power/state # suspend to RAM

    # content=$(cat "$RTC")  # Read the content of the file
    # if [ -z "$content" ] || [ "$content" -eq 0 ]; then  # Check if content is empty or zero
    #   echo -n "$duration" >"$RTC"
    #   echo "mem" >/sys/power/state
    # else
    #   log_error "Couldn't use RTC; it contained $content."
    #   exit 1
    # fi
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

  lipc-set-prop com.lab126.powerd preventScreenSaver 1
  if [ "$DEBUG" = false ]; then

      # Check RTC file exists
    if [ ! -e "$RTC" ]; then
      echo "Can't find the wake alarm at $RTC."
      exit 1
    fi
    
    optimise_power
  fi 

  log_info "Starting dashboard with $REFRESH_SCHEDULE refresh..."
  main_loop

# Run once; no powersave
elif [ $# -eq 1 ] && [ "$1" = "--once" ]; then
  "$FETCH_DASHBOARD_CMD" "$DASH_PNG"
  /usr/sbin/eips -f -g "$DASH_PNG" >/dev/null
else
  echo "Invalid usage. To loop, use no arguments. To run once, use --once."
  exit 1
fi