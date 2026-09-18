#!/usr/bin/env python3
"""Non-interactive use of DirectChat for repeatable verification."""

import argparse

from direct_chat import DirectChat


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("send", "receive"))
    parser.add_argument("--name", required=True)
    parser.add_argument("--peer-mac", required=True)
    parser.add_argument("--message")
    parser.add_argument("--timeout", type=float, default=5.0)
    args = parser.parse_args()

    with DirectChat("eth0", args.peer_mac) as chat:
        if args.mode == "send":
            if args.message is None:
                parser.error("send requires --message")
            chat.send(args.name, args.message)
            print(f"sent|{args.name}|{args.message}")
        else:
            message = chat.receive(timeout=args.timeout)
            print(f"received|{message.sender}|{message.text}")


if __name__ == "__main__":
    main()
