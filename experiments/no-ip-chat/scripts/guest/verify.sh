#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
ALICE_MAC="02:00:00:00:00:01"
BOB_MAC="02:00:00:00:00:02"
MESSAGE="checkpoint-one-real-frame"

fail() {
  echo "FAIL: $1" >&2
  exit 1
}

interface_has_no_ip() {
  local namespace="$1"
  [[ -z "$(ip -n "$namespace" -o address show dev eth0)" ]]
}

[[ "$(ip -n noip-alice link show eth0)" == *"$ALICE_MAC"* ]] || fail "Alice's MAC is wrong"
[[ "$(ip -n noip-bob link show eth0)" == *"$BOB_MAC"* ]] || fail "Bob's MAC is wrong"
interface_has_no_ip noip-alice || fail "Alice's chat interface has an IP address"
interface_has_no_ip noip-bob || fail "Bob's chat interface has an IP address"

temporary_dir="$(mktemp -d)"
trap 'rm -rf "$temporary_dir"' EXIT

ip netns exec noip-bob env PYTHONDONTWRITEBYTECODE=1 \
  python3 "$PROJECT_DIR/src/receive_frame.py" --timeout 5 \
  >"$temporary_dir/bob.txt" &
receiver_pid=$!
sleep 0.3

ip netns exec noip-alice env PYTHONDONTWRITEBYTECODE=1 \
  python3 "$PROJECT_DIR/src/send_frame.py" \
  --destination "$BOB_MAC" --message "$MESSAGE" \
  >"$temporary_dir/alice.txt"
wait "$receiver_pid"

grep -q "source MAC:      $ALICE_MAC" "$temporary_dir/bob.txt" || fail "Bob saw the wrong source"
grep -q "destination MAC: $BOB_MAC" "$temporary_dir/bob.txt" || fail "Bob saw the wrong destination"
grep -q "EtherType:       0x88b5" "$temporary_dir/bob.txt" || fail "Bob saw the wrong EtherType"
grep -q "payload:         $MESSAGE" "$temporary_dir/bob.txt" || fail "Bob saw the wrong payload"

cat "$temporary_dir/alice.txt"
echo
cat "$temporary_dir/bob.txt"
echo
echo "PASS: a real 0x88B5 Ethernet frame crossed the cable without IP."
