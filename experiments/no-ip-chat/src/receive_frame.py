#!/usr/bin/env python3
"""Wait for Bob to receive one No-IP Chat Ethernet frame."""

import argparse
import socket

from ethernet import ETHERTYPE, format_mac, parse_frame


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--interface", default="eth0")
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()

    # Asking AF_PACKET for only our EtherType filters unrelated Ethernet traffic
    # before it reaches the rest of this small program.
    raw_socket = socket.socket(
        socket.AF_PACKET,
        socket.SOCK_RAW,
        socket.htons(ETHERTYPE),
    )
    raw_socket.settimeout(args.timeout)
    raw_socket.bind((args.interface, 0))

    try:
        while True:
            frame = parse_frame(raw_socket.recv(2048))
            print("Bob received one custom Ethernet frame")
            print(f"  source MAC:      {format_mac(frame.source)}")
            print(f"  destination MAC: {format_mac(frame.destination)}")
            print(f"  EtherType:       0x{ETHERTYPE:04x}")
            print(f"  payload:         {frame.message}")
            return
    except socket.timeout as error:
        raise SystemExit("Bob timed out without receiving a No-IP Chat frame") from error
    finally:
        raw_socket.close()


if __name__ == "__main__":
    main()
