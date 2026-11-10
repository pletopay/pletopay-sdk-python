from __future__ import annotations

import random

import httpx
import pytest

from pletopay import (
    APIConnectionError,
    APIError,
    APIServerError,
    APITimeoutError,
    IdempotencyError,
    InvalidRequestError,
    Pletopay,
    RateLimitError,
    RequestOptions,
)
from pletopay import _constants as c
from pletopay._retry import IN_PROGRESS_POLL, IN_PROGRESS_WAIT, in_progress_delay, is_retryable_status, retry_delay
from tests.conftest import BASE, TEST_KEY, TRANSFER, FakeClock, SlowApi, api_error, ok

PAYOUT = {
    "amount": 100,
    "reference": "r",
    "narration": "n",
    "beneficiary": {"bank_code": "058", "account_number": "0123456789"},
}


def test_retryable_statuses() -> None:
    assert is_retryable_status(429, "rate_limited")
    assert (
        is_retryable_status(500, None)
        and is_retryable_status(502, None)
        and is_retryable_status(503, "service_unavailable")
    )
    assert is_retryable_status(409, "idempotency_request_in_progress")
    assert not is_retryable_status(409, "duplicate_reference")
    assert not is_retryable_status(422, "idempotency_key_reused")
    assert not is_retryable_status(400, "parameter_invalid")
    assert not is_retryable_status(504, None)


class _Fixed(random.Random):
    def __init__(self, value: float) -> None:
        super().__init__()
        self._value = value

    def random(self) -> float:
        return self._value


def test_backoff() -> None:
    assert retry_delay(0, rand=_Fixed(0.0)) == 0.25
    assert retry_delay(0, rand=_Fixed(1.0)) == 0.5
    assert retry_delay(1, rand=_Fixed(1.0)) == 1.0
    assert retry_delay(10, rand=_Fixed(1.0)) == 8.0
    assert retry_delay(0, retry_after=2.5) == 2.5
    assert retry_delay(0, retry_after=120) == 60.0


def test_in_progress_polling_delay() -> None:
    assert (IN_PROGRESS_POLL, IN_PROGRESS_WAIT) == (2.0, 90.0)
    assert in_progress_delay(30.0) == 2.0
    assert in_progress_delay(30.0, retry_after=5) == 5.0
    assert in_progress_delay(30.0, retry_after=0) == 2.0
    assert in_progress_delay(89.5) == 0.5
    assert in_progress_delay(89.5, retry_after=5) == 0.5
    assert in_progress_delay(90.0) is None


