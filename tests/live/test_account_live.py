from __future__ import annotations

import warnings
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from pletopay import ConflictError, Pletopay
from tests.live.conftest import is_bank_unavailable, poll, unique

state: dict[str, Any] = {}


def test_checkout_session_lifecycle(live: Pletopay) -> None:
    reference = unique("CS")
    session = live.checkout.sessions.create(
        amount=150000,
        reference=reference,
        customer_email="ada@example.com",
        success_url="https://shop.example.com/ok",
        idempotency_key=f"cs-{reference}",
    )
    assert session.status == "open"
    assert session.url.startswith("http")
    assert session.token
    assert live.checkout.sessions.retrieve_by_reference(reference).id == session.id
    assert live.checkout.sessions.expire(session.id).status == "expired"
    with pytest.raises(ConflictError):
        live.checkout.sessions.expire(session.id)
    assert session.id in [s.id for s in live.checkout.sessions.list(status="expired", limit=100)]


def test_payment_links(live: Pletopay) -> None:
    link = live.payment_links.create(name="SDK donation", amount=20000)
    assert link.object == "payment_link"
    assert live.payment_links.update(link.id, active=False).active is False
    assert live.payment_links.retrieve(link.id).active is False


def test_invoice_lifecycle(live: Pletopay) -> None:
    customer = live.customers.create(email=f"{unique('inv')}@example.com", name="Invoice Customer")
    state["customer"] = customer
    invoice = live.invoices.create(
        customer=customer.id,
        due_date=datetime.now(timezone.utc) + timedelta(days=7),
        items=[{"description": "Consulting", "quantity": 2, "unit_amount": 100000}],
    )
    assert invoice.status == "draft"
    assert live.invoices.update(invoice.id, memo="updated").id == invoice.id
    assert live.invoices.finalize(invoice.id).status == "open"
    assert live.invoices.void(invoice.id).status == "void"
    assert invoice.id in [i.id for i in live.invoices.list(customer=customer.id)]


def test_plans_and_subscriptions(live: Pletopay) -> None:
    customer = state["customer"]
    plan = live.plans.create(name="SDK monthly", amount=500000, interval="month")
    assert plan.object == "plan"
    assert live.plans.update(plan.id, name="SDK monthly v2").name == "SDK monthly v2"
    subscription = live.subscriptions.create(customer=customer.id, plan=plan.id, collection_method="invoice")
    assert subscription.status == "active"
    assert live.subscriptions.cancel(subscription.id).status == "canceled"
    assert subscription.id in [s.id for s in live.subscriptions.list(customer=customer.id, status="canceled")]
    assert plan.id in [p.id for p in live.plans.list()]


def test_reports_statement_and_risk(live: Pletopay) -> None:
    report = live.reports.create(
        type="payments",
        period_start=datetime.now(timezone.utc) - timedelta(days=7),
        period_end=datetime.now(timezone.utc),
    )
    ready = poll(lambda: live.reports.retrieve(report.id), lambda r: r.status in ("succeeded", "failed"))
    assert ready.status == "succeeded"
    csv = live.reports.download(report.id)
    assert "id" in csv.splitlines()[0].lower()
    assert report.id in [r.id for r in live.reports.list(type="payments")]
    statement = live.reports.statement(
        period_start=datetime.now(timezone.utc) - timedelta(days=1), period_end=datetime.now(timezone.utc)
    )
    assert statement.object
    assert live.risk.retrieve_limits()
    assert isinstance(live.risk.list_events(limit=5).data, list)


def test_banks_and_name_enquiry(live: Pletopay) -> None:
    try:
        banks = live.banks.list()
        assert len(banks) > 0
        resolution = live.transfers.resolve_account(bank_code=banks[0].code, account_number="0123456789")
        assert resolution.account_name
    except Exception as error:
        if not is_bank_unavailable(error):
            raise
        warnings.warn("bank side unavailable, skipping name enquiry assertions", stacklevel=1)


def test_dedicated_virtual_account(live: Pletopay) -> None:
    customer = state["customer"]
    try:
        account = live.virtual_accounts.create(type="dedicated", customer_id=customer.id)
        assert account.status in ("requested", "active")
        active = poll(lambda: live.virtual_accounts.retrieve(account.id), lambda a: a.status != "requested")
        assert active.status == "active"
        assert account.id in [a.id for a in live.virtual_accounts.list(customer=customer.id, type="dedicated")]
        assert live.virtual_accounts.close(account.id, reason="SDK live test done").status == "closed"
    except Exception as error:
        if not is_bank_unavailable(error):
            raise
        warnings.warn("bank side unavailable, skipping virtual account assertions", stacklevel=1)


async def test_async_client_round_trip(live: Pletopay) -> None:
    from pletopay import AsyncPletopay

    async with AsyncPletopay(live._secret_key, base_url=live.base_url) as client:
        balance = await client.balance.retrieve()
        assert balance.currency == "NGN"
        ids = [c.id async for c in (await client.customers.list(limit=1)).auto_paging_iter()]
        assert len(ids) >= 1
