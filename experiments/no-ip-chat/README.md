# No-IP Chat

**Question:** Can computers discover one another and chat through a switch
without using IP?

This experiment will exchange custom Ethernet frames between isolated Linux
network namespaces. Virtual Ethernet pairs act as cables, and a Linux bridge
acts as an observable switch. The chat interfaces will have neither IPv4 nor
IPv6 addresses.

## Planned checkpoints

1. Send one custom Ethernet frame from Alice to Bob.
2. Let two directly connected computers chat.
3. Replace their direct cable with a switch.
4. Add Carol and reveal unknown-unicast flooding versus learned forwarding.
5. Replace manual peer addresses with discovery while keeping chat unicast.

Every checkpoint will be independently runnable. The permanent implementation
begins with checkpoint 1 rather than importing the discarded feasibility spike.

## Checkpoints

- [01 — First frame](checkpoints/01-first-frame.md): Alice sends Bob one custom
  Ethernet frame through a direct virtual cable without IP.
- [02 — Two computers chat](checkpoints/02-two-computers-chat.md): Alice and Bob
  exchange repeated messages in both directions over that same cable.
- [03 — Introduce a switch](checkpoints/03-introduce-switch.md): their chat code
  stays unchanged while two cables and an observable bridge replace the direct
  connection.
- [04 — Add Carol](checkpoints/04-add-carol.md): a manually configured
  three-person address book makes unknown flooding and learned unicast visibly
  different while every conversation remains one-to-one.
- [05 — Discover peers](checkpoints/05-discover-peers.md): periodic broadcast
  HELLO announcements replace the manual address books; direct CHAT frames
  remain unicast to one discovered recipient.

After checkpoint 5, the [polished interface](POLISHED-INTERFACE.md) places a
Tkinter presentation layer over the same `DiscoveryChat` module. It is an
exhibit, not a sixth networking checkpoint: the protocol does not change.

For the exact tag, command, and reading order at every stage, follow the
[learning path](LEARNING-PATH.md).
