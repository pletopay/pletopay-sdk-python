from __future__ import annotations

import re
import uuid

from pletopay.errors import PletopayError

IDEMPOTENCY_KEY_PATTERN = re.compile(r"^[\x21-\x7e]{1,255}$")


def generate_idempotency_key() -> str:
    """A fresh random key (UUID v4)."""
    return str(uuid.uuid4())


def assert_idempotency_key(key: object) -> str:
    """Raises locally, before any request, when a key would be rejected by the API."""
    if not isinstance(key, str) or not IDEMPOTENCY_KEY_PATTERN.match(key):
        raise PletopayError("idempotency_key must be 1–255 printable ASCII characters (no spaces)")
    return key
