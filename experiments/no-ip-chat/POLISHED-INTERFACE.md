# Polished interface — the same checkpoint 5 protocol

This is presentation work after the five networking checkpoints. It does not
introduce a new transport, server, or protocol.

```text
Tkinter controls and transcript
        │ calls
        ▼
DiscoveryChat (unchanged checkpoint 5 interface)
        │ AF_PACKET raw socket
        ▼
eth0 → virtual cable → br-noip switch → recipient eth0
```

The three desktop windows run inside the Ubuntu VM and inside Alice, Bob, and
Carol's network namespaces. Lima's VZ display shows the Linux framebuffer in a
native macOS window. There is no browser, HTTP, localhost API, TCP, UDP, X11
forwarding, or VNC in the chat path.

## Run it

```sh
cd experiments/no-ip-chat
make setup
make test
make verify
make gui-smoke
make gui
```

The final command opens Alice, Bob, and Carol together. Wait for the peer list
to populate, select one name, type a message, and press **Send**. Use `make
gui-stop` when finished.

The first setup uses a separate `noip-chat-ui` Lima instance so its native
display setting is guaranteed to apply even if an earlier checkpoint's
headless `noip-chat` VM exists. The pinned Ubuntu image remains cached.

## What is worth reading

1. `src/gui.py` constructs the window and turns selection/send gestures into
   calls to `DiscoveryChat`. Its network thread calls only `announce()` and
   `receive()`; Tkinter updates remain on the main UI thread.
2. `src/discovery_chat.py` is the unchanged networking seam underneath both
   the terminal and GUI controllers.
3. `scripts/guest/gui.sh` starts the Linux display and launches each window in
   its participant's namespace. It is infrastructure, not protocol logic.

Network details remain visible on purpose: each window shows its own MAC, a
selected peer's discovered MAC, EtherType `0x88B5`, ambiguity state, and the
fact that “sent” is not a delivery receipt. This is still a trusted laboratory
application; it does not promise identity, authentication, encryption,
delivery, ordering, persistence, or communication across routers.
