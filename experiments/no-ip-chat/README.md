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
4. Add Carol and discover peers through broadcast frames.
5. Use broadcast for discovery and learned unicast for conversation.

Every checkpoint will be independently runnable. The implementation has not
started yet; this directory currently records only the experiment boundary and
planned progression.
