#!/usr/bin/env bash
set -euo pipefail

cat <<'EOF'
Checkpoint 5 uses this unchanged Ethernet topology:

  Alice [eth0 02:00:00:00:00:01] ── cable ── [port1] ┐
  Bob   [eth0 02:00:00:00:00:02] ── cable ── [port2] ├─ br-noip switch
  Carol [eth0 02:00:00:00:00:03] ── cable ── [port3] ┘

The application now sends two different packet types:

  HELLO  broadcast destination ff:ff:ff:ff:ff:ff
         contains a self-declared display name
         teaches every app name -> Ethernet source MAC

  CHAT   unicast destination resolved from the discovered directory
         contains the sender name and direct-message text
         goes through only the recipient's learned switch port

The switch learns source MAC -> incoming port from both kinds of frame. It does
not read names or chat text. The applications read HELLO and build their own
separate name -> MAC directories.

No 'ip address add' command exists. IPv6 is disabled on all chat interfaces.
Read checkpoints/05-discover-peers.md for the complete execution maps.
EOF
