# Checkpoint 03 — Introduce a switch

## Question

What changes when a switch replaces Alice and Bob's direct cable?

The chat protocol and clients do not change. Only the path changes: Alice and
Bob now have separate virtual cables whose other ends meet at a Linux bridge.

## Topology

```text
Alice eth0/NIC ── veth-pair cable ── port1 ┐
                                           ├── br-noip Linux bridge
Bob eth0/NIC   ── veth-pair cable ── port2 ┘
```

`br-noip` is a real software Ethernet switch in the Linux kernel. It forwards
frames by learning which source MAC address appears on which port.

When a frame arrives, the switch learns its **source** MAC on the incoming
port. It then looks up the **destination** MAC. If that address is known, it
uses the recorded port; if unknown, it floods copies to every **other** port,
never back out the incoming port. With only two ports, flooding and choosing
the sole other port look the same.

Imagine five computers, A–E, each connected to one switch port. The table is
initially empty:

| Frame arriving | What the switch learns | Where it forwards |
| --- | --- | --- |
| A → B | A's MAC is on port 1 | Ports 2–5; B's port is still unknown |
| B → C | B's MAC is on port 2 | Ports 1 and 3–5; C's port is still unknown |
| A → B again | Refreshes A on port 1 | Port 2 only, because B is now known |

The switch connects **network interfaces**, not chat applications, and its
table maps MAC addresses to ports. It does not learn C, D or E merely by
sending flooded copies toward them; each must transmit a frame for the switch
to learn its port. Dynamic entries also age out after inactivity, at which
point a future frame to that destination may be flooded again.

## Run it

```sh
cd experiments/no-ip-chat
make setup
make test
make verify
make demo
```

`make setup` replaces the checkpoint 2 cable with the bridge topology. It keeps
the existing VM and does not repeat the Ubuntu download.

For the human demonstration, use the three commands printed by `make demo`:

- `make chat-alice`
- `make chat-bob`
- `make observe-switch`

Start the switch observer before sending messages. Its forwarding table begins
empty, then learns Alice on `port1` and Bob on `port2` from frames they send.

Linux names the two interfaces at the ends of a veth pair; it does not assign a
third name to the pair itself. Throughout this experiment, the **veth pair is
the cable**, an endpoint's `eth0` is its NIC, and `port1`/`port2` are switch
ports. Earlier `alice-cable`/`bob-cable` names described interface ends
imprecisely; this checkpoint adopts the physical analogy consistently.

## Code worth reading

1. [`scripts/guest/lab.sh`](../scripts/guest/lab.sh) — compare the bridge and
   two-cable setup with the direct veth pair in the preceding tag.
2. [`scripts/guest/verify.sh`](../scripts/guest/verify.sh) — proves the bridge
   learned the expected MAC-to-port mappings after real chat traffic.
3. [`src/direct_chat.py`](../src/direct_chat.py) — its comments explain the
   receiver-side checks for a hardcoded peer and its own destination MAC.

The Python chat **behavior** is unchanged; only explanatory comments were
added. That is evidence that Ethernet applications do not need to know whether
a direct cable or switch lies between them.

The switch flooding a frame toward a port is not the same as that computer
accepting it. A physical NIC commonly drops frames addressed to someone else's
unicast MAC. Our raw socket on a virtual interface may expose the copied frame,
so the app checks the destination too. Its source-MAC check is a separate,
temporary rule that allows only the manually configured peer.

`make verify` checks the topology, absence of IP addresses, bidirectional
messages, and learned MAC-to-port entries. Run it from this experiment's
directory after `make setup`. It does not prove the unknown-unicast flood or
selective delivery to Bob; those need a third port and a capture on that port.

## Limitation that motivates checkpoint 4

The switch has two ports and both clients still have one hardcoded peer. Carol
cannot join until the topology gains a third port and participants acquire a
way to announce and discover one another.
