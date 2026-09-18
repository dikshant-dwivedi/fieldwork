#!/usr/bin/env python3
"""Send one No-IP Chat Ethernet frame from Alice to Bob."""

import argparse
import fcntl
import socket
import struct

from ethernet import ETHERTYPE, build_frame, format_mac, mac_to_bytes


SIOCGIFHWADDR = 0x8927


def interface_mac(interface: str) -> bytes:
    """Ask Linux for the real MAC assigned to this virtual interface."""
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        request = struct.pack("256s", interface[:15].encode("ascii"))
        response = fcntl.ioctl(probe.fileno(), SIOCGIFHWADDR, request)
        return response[18:24]
    finally:
        probe.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--interface", default="eth0")
    parser.add_argument("--destination", required=True)
    parser.add_argument("--message", default="hello from Alice")
    args = parser.parse_args()

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
