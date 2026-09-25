#!/usr/bin/env python3
"""Small terminal controller for checkpoint 4's three-person direct chat."""

import argparse
import socket
import sys
import threading

from ethernet_chat import EthernetChat
from manual_config import load_config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    config = load_config(args.config)
    chat = EthernetChat(config.name, config.peers)
    selected: str | None = None
    stopped = threading.Event()
    printing = threading.Lock()

    def prompt() -> str:
        return f"{config.name} → {selected or 'select with /to'}> "

    def show(line: str) -> None:
        with printing:
            print(f"\r\033[2K{line}")
            print(prompt(), end="", flush=True)

    def receive_messages() -> None:
        while not stopped.is_set():
            try:
                message = chat.receive(timeout=0.25)
            except socket.timeout:
                continue
            except OSError:
                return
            show(f"{message.sender}: {message.text}")

    receiver = threading.Thread(target=receive_messages, daemon=True)
    receiver.start()

    print(f"No-IP Chat · {config.name}")
    print("/peers lists the manual address book; /to NAME selects one recipient.")
    print(prompt(), end="", flush=True)

    try:
        for line in sys.stdin:
            text = line.rstrip("\n")
            if text == "/peers":
                show("Available: " + ", ".join(chat.peer_names()))
            elif text.startswith("/to "):
                candidate = text[4:].strip()
                if candidate in chat.peer_names():
                    selected = candidate
                    show(f"Now talking to {selected}")
                else:
                    show(f"Unknown peer: {candidate}")
            elif text and selected is None:
                show("Choose one recipient first with /to NAME")
            elif text:
                chat.send_to(selected, text)
                print(prompt(), end="", flush=True)
            else:
                print(prompt(), end="", flush=True)
    except KeyboardInterrupt:
        pass
    finally:
        stopped.set()
        chat.close()
        receiver.join(timeout=1)
        print()


if __name__ == "__main__":
    main()
