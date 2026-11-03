from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from pletopay import ConflictError, IdempotencyError, InvalidRequestError, NotFoundError, Pletopay
from pletopay.types import Customer, Payment
from tests.live.conftest import poll, unique

state: dict[str, object] = {}


def test_create_customer(live: Pletopay) -> None:
    customer = live.customers.create(email=f"{unique('ada')}@example.com", name="Ada Okeke", metadata={"via": "sdk"})
    assert customer.object == "customer"
    assert customer.livemode is False
    assert customer.last_response is not None
    assert customer.last_response.request_id.startswith("req_")
    assert customer.last_response.api_version == "2026-09-25"
    assert customer.last_response.status_code == 201
    state["customer"] = customer


def test_create_payment_and_expand(live: Pletopay) -> None:
    customer = state["customer"]
    assert isinstance(customer, Customer)
    reference = unique("ORDER")
    payment = live.payments.create(
        amount=250000,
        reference=reference,
        customer={"id": customer.id},
        description="SDK live test",
        metadata={"reference": reference},
        idempotency_key=f"create-{reference}",
    )
    assert payment.status == "pending"
    assert payment.bank_transfer is not None and len(payment.bank_transfer.account_number) == 10
    assert payment.customer == customer.id
    expanded = live.payments.retrieve(payment.id, expand=["customer"])
    assert isinstance(expanded.customer, Customer) and expanded.customer.id == customer.id
    state["payment"] = payment


def test_idempotent_replay_and_reuse(live: Pletopay) -> None:
    reference = unique("IDEM")
    first = live.payments.create(amount=100000, reference=reference, idempotency_key=f"k-{reference}")
    second = live.payments.create(amount=100000, reference=reference, idempotency_key=f"k-{reference}")
    assert second.id == first.id
    assert first.last_response is not None and first.last_response.idempotent_replayed is False
    assert second.last_response is not None and second.last_response.idempotent_replayed is True
    with pytest.raises(IdempotencyError):
        live.payments.create(amount=100001, reference=reference, idempotency_key=f"k-{reference}")


def test_typed_errors(live: Pletopay) -> None:
    payment = state["payment"]
    assert isinstance(payment, Payment)
    with pytest.raises(ConflictError) as conflict:
        live.payments.create(amount=1, reference=payment.reference)
    assert conflict.value.code == "duplicate_reference"
    with pytest.raises(InvalidRequestError) as invalid:
        live.payments.create(amount=-5, reference=unique("X"))
    assert invalid.value.param == "amount"
    with pytest.raises(NotFoundError):
        live.payments.retrieve("pay_01J8Z5X7Q9K2M4N6P8R0S2T4V6")


def test_simulated_transfer_succeeds_payment(live: Pletopay) -> None:
    payment = state["payment"]
    assert isinstance(payment, Payment) and payment.bank_transfer is not None and payment.amount is not None
    live.sandbox.simulate_transfer(account_number=payment.bank_transfer.account_number, amount=payment.amount)
    paid = poll(lambda: live.payments.retrieve(payment.id), lambda p: p.status == "succeeded")
    assert paid.amount_received == payment.amount
    assert live.payments.retrieve_by_reference(payment.reference).id == payment.id
    state["payment"] = paid


def test_list_filters_and_pagination(live: Pletopay) -> None:
    customer = state["customer"]
    payment = state["payment"]
    assert isinstance(customer, Customer) and isinstance(payment, Payment)
    page = live.payments.list(
        limit=1, customer=customer.id, created={"gte": datetime.now(timezone.utc) - timedelta(hours=1)}
    )
    assert len(page) == 1 and not page.has_more
    ids = [p.id for p in live.payments.list(limit=1).auto_paging_iter()]
    assert len(ids) >= 2 and len(set(ids)) == len(ids)
    succeeded = live.payments.list(status="succeeded", amount={"gte": payment.amount or 0}, limit=100)
    assert payment.id in [p.id for p in succeeded]


def test_metadata_merge_balance_and_transactions(live: Pletopay) -> None:
    customer = state["customer"]
    assert isinstance(customer, Customer)
    updated = live.customers.update(customer.id, metadata={"tier": "gold", "via": ""})
    assert updated.metadata == {"tier": "gold"}
    balance = live.balance.retrieve()
    assert balance.object == "balance" and balance.currency == "NGN"
    tx = live.transactions.list(limit=5, source="payment")
    assert len(tx) > 0


def test_refund(live: Pletopay) -> None:
    payment = state["payment"]
    assert isinstance(payment, Payment)
    reference = unique("REF")
    refund = live.refunds.create(
        payment=payment.id,
        amount=50000,
        reason="SDK live test refund",
        reference=reference,
        idempotency_key=f"refund-{reference}",
    )
    assert refund.payment == payment.id
    assert refund.status in ("pending", "processing", "succeeded")
    assert live.refunds.retrieve_by_reference(reference).id == refund.id
    assert refund.id in [r.id for r in live.refunds.list(payment=payment.id)]
