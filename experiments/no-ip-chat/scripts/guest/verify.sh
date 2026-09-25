#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
ALICE_MAC="02:00:00:00:00:01"
BOB_MAC="02:00:00:00:00:02"
CAROL_MAC="02:00:00:00:00:03"
MESSAGE="checkpoint-five-discovered-unicast"
temporary_dir="$(mktemp -d)"
pids=()

cleanup() {
  for pid in "${pids[@]}"; do kill "$pid" 2>/dev/null || true; done
  rm -rf "$temporary_dir"
}
trap cleanup EXIT

fail() {
  echo "FAIL: $1" >&2
  exit 1
}

run_participant() {
  local namespace="$1"
  shift
  ip netns exec "noip-$namespace" env PYTHONDONTWRITEBYTECODE=1 \
    python3 "$PROJECT_DIR/src/chat_probe.py" "$@"
}

[[ -d /sys/class/net/br-noip/bridge ]] || fail "br-noip is not a Linux bridge"
for endpoint in 'alice:01:port1' 'bob:02:port2' 'carol:03:port3'; do
  IFS=: read -r name suffix port <<<"$endpoint"
  [[ "$(readlink "/sys/class/net/$port/master")" == *'/br-noip' ]] || fail "$port is not on the switch"
  [[ "$(ip -n "noip-$name" link show eth0)" == *"02:00:00:00:00:$suffix"* ]] || fail "$name has the wrong MAC"
  [[ -z "$(ip -n "noip-$name" -o address show dev eth0)" ]] || fail "$name has an IP address"
done
[[ -z "$(ip -o address show dev br-noip)" ]] || fail "the switch has an IP address"
echo "PASS: three computers and the switch have no IP addresses."

# HELLO broadcasts cross Carol's port, but this filter watches only Bob's
# direct CHAT destination. Learned unicast must not cross port3.
timeout 6 tcpdump -Q out -l -enn -i port3 -c 1 \
  "ether src $BOB_MAC and ether dst $ALICE_MAC and ether proto 0x88b5" \
  >"$temporary_dir/carol-port.txt" 2>&1 &
capture_pid=$!
pids+=("$capture_pid")

run_participant alice --name Alice --expect Bob --expect Carol \
  --expect-message-from Bob >"$temporary_dir/alice.txt" &
alice_pid=$!
pids+=("$alice_pid")
run_participant bob --name Bob --expect Alice --expect Carol \
  --send-to Alice --message "$MESSAGE" >"$temporary_dir/bob.txt" &
bob_pid=$!
pids+=("$bob_pid")
run_participant carol --name Carol --expect Alice --expect Bob \
  >"$temporary_dir/carol.txt" &
carol_pid=$!
pids+=("$carol_pid")

wait "$alice_pid" || fail "Alice did not discover both peers and receive Bob's chat"
wait "$bob_pid" || fail "Bob did not discover both peers and send to Alice"
wait "$carol_pid" || fail "Carol did not discover both peers"

if wait "$capture_pid"; then
  fail "Bob's unicast to Alice incorrectly crossed Carol's port"
else
  status=$?
  [[ "$status" -eq 124 ]] || fail "Carol port capture failed unexpectedly"
fi
pids=()

for name in alice bob carol; do
  other_count="$(grep -c '^discovered|' "$temporary_dir/$name.txt")"
  [[ "$other_count" -eq 2 ]] || fail "$name did not learn exactly two peers"
done
grep -q "sent|Bob|Alice|$MESSAGE" "$temporary_dir/bob.txt" || fail "Bob did not resolve Alice by name"
grep -q "received|Bob|Alice|$MESSAGE" "$temporary_dir/alice.txt" || fail "Alice did not validate Bob's direct chat"

forwarding_table="$(bridge fdb show br br-noip)"
[[ "$forwarding_table" == *"$ALICE_MAC dev port1"* ]] || fail "switch did not learn Alice on port1"
[[ "$forwarding_table" == *"$BOB_MAC dev port2"* ]] || fail "switch did not learn Bob on port2"
[[ "$forwarding_table" == *"$CAROL_MAC dev port3"* ]] || fail "switch did not learn Carol on port3"

echo "PASS: Alice, Bob, and Carol discovered names without configuration files."
echo "PASS: Bob resolved Alice's name to her MAC and sent a direct CHAT frame."
echo "PASS: that unicast crossed Alice's port only, not Carol's port."
echo "PASS: duplicate-name rejection and expiry are covered by unit tests."
