"""The small piece of checkpoint 1 that is worth understanding closely.

An Ethernet frame begins with three fields the switch or receiving interface
needs before it can look at our message:

    6 bytes destination MAC | 6 bytes source MAC | 2 bytes EtherType

Everything after those 14 bytes is our protocol. Ethernet does not know that
the payload is text; EtherType 0x88B5 merely tells the receiver that this is an
experimental protocol whose bytes should be interpreted by No-IP Chat.
"""

from dataclasses import dataclass
import struct


ETHERTYPE = 0x88B5
HEADER_LENGTH = 14
MINIMUM_FRAME_WITHOUT_FCS = 60
PROTOCOL_MAGIC = b"NIP1"


@dataclass(frozen=True)
class ReceivedFrame:
    destination: bytes
    source: bytes
    message: str


def mac_to_bytes(text: str) -> bytes:
    """Turn the familiar 02:00:... notation into Ethernet's six bytes."""
    parts = text.split(":")
    if len(parts) != 6:
        raise ValueError(f"invalid MAC address: {text}")
    try:
        mac = bytes(int(part, 16) for part in parts)
    except ValueError as error:
        raise ValueError(f"invalid MAC address: {text}") from error
    if any(len(part) != 2 for part in parts):
        raise ValueError(f"invalid MAC address: {text}")
    return mac


def format_mac(mac: bytes) -> str:
    if len(mac) != 6:
        raise ValueError("a MAC address must contain exactly six bytes")
    return ":".join(f"{part:02x}" for part in mac)


def build_frame(source: bytes, destination: bytes, message: str) -> bytes:
    """Build one complete Ethernet frame, excluding the hardware-added FCS."""
    if len(source) != 6 or len(destination) != 6:
        raise ValueError("source and destination must be six-byte MAC addresses")

    message_bytes = message.encode("utf-8")
    if len(message_bytes) > 1400:
        raise ValueError("checkpoint 1 messages are limited to 1400 bytes")

    # Our tiny payload starts with a recognizable marker and an explicit length.
    # The length matters because short Ethernet frames are padded with zero bytes.
    payload = PROTOCOL_MAGIC + struct.pack("!H", len(message_bytes)) + message_bytes

    # A switch reads these fields from left to right: where the frame is going,
    # where it came from, and which higher-level protocol owns the payload.
    frame = destination + source + struct.pack("!H", ETHERTYPE) + payload

    # Ethernet frames must occupy at least 64 bytes on the wire. The network card
    # appends a four-byte checksum (FCS), so software pads our portion to 60 bytes.
    return frame.ljust(MINIMUM_FRAME_WITHOUT_FCS, b"\x00")


def parse_frame(frame: bytes) -> ReceivedFrame:
    """Validate and decode a frame belonging to checkpoint 1."""
    if len(frame) < HEADER_LENGTH + len(PROTOCOL_MAGIC) + 2:
        raise ValueError("frame is too short")

    destination = frame[0:6]
    source = frame[6:12]
    ether_type = struct.unpack("!H", frame[12:14])[0]
    if ether_type != ETHERTYPE:
        raise ValueError(f"unexpected EtherType 0x{ether_type:04x}")

    payload = frame[HEADER_LENGTH:]
    if payload[:4] != PROTOCOL_MAGIC:
        raise ValueError("payload is not a checkpoint 1 No-IP Chat message")

    message_length = struct.unpack("!H", payload[4:6])[0]
    message_bytes = payload[6 : 6 + message_length]
    if len(message_bytes) != message_length:
        raise ValueError("message was truncated")

    return ReceivedFrame(destination, source, message_bytes.decode("utf-8"))
