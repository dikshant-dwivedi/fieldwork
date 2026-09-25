#!/usr/bin/env bash
set -euo pipefail

cat <<'EOF'
Checkpoint 4 builds this topology:

  Alice [eth0 02:00:00:00:00:01] ── cable ── [port1] ┐
  Bob   [eth0 02:00:00:00:00:02] ── cable ── [port2] ├─ br-noip switch
  Carol [eth0 02:00:00:00:00:03] ── cable ── [port3] ┘

The important Linux operations are:

  ip netns add noip-alice              # create Alice's network stack
  ip netns add noip-bob                # create Bob's network stack
  ip netns add noip-carol              # create Carol's network stack
  ip link add br-noip type bridge        # create the software switch
  ip link add ... type veth peer name ...# create each virtual cable
  ip link set ... master br-noip         # plug its switch end into a port
  ip link set ... netns ...              # move its computer end into a namespace
  ip -n ... link set eth0 address ...   # assign fixed demonstration MACs
  ip -n ... link set eth0 up            # plug in and raise each interface

No 'ip address add' command exists. IPv6 is disabled on all chat interfaces.
Read scripts/guest/lab.sh for the exact executable version.

The veth pair is the cable; each named veth interface is one end of that cable.
The application puts the selected person's manually configured MAC in the
destination field. The switch never chooses who is chatting. It learns source
MAC -> incoming port and uses that table only to choose a forwarding port.
Carol's third port makes unknown flooding and known forwarding visibly
different.
EOF
