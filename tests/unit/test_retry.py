from __future__ import annotations

import random

import httpx
import pytest

from pletopay import APIConnectionError, APIServerError, APITimeoutError, Pletopay, RateLimitError, RequestOptions
from pletopay._retry import is_retryable_status, retry_delay
from tests.conftest import BASE, TEST_KEY, api_error, ok


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
    assert retry_delay(0, rand=_Fixed(0.0), status_code=409, code="idempotency_request_in_progress") == 1.0


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
