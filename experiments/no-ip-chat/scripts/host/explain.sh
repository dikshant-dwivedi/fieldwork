#!/usr/bin/env bash
set -euo pipefail

cat <<'EOF'
Checkpoint 3 builds this topology:

  Alice [eth0 02:00:00:00:00:01] ── cable ── [port1]
                                                     \
                                                      br-noip switch
                                                     /
  Bob   [eth0 02:00:00:00:00:02] ── cable ── [port2]

The important Linux operations are:

  ip netns add noip-alice              # create Alice's network stack
  ip netns add noip-bob                # create Bob's network stack
  ip link add br-noip type bridge        # create the software switch
  ip link add ... type veth peer name ...# create each virtual cable
  ip link set ... master br-noip         # plug its switch end into a port
  ip link set ... netns ...              # move its computer end into a namespace
  ip -n ... link set eth0 address ...   # assign fixed demonstration MACs
  ip -n ... link set eth0 up            # plug in and raise each interface

No 'ip address add' command exists. IPv6 is disabled on both chat interfaces.
Read scripts/guest/lab.sh for the exact executable version.

The veth pair is the cable; each named veth interface is one end of that cable.
The chat code is unchanged from checkpoint 2. The bridge learns the source MAC
of each arriving frame and records the port it came through. Once both entries
exist, it associates Alice with port1 and Bob with port2.
EOF
