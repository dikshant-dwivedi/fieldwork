#!/usr/bin/env python3
"""Non-interactive caller of EthernetChat for repeatable verification."""

import argparse

from ethernet_chat import EthernetChat
from manual_config import load_config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("send", "receive"))
    parser.add_argument("--config", required=True)
    parser.add_argument("--to")
    parser.add_argument("--message")
    parser.add_argument("--timeout", type=float, default=5.0)
    args = parser.parse_args()

    config = load_config(args.config)
    with EthernetChat(config.name, config.peers) as chat:
        if args.mode == "send":
            if not args.to or args.message is None:
                parser.error("send requires --to and --message")
            chat.send_to(args.to, args.message)
            print(f"sent|{config.name}|{args.to}|{args.message}")
        else:
            message = chat.receive(timeout=args.timeout)
            print(f"received|{message.sender}|{config.name}|{message.text}")


if __name__ == "__main__":
    main()
