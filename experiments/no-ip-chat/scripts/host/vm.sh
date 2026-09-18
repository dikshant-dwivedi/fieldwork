#!/usr/bin/env bash
set -euo pipefail

INSTANCE="noip-chat"
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
  demo|verify)
    ensure_vm
    guest sudo ./scripts/guest/verify.sh
    ;;
  topology)
    ensure_vm
    guest sudo ./scripts/guest/lab.sh topology
    ;;
  clean)
    if instance_exists; then
      limactl start "$INSTANCE" >/dev/null
      guest sudo ./scripts/guest/lab.sh destroy
    fi
    echo "Removed checkpoint 1 namespaces; the reusable VM was kept."
    ;;
  listen)
    ensure_vm
    guest sudo ip netns exec noip-bob env PYTHONDONTWRITEBYTECODE=1 \
      python3 ./src/receive_frame.py --timeout 60
    ;;
  send)
    ensure_vm
    guest sudo ip netns exec noip-alice env PYTHONDONTWRITEBYTECODE=1 \
      python3 ./src/send_frame.py --destination 02:00:00:00:00:02
    ;;
  *)
    echo "Usage: $0 {setup|test|demo|verify|topology|clean|listen|send}" >&2
    exit 2
    ;;
esac
