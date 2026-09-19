# Checkpoint 01 — First frame

## Question

Can Alice send Bob one custom Ethernet frame without either chat interface
having an IP address?

## Topology

```text
Alice namespace                         Bob namespace
eth0 02:00:00:00:00:01  <── veth ──>  eth0 02:00:00:00:00:02
no IPv4 or IPv6                         no IPv4 or IPv6
```

There is no switch yet. The veth pair behaves like one Ethernet cable with an
endpoint in each isolated Linux network stack.

Linux names the two interfaces at the ends of a veth pair; it does not create a
separate named cable object. The setup therefore creates temporary
`alice-nic` and `bob-nic` ends, moves one into each computer, and renames each
computer's NIC to the conventional `eth0`. The **veth pair itself is the
cable**.

## Run it

From the repository root, install the declared host dependency once:

```sh
brew bundle
```

Then enter the experiment:

```sh
cd experiments/no-ip-chat
make doctor
make setup
make test
make demo
make verify
```

`make setup` performs the first large download: the pinned Ubuntu image used by
Lima. It requires internet access but not host `sudo` access.

To experience the send and receive as two computers, open two terminals after
`make setup`. Start `make listen` in the first, then run `make send` in the
second.

## What to observe

Bob prints:

- Alice's source MAC;
- Bob's destination MAC;
- experimental EtherType `0x88B5`; and
- Alice's text payload.

`make topology` prints both interfaces with empty address columns. `make verify`
checks those empty IP assignments and performs another real frame exchange.

## Code worth reading

Read these in order:

1. [`src/ethernet.py`](../src/ethernet.py) — lays out and parses the bytes in
   the Ethernet frame.
2. [`src/send_frame.py`](../src/send_frame.py) — opens Linux's raw link-layer
   socket and sends those bytes.
3. [`src/receive_frame.py`](../src/receive_frame.py) — listens specifically for
   our EtherType and decodes the frame.
4. [`scripts/guest/lab.sh`](../scripts/guest/lab.sh) — creates two network
   namespaces and connects them with one virtual cable.

The Lima configuration, Makefile and host scripts are reproducibility plumbing;
skim them, but they are not the networking lesson.

## Limitation that motivates checkpoint 2

Alice can send one fixed message and Bob can receive it. There is no interactive
conversation, reply path or reusable message protocol yet. Checkpoint 2 turns
this one-way proof into a two-person chat while preserving the same direct
cable and no-IP constraint.
