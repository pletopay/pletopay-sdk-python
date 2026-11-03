"""Official Python SDK for the Pletopay API.

>>> import pletopay
>>> client = pletopay.Pletopay(secret_key="sk_test_…")
>>> payment = client.payments.create(amount=5000000, currency="NGN", reference="ORDER-123")
"""

from __future__ import annotations

from pletopay import types
from pletopay._client import AsyncPletopay, Hooks, Pletopay, RequestOptions
from pletopay._idempotency import IDEMPOTENCY_KEY_PATTERN, generate_idempotency_key
from pletopay._operations import OPERATIONS, Operation
from pletopay._pagination import AsyncPage, SyncPage
from pletopay._query import encode_query
from pletopay._response import ListMeta, RawResponse, ResponseInfo
from pletopay._version import __version__
from pletopay.errors import (
    APIConnectionError,
    APIError,
    APIServerError,
    APITimeoutError,
    AuthenticationError,
    ConflictError,
    IdempotencyError,
    InvalidRequestError,
    NotFoundError,
    PermissionDeniedError,
    PletopayError,
    RateLimitError,
    RateLimitInfo,
    SignatureVerificationError,
)
from pletopay.types import EVENT_TYPES, Event, EventType, UnknownEvent
from pletopay.types._events import SPEC_API_VERSION as API_VERSION
from pletopay.webhook import (
    DEFAULT_TOLERANCE_SECONDS,
    SIGNATURE_HEADER,
    ParsedSignature,
    Webhook,
    assert_signature,
    compute_signature,
    construct_event,
    generate_test_header,
    is_known_event_type,
    parse_signature_header,
    verify_signature,
)

__all__ = [
    "API_VERSION",
    "DEFAULT_TOLERANCE_SECONDS",
    "EVENT_TYPES",
    "IDEMPOTENCY_KEY_PATTERN",
    "OPERATIONS",
    "SIGNATURE_HEADER",
    "APIConnectionError",
    "APIError",
    "APIServerError",
    "APITimeoutError",
    "AsyncPage",
    "AsyncPletopay",
    "AuthenticationError",
    "ConflictError",
    "Event",
    "EventType",
    "Hooks",
    "IdempotencyError",
    "InvalidRequestError",
    "ListMeta",
    "NotFoundError",
    "Operation",
    "ParsedSignature",
    "PermissionDeniedError",
    "Pletopay",
    "PletopayError",
    "RateLimitError",
    "RateLimitInfo",
    "RawResponse",
    "RequestOptions",
    "ResponseInfo",
    "SignatureVerificationError",
    "SyncPage",
    "UnknownEvent",
    "Webhook",
    "__version__",
    "assert_signature",
    "compute_signature",
    "construct_event",
    "encode_query",
    "generate_idempotency_key",
    "generate_test_header",
    "is_known_event_type",
    "parse_signature_header",
    "types",
    "verify_signature",
]
