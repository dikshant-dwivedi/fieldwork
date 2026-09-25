#!/usr/bin/env python3
"""Run one discovery participant without a human for repeatable verification."""

import argparse
import socket
import time

from discovery_chat import DiscoveryChat, ReceivedChat
from ethernet import format_mac


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--expect", action="append", default=[])
    parser.add_argument("--send-to")
    parser.add_argument("--message")
    parser.add_argument("--expect-message-from")
    parser.add_argument("--timeout", type=float, default=8.0)
    args = parser.parse_args()
    if bool(args.send_to) != (args.message is not None):
        parser.error("--send-to and --message must be supplied together")

    started = time.monotonic()
    deadline = started + args.timeout
    next_hello = started
    sent = False
    received_expected = args.expect_message_from is None
    reported: set[str] = set()

    with DiscoveryChat(args.name) as chat:
        while time.monotonic() < deadline:
            now = time.monotonic()
            if now >= next_hello:
                chat.announce()
                next_hello = now + 0.4

            try:
                event = chat.receive(timeout=0.1)
            except socket.timeout:
                event = None

            current = {peer.name: peer for peer in chat.peers() if not peer.conflicted}
            for name in sorted(set(current) - reported):
                print(f"discovered|{name}|{format_mac(current[name].macs[0])}", flush=True)
                reported.add(name)

            all_expected = set(args.expect).issubset(current)
            # HELLO frames teach every app and the switch before this direct
            # CHAT is sent. The pause makes that ordering deterministic.
            if args.send_to and all_expected and not sent and now - started >= 1.2:
                chat.send_to(args.send_to, args.message)
                print(f"sent|{args.name}|{args.send_to}|{args.message}", flush=True)
                sent = True

            if isinstance(event, ReceivedChat):
                print(f"received|{event.sender}|{args.name}|{event.text}", flush=True)
                if event.sender == args.expect_message_from:
                    received_expected = True

            send_complete = args.send_to is None or sent
            if all_expected and send_complete and received_expected and now - started >= 2.5:
                return

    raise SystemExit("timed out before discovery/chat expectations were satisfied")


if __name__ == "__main__":
    main()
