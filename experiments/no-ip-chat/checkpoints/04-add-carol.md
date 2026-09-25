# Checkpoint 04 — Add Carol and expose switch forwarding

## Question

What does a switch do with a unicast frame before and after it learns the
destination's port?

## Scope

Alice, Bob and Carol are full participants, but there is no discovery yet.
Each has a small JSON file listing the other two names and MAC addresses.
Selecting Bob always produces a frame whose destination is Bob's MAC; it never
means “send to everyone.”

## Topology

```text
Alice eth0 ── cable ── port1 ┐
Bob eth0   ── cable ── port2 ├── br-noip switch (no IP)
Carol eth0 ── cable ── port3 ┘
```

With an empty switch table, Alice→Bob teaches the switch Alice's source port,
but Bob's destination port is still unknown. The switch copies the frame to
port2 and port3. Bob accepts it; Carol's chat ignores it because its destination
MAC is Bob's. After Bob transmits, the switch learns Bob→port2. The next
Alice→Bob frame goes only through port2.

## Execution map

Starting Alice:

```text
make chat-alice
→ scripts/host/vm.sh chat-alice
→ enter the noip-alice network namespace
→ src/chat.py main()
→ manual_config.load_config(config/alice.json)
→ EthernetChat(name, peers)
```

Sending a line to Bob:

```text
/to Bob
typed text
→ chat.py calls EthernetChat.send_to("Bob", text)
→ look up Bob's configured MAC
→ chat_protocol.encode_message(...)
→ ethernet.build_ethernet_frame(...)
→ AF_PACKET socket.send(frame)
→ Alice eth0 → port1 → br-noip → Bob's port
```

Receiving it:

```text
receiver thread in chat.py
→ EthernetChat.receive()
→ raw socket receives a frame
→ ethernet.parse_ethernet_frame(...)
→ reject it unless destination == my MAC
→ find sender name from configured source MAC
→ chat_protocol.decode_message(...)
→ return ReceivedChat to chat.py for display
```

## Run it

```sh
cd experiments/no-ip-chat
make setup
make test
make verify
make demo
```

For the scripted forwarding evidence, run `make observe-forwarding`. For the
human chat, open the four terminals printed by `make demo`, then use `/peers`
and `/to NAME`.

## Code worth reading

1. `config/alice.json` — makes the manual address book visible.
2. `src/ethernet_chat.py` — the three-operation networking module: list peers,
   send to a name, receive a valid direct message.
3. `scripts/guest/verify.sh` — captures port2 and port3 to prove both switch
   behaviours independently of what the chat windows display.
4. `scripts/guest/lab.sh` — adds Carol's third cable and switch port.

`src/chat.py` is terminal-interface plumbing. Its important role is simply to
turn `/to Bob` into `send_to("Bob", text)`.

## What this proves—and does not

It proves unknown unicast is flooded, known unicast is selectively forwarded,
and three people can exchange manually addressed direct messages without IP.
It does not discover anybody: every name-to-MAC mapping was prepared before
startup. Checkpoint 5 removes those files and learns the same mappings from
broadcast HELLO frames while keeping CHAT frames unicast.
