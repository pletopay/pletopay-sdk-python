from __future__ import annotations

import json
from collections.abc import Callable, Iterator
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


def list_api(count: int, *, backward_cursor: bool = True) -> Callable[[httpx.Request], httpx.Response]:
    """The API's list semantics over pay_1 (oldest) … pay_<count> (newest), as a respx side effect.

    ``starting_after`` returns the older objects, ``ending_before`` the newer ones nearest the cursor, both
    newest first within the page, and ``meta.next_cursor`` is the id of the page's last object while there
    are more. ``backward_cursor=False`` answers ``ending_before`` pages with a null cursor.
    """

    def handler(request: httpx.Request) -> httpx.Response:
        params = request.url.params
        limit = int(params.get("limit", 10))
        after, before = params.get("starting_after"), params.get("ending_before")
        if before is not None:
            rows = [n for n in range(1, count + 1) if n > int(before.removeprefix("pay_"))]
        else:
            rows = [n for n in range(count, 0, -1) if after is None or n < int(after.removeprefix("pay_"))]
        has_more = len(rows) > limit
        rows = rows[:limit]
        if before is not None:
            rows.reverse()
        data = [{"id": f"pay_{n}", "object": "payment"} for n in rows]
        with_cursor = has_more and (before is None or backward_cursor)
        return page(data, has_more, data[-1]["id"] if with_cursor else None)

    return handler


class FakeClock:
    """Stands in for ``time`` and ``asyncio`` inside ``pletopay._client``: sleeping only moves ``now``."""

    def __init__(self) -> None:
        self.now = 1000.0
        self.slept: list[float] = []

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.now += seconds

    async def async_sleep(self, seconds: float) -> None:
        self.sleep(seconds)


TRANSFER = {"id": "trf_1", "object": "transfer", "status": "succeeded"}


class SlowApi:
    """The API's idempotency behaviour on a slow money-out, as a respx side effect on a :class:`FakeClock`.

    The first request with a key runs for ``runs_for`` seconds (the client sees a read timeout when that is
    longer than its timeout), requests with the same key meanwhile get ``409 idempotency_request_in_progress``,
    and once it has finished they get its stored response with ``Idempotent-Replayed: true``. The API stores
    it even when the first caller has gone away.
    """

    def __init__(self, clock: FakeClock, runs_for: float, *, in_progress_headers: dict[str, str] | None = None) -> None:
        self.clock = clock
        self.runs_for = runs_for
        self.in_progress_headers = in_progress_headers
        self.started = clock.now
        self.finishes_at: dict[str, float] = {}
        self.calls: list[tuple[float, str]] = []

    @property
    def keys(self) -> set[str]:
        return {key for _at, key in self.calls}

    def __call__(self, request: httpx.Request) -> httpx.Response:
        key = request.headers["idempotency-key"]
        self.calls.append((self.clock.now - self.started, key))
        done = self.finishes_at.get(key)
        if done is None:
            self.finishes_at[key] = self.clock.now + self.runs_for
            timeout = request.extensions["timeout"]["read"]
            if self.runs_for > timeout:
                self.clock.now += timeout
                raise httpx.ReadTimeout("The read operation timed out", request=request)
            self.clock.now += self.runs_for
            return ok(TRANSFER, 201)
        if self.clock.now < done:
            return api_error(
                409, "idempotency_error", "idempotency_request_in_progress", headers=self.in_progress_headers
            )
        return ok(TRANSFER, 201, headers={"idempotent-replayed": "true"})


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> FakeClock:
    import types

    import pletopay._client as mod

    fake = FakeClock()
    monkeypatch.setattr(mod, "time", fake)
    monkeypatch.setattr(mod, "asyncio", types.SimpleNamespace(sleep=fake.async_sleep))
    return fake


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
