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
