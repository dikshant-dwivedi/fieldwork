#!/usr/bin/env bash
set -euo pipefail

echo "NO-IP CHAT · br-noip switch observer"
echo "────────────────────────────────────"
echo "port1 ← cable to Alice's eth0 NIC"
echo "port2 ← cable to Bob's eth0 NIC"
echo
echo "Watching for changes in the switch's learned MAC-to-port table."
echo "The bridge learns from source addresses; it does not read chat text."
echo "Press Ctrl-C to stop."

previous="__first_observation__"
while true; do
  # Polling is simple and portable, but only print when the learned table
  # changes. A terminal that cannot redraw in place will not flood with copies.
  learned="$(bridge fdb show br br-noip | grep -v permanent || true)"
  if [[ "$learned" != "$previous" ]]; then
    echo
    echo "Dynamically learned forwarding entries:"
    if [[ -n "$learned" ]]; then
      echo "$learned"
    else
      echo "(none — send a frame and watch the source MAC appear)"
    fi
    previous="$learned"
  fi
  sleep 0.5
done
