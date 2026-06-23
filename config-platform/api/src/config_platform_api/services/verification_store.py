"""Issue and validate short-lived connection test tokens."""

import secrets
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class _VerificationEntry:
    fingerprint: str
    expires_at: float


class VerificationStore:
    def __init__(self, ttl_seconds: int = 900) -> None:
        self._ttl_seconds = ttl_seconds
        self._entries: dict[str, _VerificationEntry] = {}

    def issue(self, fingerprint: str) -> str:
        self._purge_expired()
        token = secrets.token_urlsafe(24)
        self._entries[token] = _VerificationEntry(
            fingerprint=fingerprint,
            expires_at=time.time() + self._ttl_seconds,
        )
        return token

    def consume(self, token: str, fingerprint: str) -> bool:
        self._purge_expired()
        entry = self._entries.get(token)
        if entry is None or entry.fingerprint != fingerprint or entry.expires_at < time.time():
            return False
        del self._entries[token]
        return True

    def _purge_expired(self) -> None:
        now = time.time()
        expired = [token for token, entry in self._entries.items() if entry.expires_at < now]
        for token in expired:
            del self._entries[token]
