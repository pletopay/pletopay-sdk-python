"""Webhook signature verification.

Pletopay signs every delivery: ``X-PletoPay-Signature: t=<unix seconds>,v1=<hex HMAC-SHA256(secret, "<t>.<raw body>")>``.
Verify against the **raw request body** (``request.get_data()`` in Flask, ``await request.body()``
in FastAPI), never a re-serialised object, and reject timestamps older than the tolerance.
"""

from __future__ import annotations

import hmac
import json
import re
import time
import warnings
from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from pydantic import TypeAdapter, ValidationError

from pletopay._lenient import construct_lenient
from pletopay.errors import PletopayError, SignatureVerificationError
from pletopay.types import Event, UnknownEvent
from pletopay.types._events import EVENT_CLASSES, EVENT_TYPES, KnownEvent

DEFAULT_TOLERANCE_SECONDS = 300
SIGNATURE_HEADER = "X-PletoPay-Signature"
# A v1 signature is hex HMAC-SHA256: anything else cannot match, and ``hmac.compare_digest`` raises
# ``TypeError`` on non-ASCII text, which must stay a verification failure, not a crash.
_HEX_SIGNATURE = re.compile(r"^[0-9a-fA-F]{64}$")

_EVENT_ADAPTER: TypeAdapter[Any] = TypeAdapter(KnownEvent)


@dataclass(frozen=True)
class ParsedSignature:
    timestamp: int
    signatures: tuple[str, ...]


def _as_bytes(payload: bytes | bytearray | memoryview | str) -> bytes:
    if isinstance(payload, str):
        return payload.encode("utf-8")
    if isinstance(payload, (bytes, bytearray, memoryview)):
        return bytes(payload)
    raise PletopayError(
        "The webhook payload must be the raw request body (bytes or str), not a parsed object: "
        "re-serialised JSON does not verify"
    )


def parse_signature_header(header: str | None) -> ParsedSignature:
    """Parses ``t=<unix seconds>,v1=<hex>[,v1=<hex>]``."""
    if not isinstance(header, str) or not header.strip():
        raise SignatureVerificationError(f"Missing {SIGNATURE_HEADER} header")
    timestamp: int | None = None
    signatures: list[str] = []
    for part in header.split(","):
        key, sep, value = part.partition("=")
        if not sep:
            continue
        key, value = key.strip(), value.strip()
        if key == "t":
            try:
                timestamp = int(value)
            except ValueError:
                timestamp = None
        elif key == "v1" and value:
            signatures.append(value)
    if timestamp is None:
        raise SignatureVerificationError(f"Malformed {SIGNATURE_HEADER} header: no timestamp")
    if not signatures:
        raise SignatureVerificationError(f"Malformed {SIGNATURE_HEADER} header: no v1 signature")
    return ParsedSignature(timestamp=timestamp, signatures=tuple(signatures))


def compute_signature(secret: str, timestamp: int, payload: bytes | str) -> str:
    """hex HMAC-SHA256(secret, ``f"{timestamp}."`` + payload)."""
    return hmac.new(secret.encode("utf-8"), f"{timestamp}.".encode() + _as_bytes(payload), sha256).hexdigest()


def _check_secret(secret: object) -> str:
    if not isinstance(secret, str) or not secret:
        raise PletopayError("A webhook signing secret (whsec_…) is required to verify signatures")
    return secret


def assert_signature(
    payload: bytes | str,
    sig_header: str | None,
    secret: str,
    *,
    tolerance: int = DEFAULT_TOLERANCE_SECONDS,
    now: float | None = None,
) -> ParsedSignature:
    """Raises :class:`SignatureVerificationError` unless the delivery is authentic and fresh."""
    secret = _check_secret(secret)
    raw = _as_bytes(payload)
    parsed = parse_signature_header(sig_header)
    current = int(now if now is not None else time.time())
    if abs(current - parsed.timestamp) > tolerance:
        raise SignatureVerificationError(
            f"Timestamp outside the tolerance zone ({abs(current - parsed.timestamp)} s > {tolerance} s)"
        )
    expected = compute_signature(secret, parsed.timestamp, raw)
    if not any(
        _HEX_SIGNATURE.match(given) and hmac.compare_digest(expected, given.lower()) for given in parsed.signatures
    ):
        raise SignatureVerificationError("No signature found matching the expected signature for the payload")
    return parsed


