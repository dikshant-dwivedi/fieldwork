#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
ALICE_MAC="02:00:00:00:00:01"
BOB_MAC="02:00:00:00:00:02"
ALICE_MESSAGE="hello-from-alice"
BOB_MESSAGE="hello-from-bob"

fail() {
  echo "FAIL: $1" >&2
  exit 1
}

interface_has_no_ip() {
  local namespace="$1"
  [[ -z "$(ip -n "$namespace" -o address show dev eth0)" ]]
}

[[ -d /sys/class/net/br-noip/bridge ]] || fail "br-noip is not a Linux bridge"
[[ "$(readlink /sys/class/net/port1/master)" == *"/br-noip" ]] || fail "port1 is not attached to the switch"
[[ "$(readlink /sys/class/net/port2/master)" == *"/br-noip" ]] || fail "port2 is not attached to the switch"
[[ "$(ip -n noip-alice link show eth0)" == *"$ALICE_MAC"* ]] || fail "Alice's MAC is wrong"
[[ "$(ip -n noip-bob link show eth0)" == *"$BOB_MAC"* ]] || fail "Bob's MAC is wrong"
interface_has_no_ip noip-alice || fail "Alice's chat interface has an IP address"
interface_has_no_ip noip-bob || fail "Bob's chat interface has an IP address"

temporary_dir="$(mktemp -d)"
trap 'rm -rf "$temporary_dir"' EXIT

# Alice sends to Bob.
ip netns exec noip-bob env PYTHONDONTWRITEBYTECODE=1 \
  python3 "$PROJECT_DIR/src/chat_probe.py" receive \
  --name Bob --peer-mac "$ALICE_MAC" --timeout 5 \
  >"$temporary_dir/bob-received.txt" &
bob_pid=$!
sleep 0.3

ip netns exec noip-alice env PYTHONDONTWRITEBYTECODE=1 \
  python3 "$PROJECT_DIR/src/chat_probe.py" send \
  --name Alice --peer-mac "$BOB_MAC" --message "$ALICE_MESSAGE" \
  >"$temporary_dir/alice-sent.txt"
wait "$bob_pid"

forwarding_table="$(bridge fdb show br br-noip)"
[[ "$forwarding_table" == *"$ALICE_MAC dev port1"* ]] || fail "the switch did not learn Alice on port1"

# Send a separate Bob-to-Alice test message through the switch. This is not an
# automatic acknowledgement or handshake from the chat protocol.
ip netns exec noip-alice env PYTHONDONTWRITEBYTECODE=1 \
  python3 "$PROJECT_DIR/src/chat_probe.py" receive \
  --name Alice --peer-mac "$BOB_MAC" --timeout 5 \
  >"$temporary_dir/alice-received.txt" &
alice_pid=$!
sleep 0.3

ip netns exec noip-bob env PYTHONDONTWRITEBYTECODE=1 \
  python3 "$PROJECT_DIR/src/chat_probe.py" send \
  --name Bob --peer-mac "$ALICE_MAC" --message "$BOB_MESSAGE" \
  >"$temporary_dir/bob-sent.txt"
wait "$alice_pid"

forwarding_table="$(bridge fdb show br br-noip)"
[[ "$forwarding_table" == *"$BOB_MAC dev port2"* ]] || fail "the switch did not learn Bob on port2"

grep -q "received|Alice|$ALICE_MESSAGE" "$temporary_dir/bob-received.txt" || fail "Bob did not receive Alice's message"
grep -q "received|Bob|$BOB_MESSAGE" "$temporary_dir/alice-received.txt" || fail "Alice did not receive Bob's reply"

cat "$temporary_dir/alice-sent.txt"
cat "$temporary_dir/bob-received.txt"
cat "$temporary_dir/bob-sent.txt"
cat "$temporary_dir/alice-received.txt"
echo
echo "Switch forwarding table:"
grep -E "$ALICE_MAC|$BOB_MAC" <<<"$forwarding_table"
echo
echo "PASS: chat crossed br-noip and the switch learned both MAC-to-port mappings."
echo "NOTE: two ports do not prove selective forwarding; checkpoint 4 will inspect Carol's port."
