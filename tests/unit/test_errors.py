from __future__ import annotations

import httpx
import pytest

from pletopay import errors as e


def body(type_: str, code: str = "c") -> dict:
    return {"status": False, "message": "m", "error": {"type": type_, "code": code}, "request_id": "req_1"}


@pytest.mark.parametrize(
    ("type_", "cls"),
    [
        ("invalid_request", e.InvalidRequestError),
        ("authentication_error", e.AuthenticationError),
        ("permission_error", e.PermissionDeniedError),
        ("not_found", e.NotFoundError),
        ("conflict", e.ConflictError),
        ("idempotency_error", e.IdempotencyError),
        ("rate_limit_error", e.RateLimitError),
        ("api_error", e.APIServerError),
    ],
)
def test_maps_error_type(type_: str, cls: type) -> None:
    err = e.APIError.from_response(400, body(type_), httpx.Headers())
    assert isinstance(err, cls)
    assert err.type == type_
    assert err.request_id == "req_1"
    assert isinstance(err, e.PletopayError)


@pytest.mark.parametrize(
    ("status", "cls"),
    [
        (401, e.AuthenticationError),
        (403, e.PermissionDeniedError),
        (404, e.NotFoundError),
        (409, e.ConflictError),
        (429, e.RateLimitError),
        (500, e.APIServerError),
        (503, e.APIServerError),
        (400, e.InvalidRequestError),
        (418, e.InvalidRequestError),
    ],
)
def test_falls_back_to_status(status: int, cls: type) -> None:
    err = e.APIError.from_response(status, "oops", httpx.Headers({"x-request-id": "req_h"}))
    assert isinstance(err, cls)
    assert err.code is None
    assert err.body == "oops"
    assert err.request_id == "req_h"
    assert str(err) == f"Request failed with HTTP {status} (request_id: req_h)"


def test_details_retry_after_and_rate_limit() -> None:
    headers = httpx.Headers(
        {"retry-after": "3", "ratelimit-limit": "10", "ratelimit-remaining": "0", "ratelimit-reset": "3"}
    )
    raw = body("rate_limit_error", "rate_limited")
    raw["error"]["details"] = {"bucket": "money"}
    err = e.APIError.from_response(429, raw, headers)
    assert isinstance(err, e.RateLimitError)
    assert err.retry_after == 3
    assert err.details == {"bucket": "money"}
    assert err.rate_limit == e.RateLimitInfo(10, 0, 3)


def test_retry_after_parsing() -> None:
    assert e.retry_after_seconds(httpx.Headers()) is None
    assert e.retry_after_seconds(httpx.Headers({"retry-after": "2"})) == 2.0
    assert (
        e.retry_after_seconds(httpx.Headers({"retry-after": "Thu, 01 Jan 2026 00:00:05 GMT"}), now=1767225600.0) == 5.0
    )
    assert e.retry_after_seconds(httpx.Headers({"retry-after": "garbage"})) is None
    assert e.rate_limit_from_headers(httpx.Headers()) is None
    assert e.rate_limit_from_headers(httpx.Headers({"ratelimit-remaining": "5"})) == e.RateLimitInfo(None, 5, None)
