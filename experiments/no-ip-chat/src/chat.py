#!/usr/bin/env python3
"""A deliberately small line-oriented interface for two-person chat."""

import argparse
import socket
import sys
import threading

from direct_chat import DirectChat


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--peer-name", required=True)
    parser.add_argument("--peer-mac", required=True)
    parser.add_argument("--interface", default="eth0")
    args = parser.parse_args()

    chat = DirectChat(args.interface, args.peer_mac)
    stopped = threading.Event()
    printing = threading.Lock()

    def receive_messages() -> None:
        while not stopped.is_set():
            try:
                message = chat.receive(timeout=0.25)
            except socket.timeout:
                continue
            except OSError:
                return
            with printing:
                # Clear the current prompt, print the arriving message, then put
                # the prompt back. This is interface plumbing, not networking.
                print(f"\r\033[2K{message.sender}: {message.text}")
                print(f"{args.name}> ", end="", flush=True)

    receiver = threading.Thread(target=receive_messages, daemon=True)
    receiver.start()

    print(f"No-IP Chat: {args.name} ↔ {args.peer_name}")
    print("Type a message and press Enter. Ctrl-D or Ctrl-C exits.")
    print(f"{args.name}> ", end="", flush=True)

    try:
        for line in sys.stdin:
            text = line.rstrip("\n")
            if text:
                chat.send(args.name, text)
            print(f"{args.name}> ", end="", flush=True)
    except KeyboardInterrupt:
        pass
    finally:
        stopped.set()
        chat.close()
        receiver.join(timeout=1)
        print()


if __name__ == "__main__":
    main()
