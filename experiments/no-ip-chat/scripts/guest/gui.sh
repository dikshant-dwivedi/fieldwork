#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
DISPLAY_NUMBER=":0"

require_root() {
  if [[ "$(id -u)" -ne 0 ]]; then
    echo "This script must run with sudo inside the disposable VM." >&2
    exit 1
  fi
}

unit_name() {
  echo "noip-chat-$1.service"
}

stop_unit() {
  systemctl stop "$(unit_name "$1")" 2>/dev/null || true
  systemctl reset-failed "$(unit_name "$1")" 2>/dev/null || true
}

stop_gui() {
  # Stop dependants before the display they use.
  for component in alice bob carol openbox xorg; do
    stop_unit "$component"
  done
}

start_service() {
  local component="$1"
  shift
  systemd-run --quiet --collect --unit="noip-chat-$component" --property=Type=simple -- "$@"
}

start_display() {
  if ! DISPLAY="$DISPLAY_NUMBER" xset q >/dev/null 2>&1; then
    # A terminated X server can leave a socket behind. It is safe to remove
    # only after xdpyinfo has proved there is no live display using it.
    rm -f /tmp/.X11-unix/X0
    start_service xorg Xorg "$DISPLAY_NUMBER" -ac -noreset -nolisten tcp
    for _ in {1..50}; do
      DISPLAY="$DISPLAY_NUMBER" xset q >/dev/null 2>&1 && break
      sleep 0.1
    done
  fi
  DISPLAY="$DISPLAY_NUMBER" xset q >/dev/null 2>&1 || {
    echo "Linux display did not start." >&2
    journalctl --no-pager -u "$(unit_name xorg)" -n 40 >&2
    exit 1
  }

  # VZ may expose a Retina-sized framebuffer (for example 2616×1636). A fixed
  # 1280×800 guest mode keeps text legible and makes the three-window layout
  # reproducible regardless of the host display's scale factor.
  output="$(DISPLAY="$DISPLAY_NUMBER" xrandr --query | awk '/ connected/{print $1; exit}')"
  DISPLAY="$DISPLAY_NUMBER" xrandr --output "$output" --mode 1280x800

  start_service openbox env DISPLAY="$DISPLAY_NUMBER" openbox
}

launch_participant() {
  local namespace="$1"
  local name="$2"
  local geometry="$3"
  start_service "$namespace" ip netns exec "noip-$namespace" \
    env DISPLAY="$DISPLAY_NUMBER" PYTHONDONTWRITEBYTECODE=1 \
    python3 "$PROJECT_DIR/src/gui.py" --name "$name" --geometry "$geometry"
}

assert_running() {
  local component="$1"
  systemctl is-active --quiet "$(unit_name "$component")" || {
    echo "$component UI component failed." >&2
    journalctl --no-pager -u "$(unit_name "$component")" -n 40 >&2
    exit 1
  }
}

start_gui() {
  stop_gui
  start_display
  launch_participant alice Alice "410x740+10+20"
  launch_participant bob Bob "410x740+435+20"
  launch_participant carol Carol "410x740+860+20"
  sleep 2
  for participant in xorg openbox alice bob carol; do
    assert_running "$participant"
  done
  echo "Opened Alice, Bob, and Carol inside the Linux VM display."
  echo "Select a discovered name, type a message, and press Send."
  echo "Run 'make gui-stop' when finished."
}

smoke_test() {
  stop_gui
  start_display
  launch_participant alice Alice "500x700+20+20"
  sleep 2
  assert_running xorg
  assert_running openbox
  assert_running alice
  stop_gui
  echo "PASS: Tkinter opened inside Alice's namespace on the Linux display."
}

require_root
case "${1:-}" in
  start) start_gui ;;
  stop) stop_gui; echo "Stopped No-IP Chat interface windows." ;;
  smoke) smoke_test ;;
  *) echo "Usage: $0 {start|stop|smoke}" >&2; exit 2 ;;
esac
