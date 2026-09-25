"""One-to-one chat using a visible, manually configured name-to-MAC map.

The terminal interface needs to know only three operations: list peer names,
send to a chosen name, and receive a message. This module owns the networking
steps behind that small interface.
"""

from dataclasses import dataclass
from pathlib import Path
import socket

from chat_protocol import ChatMessage, decode_message, encode_message
from ethernet import ETHERTYPE, build_ethernet_frame, mac_to_bytes, parse_ethernet_frame


@dataclass(frozen=True)
class ReceivedChat:
    sender: str
    text: str


class EthernetChat:
    def __init__(self, name: str, peers: dict[str, str], interface: str = "eth0") -> None:
        self.name = name
        self.interface = interface

        # The keys are the names a person selects; the values are the Ethernet
        # destinations that the application was given before startup.
        self._peers = {peer: mac_to_bytes(mac) for peer, mac in peers.items()}
        if len(set(self._peers.values())) != len(self._peers):
            raise ValueError("each peer must have a different MAC address")
        self._names_by_mac = {mac: peer for peer, mac in self._peers.items()}

        own_address = Path(f"/sys/class/net/{interface}/address").read_text().strip()
        self._own_mac = mac_to_bytes(own_address)
        self._socket = socket.socket(
            socket.AF_PACKET,
            socket.SOCK_RAW,
            socket.htons(ETHERTYPE),
        )
        self._socket.bind((interface, 0))

    def peer_names(self) -> list[str]:
        """Return the human names available for `/to <name>`."""
        return sorted(self._peers)

    def send_to(self, recipient: str, text: str) -> None:
        """Resolve a name, create the payload and frame, then send it."""
        try:
            destination_mac = self._peers[recipient]
        except KeyError as error:
            raise ValueError(f"unknown peer: {recipient}") from error

        # Step 1: our application protocol turns a name and text into bytes.
        payload = encode_message(ChatMessage(self.name, text))
        # Step 2: Ethernet adds destination/source MACs and our EtherType.
        frame = build_ethernet_frame(self._own_mac, destination_mac, payload)
        # Step 3: AF_PACKET gives the complete frame to this computer's NIC.
        self._socket.send(frame)

    def receive(self, timeout: float | None = None) -> ReceivedChat:
        """Wait for a valid unicast frame from one configured peer."""
        self._socket.settimeout(timeout)
        while True:
            frame = parse_ethernet_frame(self._socket.recv(2048))
            if frame.destination != self._own_mac:
                continue  # A flooded frame for somebody else is not our chat.

            sender = self._names_by_mac.get(frame.source)
            if sender is None:
                continue  # This MAC is absent from our manual address book.

            message = decode_message(frame.payload)
            if message.sender != sender:
                continue  # Payload name and configured source disagree.
            return ReceivedChat(sender, message.text)

    def close(self) -> None:
        self._socket.close()

    def __enter__(self) -> "EthernetChat":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
