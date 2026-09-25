"""Discover names by broadcast, then preserve one-to-one unicast chat."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import socket

from chat_protocol import ChatMessage, Hello, decode_packet, encode_packet
from ethernet import ETHERTYPE, build_ethernet_frame, mac_to_bytes, parse_ethernet_frame
from peer_directory import PeerDirectory, PeerStatus


BROADCAST_MAC = b"\xff" * 6


@dataclass(frozen=True)
class PeerHello:
    name: str
    source_mac: bytes


@dataclass(frozen=True)
class ReceivedChat:
    sender: str
    text: str


class DiscoveryChat:
    """Small interface used by both terminal and polished GUI controllers."""

    def __init__(self, name: str, interface: str = "eth0") -> None:
        self.name = name
        own_address = Path(f"/sys/class/net/{interface}/address").read_text().strip()
        self._own_mac = mac_to_bytes(own_address)
        self._directory = PeerDirectory()
        self._socket = socket.socket(
            socket.AF_PACKET,
            socket.SOCK_RAW,
            socket.htons(ETHERTYPE),
        )
        self._socket.bind((interface, 0))

    @property
    def own_mac(self) -> bytes:
        return self._own_mac

    def announce(self) -> None:
        """Broadcast our chosen name so every current peer can learn it."""
        payload = encode_packet(Hello(self.name))
        frame = build_ethernet_frame(self._own_mac, BROADCAST_MAC, payload)
        self._socket.send(frame)

    def peers(self) -> list[PeerStatus]:
        return self._directory.statuses()

    def own_name_conflicted(self) -> bool:
        return self._directory.has_own_name_conflict(self.name)

    def send_to(self, recipient: str, text: str) -> None:
        """Resolve a discovered name and send one unicast CHAT frame."""
        destination_mac = self._directory.resolve(recipient)
        payload = encode_packet(ChatMessage(self.name, text))
        frame = build_ethernet_frame(self._own_mac, destination_mac, payload)
        self._socket.send(frame)

    def receive(self, timeout: float | None = None) -> PeerHello | ReceivedChat:
        """Process the next relevant HELLO broadcast or direct CHAT frame."""
        self._socket.settimeout(timeout)
        while True:
            frame = parse_ethernet_frame(self._socket.recv(2048))
            if frame.source == self._own_mac:
                continue
            # Another experimental EtherType user could theoretically share
            # this lab. A malformed or older packet is irrelevant, not fatal.
            try:
                packet = decode_packet(frame.payload)
            except (UnicodeDecodeError, ValueError):
                continue

            if isinstance(packet, Hello):
                if frame.destination != BROADCAST_MAC:
                    continue
                self._directory.observe(packet.name, frame.source)
                return PeerHello(packet.name, frame.source)

            if frame.destination != self._own_mac:
                continue
            if not self._directory.matches(packet.sender, frame.source):
                continue
            return ReceivedChat(packet.sender, packet.text)

    def close(self) -> None:
        self._socket.close()

    def __enter__(self) -> "DiscoveryChat":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
