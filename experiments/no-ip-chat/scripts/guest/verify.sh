#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
ALICE_MAC="02:00:00:00:00:01"
BOB_MAC="02:00:00:00:00:02"
CAROL_MAC="02:00:00:00:00:03"
MESSAGE="checkpoint-four-direct-message"
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

config() {
  echo "$PROJECT_DIR/config/$1.json"
}

run_probe() {
  local participant="$1"
  shift
  ip netns exec "noip-$participant" env PYTHONDONTWRITEBYTECODE=1 \
    python3 "$PROJECT_DIR/src/chat_probe.py" --config "$(config "$participant")" "$@"
}

capture_alice_to_bob() {
  local port="$1"
  local output="$2"
  timeout 2 tcpdump -Q out -l -enn -i "$port" -c 1 \
    "ether src $ALICE_MAC and ether dst $BOB_MAC and ether proto 0x88b5" \
    >"$output" 2>&1 &
  pids+=("$!")
}

for endpoint in 'alice:01:port1' 'bob:02:port2' 'carol:03:port3'; do
  IFS=: read -r name suffix port <<<"$endpoint"
  [[ -d /sys/class/net/br-noip/bridge ]] || fail "br-noip is not a Linux bridge"
  [[ "$(readlink "/sys/class/net/$port/master")" == *'/br-noip' ]] || fail "$port is not on the switch"
  [[ "$(ip -n "noip-$name" link show eth0)" == *"02:00:00:00:00:$suffix"* ]] || fail "$name has the wrong MAC"
  [[ -z "$(ip -n "noip-$name" -o address show dev eth0)" ]] || fail "$name has an IP address"
done
[[ -z "$(ip -o address show dev br-noip)" ]] || fail "the switch has an IP address"
echo "PASS: three computers and three switch ports exist without IP."

# Begin with no learned participant locations. Alice's first frame is addressed
# to Bob, but the switch does not yet know Bob's port, so it floods the frame
# through both other ports. Capturing ports proves the path independently of
# what Bob's or Carol's applications accept.
bridge fdb flush dev br-noip dynamic
capture_alice_to_bob port2 "$temporary_dir/unknown-port2.txt"
unknown_port2_pid="${pids[-1]}"
capture_alice_to_bob port3 "$temporary_dir/unknown-port3.txt"
unknown_port3_pid="${pids[-1]}"
run_probe bob receive >"$temporary_dir/bob-first.txt" &
bob_pid=$!
pids+=("$bob_pid")
sleep 0.4
run_probe alice send --to Bob --message "$MESSAGE"
wait "$bob_pid" || fail "Bob did not receive Alice's first frame"
wait "$unknown_port2_pid" || fail "the unknown frame did not cross Bob's port"
wait "$unknown_port3_pid" || fail "the unknown frame was not flooded across Carol's port"
pids=()
echo "UNKNOWN destination: Alice → Bob appeared on port2 and port3."
echo "Reason: the switch had not learned Bob's port yet."

# Bob now sends one separate message. The switch learns Bob from its source MAC.
run_probe alice receive >"$temporary_dir/alice-learn.txt" &
alice_pid=$!
pids+=("$alice_pid")
sleep 0.3
run_probe bob send --to Alice --message teach-the-switch-bob
wait "$alice_pid" || fail "Bob's learning message did not reach Alice"
pids=()

forwarding_table="$(bridge fdb show br br-noip)"
[[ "$forwarding_table" == *"$BOB_MAC dev port2"* ]] || fail "the switch did not learn Bob on port2"
echo "LEARNED: $BOB_MAC is on port2."

# Send the same Alice-to-Bob destination again. It must cross Bob's port but
# not Carol's because Bob is now a known unicast destination.
capture_alice_to_bob port2 "$temporary_dir/known-port2.txt"
known_port2_pid="${pids[-1]}"
capture_alice_to_bob port3 "$temporary_dir/known-port3.txt"
known_port3_pid="${pids[-1]}"
run_probe bob receive >"$temporary_dir/bob-second.txt" &
bob_pid=$!
pids+=("$bob_pid")
sleep 0.4
run_probe alice send --to Bob --message "$MESSAGE"
wait "$bob_pid" || fail "Bob did not receive Alice's known-unicast frame"
wait "$known_port2_pid" || fail "known unicast did not cross Bob's port"
if wait "$known_port3_pid"; then
  fail "known unicast incorrectly appeared on Carol's port"
else
  status=$?
  [[ "$status" -eq 124 ]] || fail "Carol port capture failed unexpectedly"
fi
pids=()
echo "KNOWN destination: Alice → Bob appeared on port2 only, not port3."

# Finally prove Carol is a real participant, not merely a capture point.
run_probe alice receive >"$temporary_dir/alice-from-carol.txt" &
alice_pid=$!
pids+=("$alice_pid")
sleep 0.3
run_probe carol send --to Alice --message hello-from-carol
wait "$alice_pid" || fail "Alice did not receive Carol's direct message"
pids=()
grep -q 'received|Carol|Alice|hello-from-carol' "$temporary_dir/alice-from-carol.txt" || fail "Carol's message was decoded incorrectly"
echo "PASS: Carol also sent a manually addressed one-to-one message."
echo "PASS: checkpoint 4 shows unknown flooding followed by learned forwarding."
