"""Bidirectional chat transport over one direct Ethernet cable."""

from pathlib import Path
import socket

from chat_protocol import ChatMessage, decode_message, encode_message
from ethernet import (
    ETHERTYPE,
    build_ethernet_frame,
    mac_to_bytes,
    parse_ethernet_frame,
)


def interface_mac(interface: str) -> bytes:
    """Read this namespace's NIC address without using an IP-family socket."""
    address = Path(f"/sys/class/net/{interface}/address").read_text().strip()
    return mac_to_bytes(address)


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
        # The sender's display name and text belong to our application payload.
        # Ethernet itself sees only bytes and the source/destination MACs.
        payload = encode_message(ChatMessage(sender, text))
        frame = build_ethernet_frame(self.own_mac, self.peer_mac, payload)
        self.socket.send(frame)

    def receive(self, timeout: float | None = None) -> ChatMessage:
        self.socket.settimeout(timeout)
        while True:
            ethernet_frame = parse_ethernet_frame(self.socket.recv(2048))

            # The peer MAC is supplied before startup in this checkpoint. This
            # first check asks, "did the configured peer send the frame?"
            if ethernet_frame.source != self.peer_mac:
                continue

            # The second check asks, "was the frame addressed to my NIC?" The
            # direct cable has only one other end, but the address still matters
            # to the chat application's one-to-one rule.
            if ethernet_frame.destination != self.own_mac:
                continue
            return decode_message(ethernet_frame.payload)

    def close(self) -> None:
        self.socket.close()

    def __enter__(self) -> "DirectChat":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
