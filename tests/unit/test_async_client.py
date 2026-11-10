from __future__ import annotations

import inspect

import httpx
import pytest

from pletopay import AsyncPletopay, IdempotencyError, NotFoundError, resources
from tests.conftest import BASE, TEST_KEY, TRANSFER, FakeClock, SlowApi, api_error, list_api, ok, page

PAYOUT = {
    "amount": 100,
    "reference": "r",
    "narration": "n",
    "beneficiary": {"bank_code": "058", "account_number": "0123456789"},
}


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


async def test_async_ending_before_walks_towards_newer_items(async_client: AsyncPletopay, mock_api) -> None:
    route = mock_api.get("/api/v1/payments").mock(side_effect=list_api(20))
    first = await async_client.payments.list(limit=3, ending_before="pay_9")
    assert [p.id for p in first] == ["pay_12", "pay_11", "pay_10"]
    assert first.has_more and first.next_cursor == "pay_12"
    assert [p.id async for p in first.auto_paging_iter()] == [f"pay_{n}" for n in range(10, 21)]
    assert [len(pg.data) async for pg in first.pages()] == [3, 3, 3, 2]
    assert [p.id for p in await first.auto_paging_list(limit=4)] == ["pay_10", "pay_11", "pay_12", "pay_13"]
    assert not any("starting_after" in call.request.url.params for call in route.calls)

    mock_api.get("/api/v1/customers").mock(side_effect=list_api(20, backward_cursor=False))
    customers = await async_client.customers.list(limit=3, ending_before="pay_9")
    assert len(await customers.auto_paging_list()) == 11


async def test_async_keeps_asking_while_a_money_out_is_in_progress(mock_api, clock: FakeClock) -> None:
    api = SlowApi(clock, 60.0)
    mock_api.post("/api/v1/transfers").mock(side_effect=api)
    async with AsyncPletopay(TEST_KEY, base_url=BASE, timeout=30.0, max_retries=2) as c:
        transfer = await c.transfers.create(**PAYOUT)
    assert transfer.id == TRANSFER["id"]
    assert transfer.last_response.idempotent_replayed
    assert len(api.calls) > 10 and len(api.keys) == 1
    assert transfer.last_response.idempotency_key in api.keys
    assert 60.0 <= api.calls[-1][0] < 62.5


async def test_async_gives_up_90s_after_the_call_started(mock_api, clock: FakeClock) -> None:
    api = SlowApi(clock, 200.0)
    mock_api.post("/api/v1/refunds").mock(side_effect=api)
    async with AsyncPletopay(TEST_KEY, base_url=BASE, timeout=30.0, max_retries=2) as c:
        with pytest.raises(IdempotencyError) as info:
            await c.refunds.create(payment="pay_1", reason="r", idempotency_key="refund-R-1")
    assert info.value.code == "idempotency_request_in_progress"
    assert info.value.idempotency_key == "refund-R-1"
    assert api.keys == {"refund-R-1"}
    assert clock.now - api.started == pytest.approx(90.0)


async def test_async_money_out_default_timeout_and_slow_bank(mock_api, clock: FakeClock) -> None:
    api = SlowApi(clock, 75.0)
    route = mock_api.post("/api/v1/transfers").mock(side_effect=api)
    async with AsyncPletopay(TEST_KEY, base_url=BASE) as c:
        assert (await c.transfers.create(**PAYOUT)).id == TRANSFER["id"]
    assert len(api.calls) == 1
    assert route.calls[0].request.extensions["timeout"]["read"] == 90.0


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
