"""Payload formats for discovery announcements and direct chat messages.

Ethernet delivers uninterpreted payload bytes. This module gives those bytes
one of two meanings: HELLO announces a name, while CHAT carries direct-message
text. The destination MAC—not the packet type—decides who receives a frame.
"""

from dataclasses import dataclass
import struct
from typing import Union


HELLO = 1
CHAT = 2
MAGIC = b"NIP5"
_HEADER = struct.Struct("!4sBBH")


@dataclass(frozen=True)
class Hello:
    name: str


@dataclass(frozen=True)
class ChatMessage:
    sender: str
    text: str


Packet = Union[Hello, ChatMessage]


def encode_packet(packet: Packet) -> bytes:
    """Turn one application packet into bytes for an Ethernet payload."""
    if isinstance(packet, Hello):
        kind, name, text = HELLO, packet.name, ""
    elif isinstance(packet, ChatMessage):
        kind, name, text = CHAT, packet.sender, packet.text
    else:
        raise TypeError("packet must be Hello or ChatMessage")

    name_bytes = name.encode("utf-8")
    text_bytes = text.encode("utf-8")
    if not 1 <= len(name_bytes) <= 32:
        raise ValueError("name must occupy 1-32 UTF-8 bytes")
    if len(text_bytes) > 1400:
        raise ValueError("message must occupy at most 1400 UTF-8 bytes")

    # Lengths separate real content from Ethernet's trailing zero padding.
    header = _HEADER.pack(MAGIC, kind, len(name_bytes), len(text_bytes))
    return header + name_bytes + text_bytes


def decode_packet(payload: bytes) -> Packet:
    """Recover a HELLO or CHAT packet from a padded Ethernet payload."""
    if len(payload) < _HEADER.size:
        raise ValueError("payload is shorter than the No-IP Chat header")
    magic, kind, name_length, text_length = _HEADER.unpack_from(payload)
    if magic != MAGIC or kind not in (HELLO, CHAT):
        raise ValueError("payload is not a checkpoint 5 packet")
    end = _HEADER.size + name_length + text_length
    if len(payload) < end:
        raise ValueError("packet was truncated")
    if not 1 <= name_length <= 32 or (kind == HELLO and text_length != 0):
        raise ValueError("packet fields are invalid")

    name_start = _HEADER.size
    text_start = name_start + name_length
    name = payload[name_start:text_start].decode("utf-8")
    text = payload[text_start:end].decode("utf-8")
    return Hello(name) if kind == HELLO else ChatMessage(name, text)
