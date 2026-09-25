"""The tiny application protocol introduced when one frame becomes a chat.

Ethernet tells us which network interface should receive some bytes. It does
not say who typed them or where the text ends. This file defines only that
meaning, keeping it separate from the Ethernet header in ``ethernet.py``.
"""

from dataclasses import dataclass
import struct


MAGIC = b"NIP2"
_HEADER = struct.Struct("!4sBH")


@dataclass(frozen=True)
class ChatMessage:
    # ``sender`` is a display name chosen by our application. It lives in the
    # payload; it is not part of the Ethernet header and is not authenticated.
    sender: str
    text: str


def encode_message(message: ChatMessage) -> bytes:
    sender = message.sender.encode("utf-8")
    text = message.text.encode("utf-8")
    if not 1 <= len(sender) <= 32:
        raise ValueError("sender must occupy 1-32 UTF-8 bytes")
    if len(text) > 1400:
        raise ValueError("message must occupy at most 1400 UTF-8 bytes")

    # The two lengths let the receiver ignore Ethernet's trailing padding and
    # separate the sender name from the message without guessing delimiters.
    return _HEADER.pack(MAGIC, len(sender), len(text)) + sender + text


def decode_message(payload: bytes) -> ChatMessage:
    if len(payload) < _HEADER.size:
        raise ValueError("payload is shorter than the chat header")

    magic, sender_length, text_length = _HEADER.unpack_from(payload)
    if magic != MAGIC:
        raise ValueError("payload is not a checkpoint 2 chat message")

    expected_length = _HEADER.size + sender_length + text_length
    if len(payload) < expected_length:
        raise ValueError("chat message was truncated")

    sender_start = _HEADER.size
    text_start = sender_start + sender_length
    return ChatMessage(
        sender=payload[sender_start:text_start].decode("utf-8"),
        text=payload[text_start:expected_length].decode("utf-8"),
    )
