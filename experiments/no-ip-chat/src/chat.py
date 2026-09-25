#!/usr/bin/env python3
"""Terminal interface for checkpoint 5.

This file controls what the person sees. The networking details live behind
DiscoveryChat's five small operations: announce, peers, send_to, receive, and
close. That separation lets the final GUI reuse the exact same protocol.
"""

from __future__ import annotations

import argparse
import socket
import sys
import threading
import time

from discovery_chat import DiscoveryChat, PeerHello, ReceivedChat
from ethernet import format_mac
from peer_directory import HELLO_INTERVAL_SECONDS


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True, help="the display name to announce")
    args = parser.parse_args()

    chat = DiscoveryChat(args.name)
    selected: str | None = None
    stopped = threading.Event()
    printing = threading.Lock()

    def prompt() -> str:
        return f"{chat.name} → {selected or 'select with /to'}> "

    def show(line: str) -> None:
        with printing:
            print(f"\r\033[2K{line}")
            print(prompt(), end="", flush=True)

    def announce_repeatedly() -> None:
        # Repetition lets somebody joining later learn us, and it lets
        # everybody remove us after our announcements stop.
        while not stopped.is_set():
            chat.announce()
            stopped.wait(HELLO_INTERVAL_SECONDS)

    def receive_frames() -> None:
        while not stopped.is_set():
            try:
                event = chat.receive(timeout=0.25)
            except socket.timeout:
                continue
            except OSError:
                return
            if isinstance(event, ReceivedChat):
                show(f"{event.sender}: {event.text}")
            elif isinstance(event, PeerHello):
                # HELLO changes the directory, but it is not a chat message.
                # Keep the normal interface quiet; /peers exposes the result.
                continue

    announcer = threading.Thread(target=announce_repeatedly, daemon=True)
    receiver = threading.Thread(target=receive_frames, daemon=True)
    announcer.start()
    receiver.start()

    print(f"No-IP Chat · {chat.name}")
    print("/peers lists discovered names; /to NAME selects one recipient.")
    print("/details reveals the names-to-MAC mappings used underneath.")
    print(prompt(), end="", flush=True)

    try:
        for line in sys.stdin:
            text = line.rstrip("\n")
            if text == "/peers":
                names = [peer.name for peer in chat.peers() if not peer.conflicted]
                show("Available: " + (", ".join(names) if names else "nobody yet"))
            elif text == "/details":
                now = time.monotonic()
                details = [peer.describe(now) for peer in chat.peers()]
                show("My MAC: " + format_mac(chat.own_mac))
                for detail in details or ["No current peer announcements"]:
                    show(detail)
            elif text.startswith("/to "):
                candidate = text[4:].strip()
                try:
                    peer = next(peer for peer in chat.peers() if peer.name == candidate)
                    if peer.conflicted:
                        raise ValueError
                except (StopIteration, ValueError):
                    show(f"Unavailable or ambiguous peer: {candidate}")
                else:
                    selected = candidate
                    show(f"Now talking to {selected}")
            elif text and selected is None:
                show("Choose one recipient first with /to NAME")
            elif text:
                try:
                    chat.send_to(selected, text)
                except ValueError as error:
                    show(str(error))
                else:
                    show(f"You → {selected}: {text} (sent to Ethernet)")
            else:
                print(prompt(), end="", flush=True)
    except KeyboardInterrupt:
        pass
    finally:
        stopped.set()
        chat.close()
        announcer.join(timeout=1)
        receiver.join(timeout=1)
        print()


if __name__ == "__main__":
    main()
