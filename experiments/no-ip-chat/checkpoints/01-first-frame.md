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

The frame still contains real source and destination MAC fields. Alice's source
MAC says which NIC created it, while Bob's destination MAC says which NIC it is
meant for. They do not have to choose between several physical paths yet: this
cable has only Alice at one end and Bob at the other.

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

## Execution map

Start Bob first:

```text
make listen
→ Makefile target listen
→ scripts/host/vm.sh listen
→ enter Bob's noip-bob network namespace
→ src/receive_frame.py main()
→ open an AF_PACKET raw Ethernet socket
→ wait for one frame with EtherType 0x88B5
→ ethernet.parse_frame(...) separates header and message
→ print what Bob received
```

Then send from Alice:

```text
make send
→ Makefile target send
→ scripts/host/vm.sh send
→ enter Alice's noip-alice network namespace
→ src/send_frame.py main()
→ interface_mac(...) reads Alice's eth0 MAC
→ ethernet.build_frame(...) builds payload, then Ethernet header
→ AF_PACKET socket.send(frame)
→ Alice eth0 → direct virtual cable → Bob eth0
```

Read each `main()` from top to bottom first. When it calls `build_frame` or
`parse_frame`, use “go to definition” to enter `ethernet.py`; return to the
caller afterward. This preserves the story instead of starting among byte
offsets without knowing why they are needed.

## What to observe

Bob prints:

- Alice's source MAC;
- Bob's destination MAC;
- experimental EtherType `0x88B5`; and
- Alice's text payload.

This first receiver deliberately stops at **observing** one valid No-IP Chat
frame. It prints the source and destination but does not yet reject an
unexpected address. Checkpoint 2 adds that application-level filtering when a
one-shot proof becomes a continuing conversation.

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
conversation, reply path, sender name in the payload, address filtering or
reusable message protocol yet. Checkpoint 2 adds those application behaviours
while preserving the same Ethernet mechanism, direct cable and no-IP
constraint.
