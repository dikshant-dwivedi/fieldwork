#!/usr/bin/env bash
set -euo pipefail

cat <<'EOF'
Checkpoint 1 builds this topology:

  Alice namespace [eth0 02:00:00:00:00:01]
                         |
                  one veth cable
                         |
  Bob namespace   [eth0 02:00:00:00:00:02]

The important Linux operations are:

  ip netns add noip-alice              # create Alice's network stack
  ip netns add noip-bob                # create Bob's network stack
  ip link add alice-nic type veth peer name bob-nic
                                        # create the two NIC ends of one cable
  ip link set ... netns ...             # move one end into each computer
  ip -n ... link set eth0 address ...   # assign fixed demonstration MACs
  ip -n ... link set eth0 up            # plug in and raise each interface

No 'ip address add' command exists. IPv6 is disabled on both chat interfaces.
The veth pair is the cable; alice-nic and bob-nic are its interface ends. Each
end is renamed eth0 after it moves into its computer's network namespace.
Read scripts/guest/lab.sh for the exact executable version.
EOF
