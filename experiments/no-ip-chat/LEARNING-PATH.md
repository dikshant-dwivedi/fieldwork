# No-IP Chat learning path

Each release is an immutable, independently runnable answer to one networking
question. Ordinary implementation commits live between them; study the tags.

## First-time setup

```sh
git clone https://github.com/dikshant-dwivedi/fieldwork.git
cd fieldwork
brew bundle
cd experiments/no-ip-chat
```

When changing stages, stop any open chat windows. Every block below starts by
finding the repository root, so it works whether your terminal is currently at
the root or still inside the experiment:

```sh
cd "$(git rev-parse --show-toplevel)"
git switch --detach TAG
cd experiments/no-ip-chat
make setup
make test
make verify
```

`make setup` deliberately rebuilds only this disposable lab. The Lima VM and
downloaded Ubuntu image are reused.

## Checkpoint 1 — one real frame

```sh
cd "$(git rev-parse --show-toplevel)"
git switch --detach no-ip-chat-v0.1.3
cd experiments/no-ip-chat
make setup test verify
```

Read `checkpoints/01-first-frame.md`, then `src/send_frame.py`, then jump into
`ethernet.build_frame`. In another pass read `src/receive_frame.py` and jump
into `ethernet.parse_frame`.

## Checkpoint 2 — two-way direct chat

```sh
cd "$(git rev-parse --show-toplevel)"
git switch --detach no-ip-chat-v0.2.3
cd experiments/no-ip-chat
make setup test verify demo
```

Read `checkpoints/02-two-computers-chat.md`, `src/chat.py`, and the two public
operations in `src/direct_chat.py`. Follow their calls into `chat_protocol.py`
and `ethernet.py` only after understanding the high-level path.

## Checkpoint 3 — insert a switch

```sh
cd "$(git rev-parse --show-toplevel)"
git switch --detach no-ip-chat-v0.3.2
cd experiments/no-ip-chat
make setup test verify demo
```

Read `checkpoints/03-introduce-switch.md`, then `scripts/guest/lab.sh`. The chat
path stays unchanged; compare the topology setup and run `make observe-switch`.

## Checkpoint 4 — add Carol and expose forwarding

```sh
cd "$(git rev-parse --show-toplevel)"
git switch --detach no-ip-chat-v0.4.0
cd experiments/no-ip-chat
make setup test verify demo
```

Read `checkpoints/04-add-carol.md`, the manual `config/*.json` address book,
`src/ethernet_chat.py`, and finally the port captures in
`scripts/guest/verify.sh`.

## Checkpoint 5 — discover, then unicast

```sh
cd "$(git rev-parse --show-toplevel)"
git switch --detach no-ip-chat-v0.5.0
cd experiments/no-ip-chat
make setup test verify demo
```

Read `checkpoints/05-discover-peers.md`, then `chat_protocol.py`,
`peer_directory.py`, and `discovery_chat.py`. Follow `chat.py` last to see how
periodic announcement and receiving are scheduled around that module.

## Final exhibit — polished Linux interface

```sh
cd "$(git rev-parse --show-toplevel)"
git switch --detach no-ip-chat-v1.0.0
cd experiments/no-ip-chat
make setup test verify gui-smoke
make gui
```

Read `POLISHED-INTERFACE.md` and `src/gui.py`. The networking module and packet
formats are checkpoint 5's; this last release changes how the experiment is
presented, not what crosses the network.
