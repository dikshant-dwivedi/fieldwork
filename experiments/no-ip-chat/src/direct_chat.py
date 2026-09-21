"""Bidirectional chat transport over Ethernet, regardless of cable or switch."""

import fcntl
import socket
import struct

from chat_protocol import ChatMessage, decode_message, encode_message
from ethernet import (
    ETHERTYPE,
    build_ethernet_frame,
    mac_to_bytes,
    parse_ethernet_frame,
)


SIOCGIFHWADDR = 0x8927


def interface_mac(interface: str) -> bytes:
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        request = struct.pack("256s", interface[:15].encode("ascii"))
        response = fcntl.ioctl(probe.fileno(), SIOCGIFHWADDR, request)
        return response[18:24]
    finally:
        probe.close()


class DirectChat:
    """The same send-and-receive capability used by Alice and Bob."""

    def __init__(self, interface: str, peer_mac: str) -> None:
        self.interface = interface
        self.own_mac = interface_mac(interface)
        self.peer_mac = mac_to_bytes(peer_mac)

        # A single raw socket can both send and receive our Ethernet protocol.
        # The two computers need no IP addresses because AF_PACKET works below IP.
        self.socket = socket.socket(
            socket.AF_PACKET,
            socket.SOCK_RAW,
            socket.htons(ETHERTYPE),
        )
        self.socket.bind((interface, 0))

    def send(self, sender: str, text: str) -> None:
        payload = encode_message(ChatMessage(sender, text))
        frame = build_ethernet_frame(self.own_mac, self.peer_mac, payload)
        self.socket.send(frame)

    def receive(self, timeout: float | None = None) -> ChatMessage:
        self.socket.settimeout(timeout)
        while True:
            ethernet_frame = parse_ethernet_frame(self.socket.recv(2048))

            # The peer MAC is fixed in this checkpoint. Automatic discovery is
            # deliberately postponed until Carol creates that need. This is
            # our application's temporary single-peer rule, not switch logic.
            if ethernet_frame.source != self.peer_mac:
                continue

            # An unknown-destination frame can be flooded to multiple switch
            # ports. A physical NIC commonly filters a foreign unicast MAC;
            # a raw socket in this virtual lab may still see the copied frame.
            # Only accept frames addressed to this endpoint's own MAC.
            if ethernet_frame.destination != self.own_mac:
                continue
            return decode_message(ethernet_frame.payload)

    def close(self) -> None:
        self.socket.close()

    def __enter__(self) -> "DirectChat":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
