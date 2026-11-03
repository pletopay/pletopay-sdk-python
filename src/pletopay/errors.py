"""Exceptions raised by the SDK.

Every API failure is a subclass of :class:`APIError`, chosen from the response's ``error.type``.
Branch on :attr:`APIError.code` (stable) or on the class; ``message`` is for people and may change.
"""

from __future__ import annotations

from email.utils import parsedate_to_datetime
from typing import Any

import httpx


class PletopayError(Exception):
    """Base class of every error this SDK raises."""


class RateLimitInfo:
    """The ``RateLimit-*`` headers of a response."""

    __slots__ = ("limit", "remaining", "reset")

    def __init__(self, limit: int | None, remaining: int | None, reset: int | None) -> None:
        self.limit = limit
        self.remaining = remaining
        self.reset = reset

    def __repr__(self) -> str:
        return f"RateLimitInfo(limit={self.limit}, remaining={self.remaining}, reset={self.reset})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, RateLimitInfo) and (self.limit, self.remaining, self.reset) == (
            other.limit,
            other.remaining,
            other.reset,
        )


def _int_header(headers: httpx.Headers, name: str) -> int | None:
    value = headers.get(name)
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def rate_limit_from_headers(headers: httpx.Headers) -> RateLimitInfo | None:
    info = RateLimitInfo(
        _int_header(headers, "ratelimit-limit"),
        _int_header(headers, "ratelimit-remaining"),
        _int_header(headers, "ratelimit-reset"),
    )
    if info.limit is None and info.remaining is None and info.reset is None:
        return None
    return info


def retry_after_seconds(headers: httpx.Headers, now: float | None = None) -> float | None:
    """``Retry-After`` as seconds (delay-seconds or an HTTP date); ``None`` when absent or unreadable."""
    value = headers.get("retry-after")
    if value is None or not value.strip():
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        pass
    try:
        when = parsedate_to_datetime(value).timestamp()
    except (TypeError, ValueError, IndexError):
        return None
    import time

    return max(0.0, when - (now if now is not None else time.time()))


def _envelope(body: Any) -> dict[str, Any] | None:
    if isinstance(body, dict) and isinstance(body.get("error"), dict):
        return body
    return None


class APIError(PletopayError):
    """The API answered with an error envelope (``status: false``)."""

    status_code: int
    type: str | None
    code: str | None
    param: str | None
    details: dict[str, Any] | None
    request_id: str | None
    headers: httpx.Headers
    body: Any
    rate_limit: RateLimitInfo | None

    def __init__(self, status_code: int, body: Any, headers: httpx.Headers, message: str | None = None) -> None:
        envelope = _envelope(body)
        error = envelope["error"] if envelope else {}
        request_id = (envelope or {}).get("request_id") or headers.get("x-request-id")
        base = message or (envelope or {}).get("message") or f"Request failed with HTTP {status_code}"
        super().__init__(f"{base} (request_id: {request_id})" if request_id else base)
        self.status_code = status_code
        self.type = error.get("type")
        self.code = error.get("code")
        self.param = error.get("param")
        self.details = error.get("details")
        self.request_id = request_id
        self.headers = headers
        self.body = body
        self.rate_limit = rate_limit_from_headers(headers)

    @property
    def message(self) -> str:
        return str(self)

    @classmethod
    def from_response(cls, status_code: int, body: Any, headers: httpx.Headers) -> APIError:
        """Builds the right subclass from ``error.type``, falling back to the status code."""
        envelope = _envelope(body)
        error_type = envelope["error"].get("type") if envelope else None
        by_type: dict[str, type[APIError]] = {
            "invalid_request": InvalidRequestError,
            "authentication_error": AuthenticationError,
            "permission_error": PermissionDeniedError,
            "not_found": NotFoundError,
            "conflict": ConflictError,
            "idempotency_error": IdempotencyError,
            "rate_limit_error": RateLimitError,
            "api_error": APIServerError,
        }
        klass = by_type.get(error_type or "")
        if klass is None:
            if status_code == 401:
                klass = AuthenticationError
            elif status_code == 403:
                klass = PermissionDeniedError
            elif status_code == 404:
                klass = NotFoundError
            elif status_code == 409:
                klass = ConflictError
            elif status_code == 429:
                klass = RateLimitError
            elif status_code >= 500:
                klass = APIServerError
            elif status_code >= 400:
                klass = InvalidRequestError
            else:
                klass = APIError
        return klass(status_code, body, headers)


class InvalidRequestError(APIError):
    """400: a field is missing, invalid or unknown (``param`` names it), or the request is malformed."""


class AuthenticationError(APIError):
    """401: missing or invalid secret key, or a publishable key used as a bearer."""


class PermissionDeniedError(APIError):
    """403: the key, mode or account is not allowed to do this (e.g. ``test_mode_only``)."""


class NotFoundError(APIError):
    """404: no such resource for this organization and mode."""


class ConflictError(APIError):
    """409: the resource is in the wrong state (e.g. ``duplicate_reference``)."""


class IdempotencyError(APIError):
    """409/422: an ``Idempotency-Key`` problem (``idempotency_key_reused``, ``idempotency_request_in_progress``)."""


class RateLimitError(APIError):
    """429: too many requests; wait ``retry_after`` seconds. The SDK already retried when that was safe."""

    retry_after: float | None

    def __init__(self, status_code: int, body: Any, headers: httpx.Headers, message: str | None = None) -> None:
        super().__init__(status_code, body, headers, message)
        self.retry_after = retry_after_seconds(headers)


class APIServerError(APIError):
    """5xx: Pletopay could not complete the request. Retry with the same ``Idempotency-Key``."""


class APIConnectionError(PletopayError):
    """The request never reached the API or no response arrived."""


class APITimeoutError(APIConnectionError):
    """The request exceeded the timeout."""


class SignatureVerificationError(PletopayError):
    """A webhook's ``X-PletoPay-Signature`` did not verify. Reject the delivery."""
