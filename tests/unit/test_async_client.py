from __future__ import annotations

import inspect

import httpx
import pytest

from pletopay import AsyncPletopay, NotFoundError, resources
from tests.conftest import BASE, TEST_KEY, api_error, ok, page


async def test_async_calls_and_pagination(async_client: AsyncPletopay, mock_api) -> None:
    mock_api.get("/api/v1/balance").mock(return_value=ok({"object": "balance", "currency": "NGN"}))
    balance = await async_client.balance.retrieve()
    assert balance.currency == "NGN"
    assert balance.last_response.request_id == "req_test"

    mock_api.get("/api/v1/customers").mock(
        side_effect=[
            page([{"id": "cus_2", "object": "customer"}], True, "cus_2"),
            page([{"id": "cus_1", "object": "customer"}], False, None),
        ]
    )
    first = await async_client.customers.list(limit=1)
    assert first.has_more and first.next_cursor == "cus_2"
    ids = [c.id async for c in first.auto_paging_iter()]
    assert ids == ["cus_2", "cus_1"]


async def test_async_errors_and_retries(mock_api) -> None:
    mock_api.get("/api/v1/payments/pay_x").mock(
        side_effect=[
            api_error(503, "api_error", "service_unavailable"),
            api_error(404, "not_found", "resource_missing"),
        ]
    )
    import pletopay._client as mod

    slept: list[float] = []

    async def fake_sleep(s: float) -> None:
        slept.append(s)

    original = mod.asyncio.sleep
    mod.asyncio.sleep = fake_sleep  # type: ignore[assignment]
    try:
        async with AsyncPletopay(TEST_KEY, base_url=BASE, max_retries=2) as c:
            with pytest.raises(NotFoundError):
                await c.payments.retrieve("pay_x")
    finally:
        mod.asyncio.sleep = original  # type: ignore[assignment]
    assert len(slept) == 1


async def test_async_transport_errors(mock_api) -> None:
    mock_api.get("/api/v1/balance").mock(side_effect=httpx.ConnectError("boom"))
    from pletopay import APIConnectionError

    async with AsyncPletopay(TEST_KEY, base_url=BASE, max_retries=0) as c:
        with pytest.raises(APIConnectionError, match="boom"):
            await c.balance.retrieve()


def test_sync_and_async_resources_have_identical_signatures() -> None:
    """The async classes are hand-written twins: any drift in parameters or defaults fails here."""
    pairs = [
        (name, getattr(resources, name), getattr(resources, f"Async{name}"))
        for name in resources.__all__
        if not name.startswith("Async") and name[0].isupper()
    ]
    assert len(pairs) == 22
    checked = 0
    for name, sync_cls, async_cls in pairs:
        for attr, fn in inspect.getmembers(sync_cls, inspect.isfunction):
            if attr.startswith("_"):
                continue
            twin = getattr(async_cls, attr, None)
            assert twin is not None, f"Async{name}.{attr} is missing"
            assert inspect.iscoroutinefunction(twin), f"Async{name}.{attr} must be async"
            sig_sync = inspect.signature(fn)
            sig_async = inspect.signature(twin)
            assert sig_sync.parameters == sig_async.parameters, f"{name}.{attr} parameters differ"
            assert str(sig_sync.return_annotation).replace("SyncPage", "Page") == str(
                sig_async.return_annotation
            ).replace("AsyncPage", "Page"), f"{name}.{attr} return differs"
            checked += 1
    assert checked >= 82
