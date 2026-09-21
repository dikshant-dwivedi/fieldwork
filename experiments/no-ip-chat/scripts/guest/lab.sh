#!/usr/bin/env bash
set -euo pipefail

ALICE_NAMESPACE="noip-alice"
BOB_NAMESPACE="noip-bob"
BRIDGE="br-noip"
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
  ip link delete "$BRIDGE" 2>/dev/null || true
}

create_lab() {
  require_root
  destroy_lab

  # The bridge is Linux's software Ethernet switch. It has no IP address and
  # learns source MAC -> incoming port. It sends a known destination through
  # only that destination's port. For an unknown destination, it floods every
  # OTHER port, never the one the frame arrived on. Receiving a flooded copy
  # does not teach the switch where that receiver lives; it must send a frame.
  # With only Alice and Bob, flooding and choosing the sole other port look
  # identical. Carol will make the difference observable.
  ip link add "$BRIDGE" type bridge
  sysctl -q -w "net.ipv6.conf.${BRIDGE}.disable_ipv6=1"
  ip address flush dev "$BRIDGE"
  ip link set "$BRIDGE" up

  ip netns add "$ALICE_NAMESPACE"
  ip netns add "$BOB_NAMESPACE"

  # Each veth pair is one cable. Its two named interfaces are the cable ends:
  # a computer's NIC at one end and a numbered switch port at the other.
  ip link add alice-nic type veth peer name port1
  ip link add bob-nic type veth peer name port2
  ip link set alice-nic netns "$ALICE_NAMESPACE"
  ip link set bob-nic netns "$BOB_NAMESPACE"
  configure_switch_port port1
  configure_switch_port port2

  configure_endpoint "$ALICE_NAMESPACE" alice-nic "$ALICE_MAC"
  configure_endpoint "$BOB_NAMESPACE" bob-nic "$BOB_MAC"

  echo "Connected Alice and Bob to the br-noip software switch."
  show_topology
}

configure_switch_port() {
  local port="$1"
  sysctl -q -w "net.ipv6.conf.${port}.disable_ipv6=1"
  ip address flush dev "$port"
  ip link set "$port" master "$BRIDGE"
  ip link set "$port" up
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
  echo "Switch and ports:"
  ip -brief address show dev "$BRIDGE"
  ip -brief link show master "$BRIDGE"
  echo
  echo "Alice namespace:"
  ip -n "$ALICE_NAMESPACE" -brief address show dev eth0
  echo "Bob namespace:"
  ip -n "$BOB_NAMESPACE" -brief address show dev eth0
  echo
  echo "Empty address columns show that the switch and chat interfaces have no IP."
  show_switch_table
}

show_switch_table() {
  echo
  echo "Dynamically learned switch entries:"
  local learned
  learned="$(bridge fdb show br "$BRIDGE" | grep -v permanent || true)"
  if [[ -n "$learned" ]]; then
    echo "$learned"
  else
    echo "  (none yet; the switch learns from source MACs in arriving frames)"
  fi
}

case "${1:-}" in
  create) create_lab ;;
  destroy) require_root; destroy_lab ;;
  topology) show_topology ;;
  switch-table) show_switch_table ;;
  *) echo "Usage: $0 {create|destroy|topology|switch-table}" >&2; exit 2 ;;
esac
