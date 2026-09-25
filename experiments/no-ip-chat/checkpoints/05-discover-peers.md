# Checkpoint 05 — Discover names, then chat directly

## Question

Can Alice, Bob, and Carol learn friendly names without a prepared address book
while keeping every actual chat message one-to-one?

## The two kinds of packet

This checkpoint deliberately separates discovery from conversation:

```text
HELLO("Bob")                         CHAT("Bob", "Hi Alice")
destination ff:ff:ff:ff:ff:ff       destination Alice's discovered MAC
broadcast to the local network      unicast to Alice only
teaches Bob → Bob's source MAC      carries the actual private chat text
```

The broadcast does not make chat a group chat. It only answers “who is
currently here, and which source MAC did their announcement arrive from?”
HELLO repeats every two seconds so a late-arriving Carol can learn Alice and
Bob, and they can learn Carol. An entry disappears after seven seconds without
a fresh HELLO.

## Execution map: starting Bob

```text
make chat-bob
→ scripts/host/vm.sh chat-bob
→ enter the noip-bob network namespace
→ src/chat.py main()
→ DiscoveryChat("Bob") opens one raw Ethernet socket
→ announcer thread calls announce() every two seconds
→ chat_protocol.encode_packet(Hello("Bob")) creates the payload
→ ethernet.build_ethernet_frame(...) adds broadcast/source/type header
→ raw socket sends the frame through Bob eth0
```

At the receiving apps:

```text
DiscoveryChat.receive()
→ ethernet.parse_ethernet_frame(...) separates header and payload
→ chat_protocol.decode_packet(...) recognises HELLO
→ PeerDirectory.observe("Bob", Ethernet source MAC)
→ /peers can now show Bob by name
```

The name is application data inside the Ethernet payload. Ethernet itself
still knows only MAC addresses.

## Execution map: sending Bob → Alice

```text
/to Alice, then type text
→ chat.py calls DiscoveryChat.send_to("Alice", text)
→ PeerDirectory.resolve("Alice") returns one current, unambiguous MAC
→ chat_protocol.encode_packet(ChatMessage("Bob", text)) creates the payload
→ ethernet.build_ethernet_frame(...) adds Alice's destination MAC
→ raw socket sends a unicast frame
→ switch forwards it to Alice's learned port, not Carol's
```

Alice accepts the message only when its destination is her MAC and its claimed
sender name matches the source MAC previously learned from HELLO. This is a
useful consistency check, not authentication or encryption.

## Names, conflicts, and leaving

The display name is self-declared. If two current MAC addresses announce
`Bob`, the directory marks that name as `CONFLICT` and refuses to send to it;
guessing would risk sending to the wrong computer. For simplicity, a leaving
app sends no goodbye. Its periodic HELLO stops and the directory expires it.

Real systems can query on demand, send explicit goodbyes, use a central
directory, or combine announcements and queries. Periodic announcements are
used here because all three behaviours—joining, remaining present, and
leaving—stay visible in one tiny protocol.

## Run it

```sh
cd experiments/no-ip-chat
make setup
make test
make verify
make demo
```

`make demo` prints the four terminal commands. In a chat use `/peers`, `/to
NAME`, and `/details`. `make verify` starts three real processes concurrently,
checks all six discovered relationships, sends Bob→Alice by name, and captures
Carol's port to prove that direct CHAT did not traverse it.

## Code worth reading

1. `src/chat_protocol.py` — translates `Hello` and `ChatMessage` objects to
   payload bytes and back.
2. `src/peer_directory.py` — turns repeated observations into name lookup,
   duplicate-name refusal, and expiry.
3. `src/discovery_chat.py` — the small networking interface used by terminal
   and GUI controllers: announce, list peers, send, receive.
4. `src/chat.py` — threads that schedule announcements and keep receiving while
   the person types.
5. `scripts/guest/verify.sh` — real three-process and switch-port evidence.

## Boundary of the claim

The chat interfaces and switch have no IPv4 or IPv6 address. Lima may still use
IP internally to manage its VM; that is outside this experiment's data path.
Broadcast discovery remains inside one local Ethernet network and does not
cross a router. “Sent” means handed to Ethernet—not acknowledged, delivered,
read, encrypted, or authenticated. This is a trusted disposable lab designed
to demonstrate direct communication using MAC addresses.
