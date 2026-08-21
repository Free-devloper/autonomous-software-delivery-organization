"""Identifiers with sortable creation-time semantics."""

from __future__ import annotations

import secrets
import time
from uuid import UUID


def new_uuid7() -> UUID:
    """Create an RFC 9562 UUIDv7 without requiring a database extension."""
    timestamp_ms = time.time_ns() // 1_000_000
    random_a = secrets.randbits(12)
    random_b = secrets.randbits(62)
    value = (timestamp_ms << 80) | (0x7 << 76) | (random_a << 64) | (0b10 << 62) | random_b
    return UUID(int=value)