@pytest.fixture
def no_sleep(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    slept: list[float] = []
    import pletopay._client as mod

    monkeypatch.setattr(mod.time, "sleep", slept.append)
    return slept


def client(retries: int) -> Pletopay:
    return Pletopay(TEST_KEY, base_url=BASE, max_retries=retries)


def test_retries_get_on_5xx(mock_api, no_sleep) -> None:
    route = mock_api.get("/api/v1/balance").mock(
        side_effect=[
            api_error(503, "api_error", "service_unavailable"),
            api_error(500, "api_error", "internal_error"),
            ok({"object": "balance"}),
        ]
    )
    assert client(2).balance.retrieve().object == "balance"
    assert route.call_count == 3
    assert len(no_sleep) == 2


def test_gives_up_after_max_retries(mock_api, no_sleep) -> None:
    route = mock_api.get("/api/v1/balance").mock(return_value=api_error(500, "api_error", "internal_error"))
    with pytest.raises(APIServerError):
        client(1).balance.retrieve()
    assert route.call_count == 2


def test_retries_post_with_idempotency_key_reusing_it(mock_api, no_sleep) -> None:
    route = mock_api.post("/api/v1/payments").mock(
        side_effect=[api_error(503, "api_error", "service_unavailable"), ok({"id": "pay_1", "object": "payment"}, 201)]
    )
    assert client(2).payments.create(amount=1, currency="NGN", reference="r").id == "pay_1"
    assert route.call_count == 2
    assert route.calls[0].request.headers["idempotency-key"] == route.calls[1].request.headers["idempotency-key"]


def test_does_not_retry_post_without_idempotency_key(mock_api, no_sleep) -> None:
    route = mock_api.post("/api/v1/transfers/name-enquiry").mock(
        return_value=api_error(503, "api_error", "service_unavailable")
    )
    with pytest.raises(APIServerError):
        client(2).transfers.resolve_account(bank_code="058", account_number="0123456789")
    assert route.call_count == 1


def test_honours_retry_after_and_reports_to_hook(mock_api, no_sleep) -> None:
    from pletopay import Hooks

    retries: list[dict] = []
    mock_api.get("/api/v1/balance").mock(
        side_effect=[api_error(429, "rate_limit_error", "rate_limited", headers={"retry-after": "2"}), ok({})]
    )
    Pletopay(TEST_KEY, base_url=BASE, max_retries=1, hooks=Hooks(on_retry=retries.append)).balance.retrieve()
    assert no_sleep == [2.0]
    assert retries[0]["status_code"] == 429 and retries[0]["code"] == "rate_limited" and retries[0]["delay"] == 2.0


def test_surfaces_429_when_exhausted(mock_api, no_sleep) -> None:
    mock_api.get("/api/v1/balance").mock(
        return_value=api_error(429, "rate_limit_error", "rate_limited", headers={"retry-after": "1"})
    )
    with pytest.raises(RateLimitError) as info:
        client(0).balance.retrieve()
    assert info.value.retry_after == 1


def test_409_in_progress_retried_but_not_other_conflicts(mock_api, no_sleep) -> None:
    route = mock_api.post("/api/v1/transfers").mock(
        side_effect=[api_error(409, "idempotency_error", "idempotency_request_in_progress"), ok({"id": "trf_1"}, 201)]
    )
    kwargs = dict(
        amount=100,
        reference="r",
        narration="n",
        beneficiary={"bank_code": "058", "account_number": "0123456789"},
        idempotency_key="k",
    )
    assert client(1).transfers.create(**kwargs).id == "trf_1"
    assert route.call_count == 2
    route.mock(return_value=api_error(409, "conflict", "duplicate_reference"))
    from pletopay import ConflictError

    with pytest.raises(ConflictError):
        client(1).transfers.create(**kwargs)
    assert route.call_count == 3


def test_connection_errors_are_retried_then_wrapped(mock_api, no_sleep) -> None:
    route = mock_api.get("/api/v1/balance").mock(side_effect=httpx.ConnectError("boom"))
    with pytest.raises(APIConnectionError, match="boom") as info:
        client(1).balance.retrieve()
    assert isinstance(info.value.__cause__, httpx.ConnectError)
    assert route.call_count == 2


def test_timeouts_become_timeout_errors(mock_api, no_sleep) -> None:
    mock_api.get("/api/v1/balance").mock(side_effect=httpx.ReadTimeout("slow"))
    with pytest.raises(APITimeoutError, match=r"timed out after 30\.0 s"):
        client(0).balance.retrieve()


def test_per_call_max_retries_overrides(mock_api, no_sleep) -> None:
    route = mock_api.get("/api/v1/balance").mock(return_value=api_error(500, "api_error", "internal_error"))
    with pytest.raises(APIServerError):
        client(3).balance.retrieve(options=RequestOptions(max_retries=0))
    assert route.call_count == 1


def test_money_out_calls_default_to_90s_and_an_explicit_timeout_wins(mock_api) -> None:
    assert c.MONEY_OUT_TIMEOUT_SECONDS == 90.0
    assert {"createTransfer", "createRefund"} == c.MONEY_OUT_OPERATIONS
    transfers = mock_api.post("/api/v1/transfers").mock(return_value=ok(TRANSFER, 201))
    refunds = mock_api.post("/api/v1/refunds").mock(return_value=ok({"id": "ref_1"}, 201))
    payments = mock_api.post("/api/v1/payments").mock(return_value=ok({"id": "pay_1"}, 201))

    def read_timeouts(route) -> list[float]:
        return [call.request.extensions["timeout"]["read"] for call in route.calls]

    defaults = client(0)
    defaults.transfers.create(**PAYOUT)
    defaults.transfers.create(**PAYOUT, options=RequestOptions(timeout=5.0))
    defaults.refunds.create(payment="pay_1", reason="r")
    defaults.payments.create(amount=1, reference="r")
    explicit = Pletopay(TEST_KEY, base_url=BASE, timeout=45.0)
    explicit.transfers.create(**PAYOUT)
    explicit.refunds.create(payment="pay_1", reason="r", options=RequestOptions(timeout=120.0))
    assert read_timeouts(transfers) == [90.0, 5.0, 45.0]
    assert read_timeouts(refunds) == [90.0, 120.0]
    assert read_timeouts(payments) == [30.0]
    assert defaults.timeout == 30.0 and explicit.timeout == 45.0


def test_waits_out_a_bank_that_takes_75s_without_a_second_request(mock_api, clock: FakeClock) -> None:
    api = SlowApi(clock, 75.0)
    mock_api.post("/api/v1/transfers").mock(side_effect=api)
    assert client(2).transfers.create(**PAYOUT).id == TRANSFER["id"]
    assert len(api.calls) == 1


def test_keeps_asking_with_the_same_key_after_a_timeout(mock_api, clock: FakeClock) -> None:
    from pletopay import Hooks

    retries: list[dict] = []
    api = SlowApi(clock, 60.0)
    mock_api.post("/api/v1/transfers").mock(side_effect=api)
    pletopay = Pletopay(TEST_KEY, base_url=BASE, timeout=30.0, max_retries=2, hooks=Hooks(on_retry=retries.append))
    transfer = pletopay.transfers.create(**PAYOUT)
    assert transfer.id == TRANSFER["id"]
    assert transfer.last_response.idempotent_replayed
    # One timeout, then a 409 every 2 s until the first attempt has finished: far more requests than
    # max_retries allows, all with the key of the first.
    assert len(api.calls) > 10 and len(api.keys) == 1
    assert transfer.last_response.idempotency_key in api.keys
    assert api.calls[2][0] - api.calls[1][0] == pytest.approx(2.0)
    assert 60.0 <= api.calls[-1][0] < 62.5
    assert [r["reason"] for r in retries] == ["APITimeoutError"] + ["status"] * (len(api.calls) - 2)
    assert clock.slept[1:] == [2.0] * (len(api.calls) - 2)


def test_gives_up_90s_after_the_call_started_with_the_key_on_the_error(mock_api, clock: FakeClock) -> None:
    api = SlowApi(clock, 200.0)
    mock_api.post("/api/v1/refunds").mock(side_effect=api)
    with pytest.raises(IdempotencyError) as info:
        Pletopay(TEST_KEY, base_url=BASE, timeout=30.0, max_retries=2).refunds.create(
            payment="pay_1", reason="r", idempotency_key="refund-R-1"
        )
    assert info.value.status_code == 409 and info.value.code == "idempotency_request_in_progress"
    assert info.value.idempotency_key == "refund-R-1"
    assert api.keys == {"refund-R-1"}
    assert clock.now - api.started == pytest.approx(IN_PROGRESS_WAIT)
    assert api.calls[-1][0] == pytest.approx(IN_PROGRESS_WAIT)


def test_honours_retry_after_on_the_in_progress_answer(mock_api, clock: FakeClock) -> None:
    api = SlowApi(clock, 60.0, in_progress_headers={"retry-after": "10"})
    mock_api.post("/api/v1/transfers").mock(side_effect=api)
    assert Pletopay(TEST_KEY, base_url=BASE, timeout=30.0, max_retries=1).transfers.create(**PAYOUT).id == "trf_1"
    assert len(api.calls) == 5
    assert clock.slept[1:] == [10.0, 10.0, 10.0]


def test_does_not_wait_when_retries_are_off(mock_api, clock: FakeClock) -> None:
    api = SlowApi(clock, 60.0)
    route = mock_api.post("/api/v1/transfers").mock(side_effect=api)
    with pytest.raises(APITimeoutError) as info:
        Pletopay(TEST_KEY, base_url=BASE, timeout=30.0, max_retries=0).transfers.create(**PAYOUT)
    assert len(api.calls) == 1 and info.value.idempotency_key in api.keys

    route.mock(return_value=api_error(409, "idempotency_error", "idempotency_request_in_progress"))
    with pytest.raises(IdempotencyError):
        client(0).transfers.create(**PAYOUT, idempotency_key="k")
    assert route.call_count == 2 and clock.slept == []


def test_errors_carry_the_idempotency_key_of_the_request(mock_api) -> None:
    payments = mock_api.post("/api/v1/payments").mock(
        return_value=api_error(400, "invalid_request", "parameter_missing", param="amount")
    )
    with pytest.raises(InvalidRequestError) as invalid:
        client(0).payments.create(amount=1, reference="r")
    assert invalid.value.idempotency_key == payments.calls[0].request.headers["idempotency-key"]
    assert len(invalid.value.idempotency_key or "") == 36

    mock_api.post("/api/v1/transfers").mock(side_effect=httpx.ConnectError("boom"))
    with pytest.raises(APIConnectionError) as refused:
        client(0).transfers.create(**PAYOUT, idempotency_key="payout-1")
    assert refused.value.idempotency_key == "payout-1"

    mock_api.post("/api/v1/refunds").mock(return_value=httpx.Response(200, text="<html>bad gateway</html>"))
    with pytest.raises(APIError) as garbled:
        client(0).refunds.create(payment="pay_1", reason="r", idempotency_key="refund-1")
    assert garbled.value.idempotency_key == "refund-1"

    mock_api.get("/api/v1/payments/pay_x").mock(return_value=api_error(404, "not_found", "resource_missing"))
    with pytest.raises(APIError) as missing:
        client(0).payments.retrieve("pay_x")
    assert missing.value.idempotency_key is None
