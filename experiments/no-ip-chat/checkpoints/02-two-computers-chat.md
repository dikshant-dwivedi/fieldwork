# Checkpoint 02 — Two computers chat

## Question

Can two directly connected computers hold a conversation without IP?

Checkpoint 1 proved that one frame could travel from Alice to Bob. This stage
gives both endpoints the same ability to send and receive repeated messages.
The physical topology does not change.

This is primarily an **application progression**, not a new Ethernet forwarding
mechanism. The one-shot sender and observer become one long-running program on
each computer. Both programs can send, receive and distinguish a display name
from message text.

The veth pair is the virtual cable. `alice-nic` and `bob-nic` are temporary
names for its two interface ends; after each end moves into its computer's
network namespace, it is renamed to the conventional `eth0` NIC.

## Run it

```sh
cd experiments/no-ip-chat
make doctor
make setup
make test
make verify
make demo
```

`make demo` prints two commands. Run `make chat-alice` and `make chat-bob` in
separate terminals, then type into either one.

## What changed

- `chat_protocol.py` defines how sender names and text become payload bytes.
- `direct_chat.py` gives Alice and Bob the same raw send/receive transport.
- `chat.py` adds the minimal interactive terminal interface.
- Verification now sends Alice→Bob and Bob→Alice through the real cable.

Every chat frame is unicast: Alice places Bob's MAC in the destination field,
and Bob places Alice's MAC there when replying. The receiver now checks both
questions that checkpoint 1 only displayed:

1. Did this frame come from the one configured peer?
2. Was this frame addressed to my own NIC?

The sender name (`Alice` or `Bob`) is separate application data inside our
payload. Ethernet does not interpret or authenticate it.

The endpoints still know each other's names and MAC addresses in advance. This
is a manually configured two-person conversation; discovery will later replace
that configuration without replacing unicast chat.

## Code worth reading

1. [`src/chat_protocol.py`](../src/chat_protocol.py) — separates application
   meaning from Ethernet framing.
2. [`src/direct_chat.py`](../src/direct_chat.py) — uses one raw socket for both
   directions and filters for the configured peer.
3. [`src/ethernet.py`](../src/ethernet.py) — now exposes a general Ethernet
   payload layer while retaining the checkpoint 1 helpers.

`chat.py` is small interface plumbing. Read it if curious, but it is not the
networking lesson.

## Limitation that motivates checkpoint 3

One virtual cable can connect exactly two endpoints. Before Carol can join, the
direct cable must be replaced by multiple cables meeting at a switch. The next
checkpoint changes only that path while Alice and Bob continue chatting.
