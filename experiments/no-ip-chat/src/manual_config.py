"""Load the small, visible address book used only by checkpoint 4."""

from dataclasses import dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class ParticipantConfig:
    name: str
    peers: dict[str, str]


def load_config(path: str) -> ParticipantConfig:
    """Read one participant's name and manually configured peer MACs."""
    data = json.loads(Path(path).read_text())
    name = data.get("name")
    peers = data.get("peers")
    if not isinstance(name, str) or not name:
        raise ValueError("config requires a non-empty name")
    if not isinstance(peers, dict) or not peers:
        raise ValueError("config requires at least one peer")
    valid_entries = all(
        isinstance(peer, str) and isinstance(mac, str)
        for peer, mac in peers.items()
    )
    if not valid_entries:
        raise ValueError("each peer must map a name to a MAC address")
    if name in peers:
        raise ValueError("a participant must not list itself as a peer")
    return ParticipantConfig(name, peers)
