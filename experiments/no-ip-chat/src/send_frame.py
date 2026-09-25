#!/usr/bin/env python3
"""Send one No-IP Chat Ethernet frame from Alice to Bob."""

import argparse
from pathlib import Path
import socket

from ethernet import ETHERTYPE, build_frame, format_mac, mac_to_bytes


def interface_mac(interface: str) -> bytes:
    """Read this computer's MAC without opening an IP-family socket.

    Linux exposes every network interface in /sys/class/net. Inside Alice's
    namespace, this path describes Alice's eth0 NIC; inside Bob's, it describes
    Bob's. Reading the address file does not send anything onto the network.
    """
    address = Path(f"/sys/class/net/{interface}/address").read_text().strip()
    return mac_to_bytes(address)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--interface", default="eth0")
    parser.add_argument("--destination", required=True)
    parser.add_argument("--message", default="hello from Alice")
    args = parser.parse_args()

    # 1. Identify NICs. 2. Build payload + header. 3. Send complete frame.
    source = interface_mac(args.interface)
    destination = mac_to_bytes(args.destination)
    frame = build_frame(source, destination, args.message)

    # AF_PACKET is Linux's direct doorway to the link layer. There is no IP
    # address, TCP connection, UDP port, or localhost service in this send path.
    raw_socket = socket.socket(
        socket.AF_PACKET,
        socket.SOCK_RAW,
        socket.htons(ETHERTYPE),
    )
    try:
        raw_socket.bind((args.interface, 0))
        raw_socket.send(frame)
    finally:
        raw_socket.close()

    print("Alice sent one custom Ethernet frame")
    print(f"  source MAC:      {format_mac(source)}")
    print(f"  destination MAC: {format_mac(destination)}")
    print(f"  EtherType:       0x{ETHERTYPE:04x}")
    print(f"  payload:         {args.message}")


if __name__ == "__main__":
    main()
