#!/usr/bin/env bash
set -euo pipefail

ALICE_NAMESPACE="noip-alice"
BOB_NAMESPACE="noip-bob"
ALICE_MAC="02:00:00:00:00:01"
BOB_MAC="02:00:00:00:00:02"

require_root() {
  if [[ "$(id -u)" -ne 0 ]]; then
    echo "This script must run with sudo inside the disposable VM." >&2
    exit 1
  fi
}

destroy_lab() {
  ip netns delete "$ALICE_NAMESPACE" 2>/dev/null || true
  ip netns delete "$BOB_NAMESPACE" 2>/dev/null || true
}

create_lab() {
  require_root
  destroy_lab

  # The veth pair is the virtual cable. alice-nic and bob-nic are the two
  # interface ends of that cable, like NICs plugged into opposite ends.
  ip netns add "$ALICE_NAMESPACE"
  ip netns add "$BOB_NAMESPACE"
  ip link add alice-nic type veth peer name bob-nic
  ip link set alice-nic netns "$ALICE_NAMESPACE"
  ip link set bob-nic netns "$BOB_NAMESPACE"

  configure_endpoint "$ALICE_NAMESPACE" alice-nic "$ALICE_MAC"
  configure_endpoint "$BOB_NAMESPACE" bob-nic "$BOB_MAC"

  echo "Created one virtual cable between Alice and Bob."
  show_topology
}

configure_endpoint() {
  local namespace="$1"
  local original_name="$2"
  local mac="$3"

  ip -n "$namespace" link set "$original_name" name eth0
  ip -n "$namespace" link set eth0 address "$mac"

  # Disable IPv6 before raising the interface so Linux never assigns a
  # link-local IPv6 address. We deliberately assign no IPv4 address either.
  ip netns exec "$namespace" sysctl -q -w net.ipv6.conf.eth0.disable_ipv6=1
  ip -n "$namespace" address flush dev eth0
  ip -n "$namespace" link set eth0 up
}

show_topology() {
  echo
  echo "Alice namespace:"
  ip -n "$ALICE_NAMESPACE" -brief address show dev eth0
  echo "Bob namespace:"
  ip -n "$BOB_NAMESPACE" -brief address show dev eth0
  echo
  echo "The empty address columns are evidence that neither chat interface has IP."
}

case "${1:-}" in
  create) create_lab ;;
  destroy) require_root; destroy_lab ;;
  topology) show_topology ;;
  *) echo "Usage: $0 {create|destroy|topology}" >&2; exit 2 ;;
esac