def verify_signature(
    payload: bytes | str,
    sig_header: str | None,
    secret: str,
    *,
    tolerance: int = DEFAULT_TOLERANCE_SECONDS,
    now: float | None = None,
) -> bool:
    """``True`` when the delivery is authentic and fresh. Never raises for a bad header or signature."""
    try:
        assert_signature(payload, sig_header, secret, tolerance=tolerance, now=now)
    except SignatureVerificationError:
        return False
    return True


def parse_event(data: Any) -> Event:
    """Builds the typed event for a decoded payload; unknown event types become :class:`UnknownEvent`."""
    if not isinstance(data, dict) or data.get("object") != "event":
        raise SignatureVerificationError("The webhook payload is not an event object")
    event_type = data.get("type")
    if event_type in EVENT_TYPES:
        try:
            event: Event = _EVENT_ADAPTER.validate_python(data)
            return event
        except ValidationError as exc:
            # The event's object changed in a way this SDK version does not describe: keep the typed
            # class, built without validation, so handlers keep working.
            warnings.warn(
                f"pletopay: {event_type} event did not match this SDK's schema ({exc.error_count()} issue(s)); update the SDK.",
                stacklevel=2,
            )
            return construct_lenient(EVENT_CLASSES[event_type], data)
    return UnknownEvent.model_validate(data)


def construct_event(
    payload: bytes | str,
    sig_header: str | None,
    secret: str,
    *,
    tolerance: int = DEFAULT_TOLERANCE_SECONDS,
    now: float | None = None,
) -> Event:
    """Verifies the signature and returns the parsed, typed event.

    Raises :class:`SignatureVerificationError` for a missing, malformed, stale or wrong signature, or
    a body that is not an event.
    """
    assert_signature(payload, sig_header, secret, tolerance=tolerance, now=now)
    try:
        data = json.loads(_as_bytes(payload))
    except ValueError as exc:
        raise SignatureVerificationError("The webhook payload is not valid JSON") from exc
    return parse_event(data)


def generate_test_header(payload: bytes | str, secret: str, *, timestamp: int | None = None) -> str:
    """A valid ``X-PletoPay-Signature`` for ``payload``, to test your own handler."""
    secret = _check_secret(secret)
    ts = timestamp if timestamp is not None else int(time.time())
    return f"t={ts},v1={compute_signature(secret, ts, payload)}"


def is_known_event_type(event_type: str) -> bool:
    return event_type in EVENT_TYPES


class Webhook:
    """Signature verification, optionally bound to a secret (``Pletopay(webhook_secret=…).webhooks``).

    The module-level functions (:func:`construct_event`, :func:`verify_signature`,
    :func:`generate_test_header`) are also available as static methods here.
    """

    def __init__(self, secret: str | None = None, *, tolerance: int = DEFAULT_TOLERANCE_SECONDS) -> None:
        self._secret = secret
        self._tolerance = tolerance

    def _resolve(self, secret: str | None) -> str:
        value = secret or self._secret
        if not value:
            raise PletopayError("No webhook secret: pass one here or set `webhook_secret` on the client")
        return value

    def construct_event(
        self, payload: bytes | str, sig_header: str | None, secret: str | None = None, *, tolerance: int | None = None
    ) -> Event:
        return construct_event(
            payload, sig_header, self._resolve(secret), tolerance=self._tolerance if tolerance is None else tolerance
        )

    def verify_signature(
        self, payload: bytes | str, sig_header: str | None, secret: str | None = None, *, tolerance: int | None = None
    ) -> bool:
        return verify_signature(
            payload, sig_header, self._resolve(secret), tolerance=self._tolerance if tolerance is None else tolerance
        )

    def generate_test_header(
        self, payload: bytes | str, secret: str | None = None, *, timestamp: int | None = None
    ) -> str:
        return generate_test_header(payload, self._resolve(secret), timestamp=timestamp)
