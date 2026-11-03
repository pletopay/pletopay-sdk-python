"""Live tests run against a real API (normally a local one) with a test-mode key:

    PLETOPAY_API_URL=http://localhost:8080 PLETOPAY_SECRET_KEY=sk_test_… pytest tests/live

They are skipped when PLETOPAY_SECRET_KEY is not set.
"""

from __future__ import annotations

import os
import time
import uuid
from collections.abc import Callable, Iterator
from typing import TypeVar

import pytest

from pletopay import APIError, Pletopay

T = TypeVar("T")
SECRET_KEY = os.environ.get("PLETOPAY_SECRET_KEY")
API_URL = os.environ.get("PLETOPAY_API_URL", "http://localhost:8080")
enabled = bool(SECRET_KEY and SECRET_KEY.startswith("sk_test_"))

pytestmark = pytest.mark.live


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    if enabled:
        return
    skip = pytest.mark.skip(reason="PLETOPAY_SECRET_KEY (sk_test_…) not set")
    for item in items:
        if "live" in str(item.fspath):
            item.add_marker(skip)


@pytest.fixture(scope="session")
def live() -> Iterator[Pletopay]:
    assert SECRET_KEY
    client = Pletopay(SECRET_KEY, base_url=API_URL)
    yield client
    client.close()


def unique(prefix: str) -> str:
    return f"{prefix}-{int(time.time() * 1000)}-{uuid.uuid4().hex[:6]}"


def poll(fn: Callable[[], T], until: Callable[[T], bool], *, timeout: float = 45.0, interval: float = 1.0) -> T:
    deadline = time.monotonic() + timeout
    value = fn()
    while not until(value):
        if time.monotonic() > deadline:
            raise TimeoutError(f"timed out waiting; last value: {value!r}"[:600])
        time.sleep(interval)
        value = fn()
    return value


def is_bank_unavailable(error: BaseException) -> bool:
    return isinstance(error, APIError) and error.code in ("service_unavailable", "service_paused")
