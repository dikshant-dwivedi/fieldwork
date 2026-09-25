#!/usr/bin/env bash
set -euo pipefail

# The final exhibit uses a separate instance so Lima applies the native-display
# configuration even when an earlier checkpoint's headless VM already exists.
INSTANCE="noip-chat-ui"
PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
CONFIG="$PROJECT_DIR/infrastructure/lima.yaml"

instance_exists() {
  limactl list --format '{{.Name}}' 2>/dev/null | grep -Fxq "$INSTANCE"
}

ensure_vm() {
  if ! instance_exists; then
    echo "Creating the $INSTANCE VM from the pinned Ubuntu image..."
    limactl create --name "$INSTANCE" --tty=false "$CONFIG"
  fi
  limactl start "$INSTANCE" >/dev/null
}

guest() {
  limactl shell --tty=false --workdir "$PROJECT_DIR" "$INSTANCE" "$@"
}

guest_interactive() {
  # Interactive chat keeps Lima's terminal allocation so typed input, Ctrl-C,
  # and the small amount of terminal formatting behave normally.
  limactl shell --workdir "$PROJECT_DIR" "$INSTANCE" "$@"
}

case "${1:-}" in
  setup)
    "$PROJECT_DIR/scripts/host/doctor.sh"
    ensure_vm
    guest sudo ./scripts/guest/lab.sh create
    ;;
  test)
    ensure_vm
    guest env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
      python3 -m unittest discover -s tests -v
    ;;
  demo)
    ensure_vm
    cat <<EOF
Open four terminal windows in:
  $PROJECT_DIR

Run in terminal 1:
  make chat-alice

Run in terminal 2:
  make chat-bob

Run in terminal 3:
  make chat-carol

Run in terminal 4:
  make observe-switch

Each app periodically broadcasts only a small HELLO announcement. Run /peers
and /to NAME after discovery. CHAT frames remain one-to-one unicast.

Run `make verify` for the scripted proof that Bob discovers Alice by name and
his direct message does not cross Carol's switch port.
EOF
    ;;
  gui)
    ensure_vm
    guest sudo ./scripts/guest/gui.sh start
    ;;
  gui-stop)
    ensure_vm
    guest sudo ./scripts/guest/gui.sh stop
    ;;
  gui-smoke)
    ensure_vm
    guest sudo ./scripts/guest/gui.sh smoke
    ;;
  verify)
    ensure_vm
    guest sudo ./scripts/guest/verify.sh
    ;;
  topology)
    ensure_vm
    guest sudo ./scripts/guest/lab.sh topology
    ;;
  switch-table)
    ensure_vm
    guest sudo ./scripts/guest/lab.sh switch-table
    ;;
  observe-switch)
    ensure_vm
    guest_interactive sudo ./scripts/guest/observe_switch.sh
    ;;
  clean)
    if instance_exists; then
      limactl start "$INSTANCE" >/dev/null
      guest sudo ./scripts/guest/lab.sh destroy
    fi
    echo "Removed the No-IP Chat namespaces and switch; the reusable VM was kept."
    ;;
  listen)
    ensure_vm
    guest_interactive sudo ip netns exec noip-bob env PYTHONDONTWRITEBYTECODE=1 \
      python3 ./src/receive_frame.py --timeout 60
    ;;
  send)
    ensure_vm
    guest sudo ip netns exec noip-alice env PYTHONDONTWRITEBYTECODE=1 \
      python3 ./src/send_frame.py --destination 02:00:00:00:00:02
    ;;
  chat-alice)
    ensure_vm
    guest_interactive sudo ip netns exec noip-alice env PYTHONDONTWRITEBYTECODE=1 \
      python3 ./src/chat.py --name Alice
    ;;
  chat-bob)
    ensure_vm
    guest_interactive sudo ip netns exec noip-bob env PYTHONDONTWRITEBYTECODE=1 \
      python3 ./src/chat.py --name Bob
    ;;
  chat-carol)
    ensure_vm
    guest_interactive sudo ip netns exec noip-carol env PYTHONDONTWRITEBYTECODE=1 \
      python3 ./src/chat.py --name Carol
    ;;
  *)
    echo "Usage: $0 {setup|test|demo|verify|gui|gui-stop|gui-smoke|topology|switch-table|observe-switch|clean|listen|send|chat-alice|chat-bob|chat-carol}" >&2
    exit 2
    ;;
esac
