from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import httpx
import pytest
import respx

from pletopay import AsyncPletopay, Pletopay

TEST_KEY = "sk_test_0123456789abcdef_0123456789abcdef0123456789abcdef01234567"
LIVE_KEY = "sk_live_0123456789abcdef_0123456789abcdef0123456789abcdef01234567"
BASE = "http://api.test"
FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def envelope(data: Any, message: str = "OK", meta: dict[str, Any] | None = None) -> dict[str, Any]:
    body: dict[str, Any] = {"status": True, "message": message, "data": data}
    if meta is not None:
        body["meta"] = {"url": "/api/v1/x", **meta}
    return body


def ok(data: Any, status_code: int = 200, headers: dict[str, str] | None = None, message: str = "OK") -> httpx.Response:
    return httpx.Response(
        status_code,
        json=envelope(data, message),
        headers={"x-request-id": "req_test", "pletopay-version": "2026-09-25", **(headers or {})},
    )


def page(data: list[Any], has_more: bool, next_cursor: str | None) -> httpx.Response:
    return httpx.Response(
        200,
        json=envelope(data, "Listed", {"has_more": has_more, "next_cursor": next_cursor}),
        headers={"x-request-id": "req_test"},
    )


def api_error(
    status_code: int,
    type_: str,
    code: str,
    *,
    message: str | None = None,
    param: str | None = None,
    details: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> httpx.Response:
    error: dict[str, Any] = {"type": type_, "code": code}
    if param:
        error["param"] = param
    if details:
        error["details"] = details
    return httpx.Response(
        status_code,
        json={"status": False, "message": message or f"{code} happened", "error": error, "request_id": "req_err"},
        headers={"x-request-id": "req_err", **(headers or {})},
    )


def load_fixture(name: str) -> Any:
    return json.loads((FIXTURES / name).read_text())


@pytest.fixture
def mock_api() -> Iterator[respx.MockRouter]:
    with respx.mock(base_url=BASE, assert_all_called=False) as router:
        yield router


@pytest.fixture
def client() -> Iterator[Pletopay]:
    c = Pletopay(TEST_KEY, base_url=BASE, max_retries=0)
    yield c
    c.close()


@pytest.fixture
async def async_client() -> Any:
    c = AsyncPletopay(TEST_KEY, base_url=BASE, max_retries=0)
    yield c
    await c.close()
