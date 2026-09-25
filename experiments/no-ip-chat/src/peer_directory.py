"""Turn repeated name announcements into a safe, expiring peer directory."""

from __future__ import annotations

from dataclasses import dataclass
import threading
import time

from ethernet import format_mac


HELLO_INTERVAL_SECONDS = 2.0
PEER_TIMEOUT_SECONDS = 7.0


@dataclass(frozen=True)
class PeerStatus:
    name: str
    macs: tuple[bytes, ...]
    last_seen: float

    @property
    def conflicted(self) -> bool:
        return len(self.macs) > 1

    def describe(self, now: float) -> str:
        addresses = ", ".join(format_mac(mac) for mac in self.macs)
        state = "CONFLICT" if self.conflicted else "available"
        return f"{self.name}: {addresses} · {state} · seen {now - self.last_seen:.1f}s ago"


class PeerDirectory:
    """Record name → MAC observations and reject ambiguous lookups."""

    def __init__(self, timeout: float = PEER_TIMEOUT_SECONDS) -> None:
        self._timeout = timeout
        self._entries: dict[str, dict[bytes, float]] = {}
        self._lock = threading.Lock()

    def observe(self, name: str, mac: bytes, now: float | None = None) -> None:
        """Record one HELLO's payload name and Ethernet source MAC."""
        observed_at = time.monotonic() if now is None else now
        with self._lock:
            self._entries.setdefault(name, {})[mac] = observed_at

    def statuses(self, now: float | None = None) -> list[PeerStatus]:
        """Return current names after removing expired observations."""
        checked_at = time.monotonic() if now is None else now
        with self._lock:
            self._expire(checked_at)
            return [
                PeerStatus(name, tuple(sorted(macs)), max(macs.values()))
                for name, macs in sorted(self._entries.items())
            ]

    def resolve(self, name: str, now: float | None = None) -> bytes:
        """Resolve one unambiguous display name to its current MAC."""
        matches = [status for status in self.statuses(now) if status.name == name]
        if not matches:
            raise ValueError(f"peer is unavailable: {name}")
        if matches[0].conflicted:
            raise ValueError(f"peer name is ambiguous: {name}")
        return matches[0].macs[0]

    def matches(self, name: str, mac: bytes, now: float | None = None) -> bool:
        """Check whether a CHAT source matches one unambiguous HELLO name."""
        try:
            return self.resolve(name, now) == mac
        except ValueError:
            return False

    def has_own_name_conflict(self, own_name: str, now: float | None = None) -> bool:
        """True when another MAC is currently announcing our chosen name."""
        return any(status.name == own_name for status in self.statuses(now))

    def _expire(self, now: float) -> None:
        for name, observations in list(self._entries.items()):
            current = {
                mac: last_seen
                for mac, last_seen in observations.items()
                if now - last_seen <= self._timeout
            }
            if current:
                self._entries[name] = current
            else:
                del self._entries[name]
