"""Resource classes. ``bind_sync`` / ``bind_async`` attach one instance of each to a client."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pletopay.resources.balance import AsyncBalance, AsyncSandbox, AsyncTransactions, Balance, Sandbox, Transactions
from pletopay.resources.checkout import AsyncCheckout, AsyncCheckoutSessions, Checkout, CheckoutSessions
from pletopay.resources.customers import AsyncCustomers, Customers
from pletopay.resources.events import AsyncEvents, Events
from pletopay.resources.invoices import AsyncInvoices, Invoices
from pletopay.resources.payment_links import AsyncPaymentLinks, PaymentLinks
from pletopay.resources.payments import AsyncPayments, Payments
from pletopay.resources.plans import AsyncPlans, Plans
from pletopay.resources.refunds import AsyncRefunds, Refunds
from pletopay.resources.reports import AsyncReports, Reports
from pletopay.resources.risk import AsyncRisk, Risk
from pletopay.resources.settlements import AsyncSettlements, Settlements
from pletopay.resources.split_rules import AsyncSplitRules, SplitRules
from pletopay.resources.subaccounts import AsyncSubaccounts, Subaccounts
from pletopay.resources.subscriptions import AsyncSubscriptions, Subscriptions
from pletopay.resources.transfers import AsyncBanks, AsyncTransfers, Banks, Transfers
from pletopay.resources.virtual_accounts import AsyncVirtualAccounts, VirtualAccounts
from pletopay.resources.webhook_endpoints import AsyncWebhookEndpoints, WebhookEndpoints

if TYPE_CHECKING:
    from pletopay._client import AsyncPletopay, Pletopay


def bind_sync(client: Pletopay) -> None:
    client.customers = Customers(client)
    client.payments = Payments(client)
    client.virtual_accounts = VirtualAccounts(client)
    client.subaccounts = Subaccounts(client)
    client.split_rules = SplitRules(client)
    client.transfers = Transfers(client)
    client.banks = Banks(client)
    client.settlements = Settlements(client)
    client.refunds = Refunds(client)
    client.checkout = Checkout(client)
    client.payment_links = PaymentLinks(client)
    client.invoices = Invoices(client)
    client.risk = Risk(client)
    client.plans = Plans(client)
    client.subscriptions = Subscriptions(client)
    client.reports = Reports(client)
    client.webhook_endpoints = WebhookEndpoints(client)
    client.events = Events(client)
    client.balance = Balance(client)
    client.transactions = Transactions(client)
    client.sandbox = Sandbox(client)


def bind_async(client: AsyncPletopay) -> None:
    client.customers = AsyncCustomers(client)
    client.payments = AsyncPayments(client)
    client.virtual_accounts = AsyncVirtualAccounts(client)
    client.subaccounts = AsyncSubaccounts(client)
    client.split_rules = AsyncSplitRules(client)
    client.transfers = AsyncTransfers(client)
    client.banks = AsyncBanks(client)
    client.settlements = AsyncSettlements(client)
    client.refunds = AsyncRefunds(client)
    client.checkout = AsyncCheckout(client)
    client.payment_links = AsyncPaymentLinks(client)
    client.invoices = AsyncInvoices(client)
    client.risk = AsyncRisk(client)
    client.plans = AsyncPlans(client)
    client.subscriptions = AsyncSubscriptions(client)
    client.reports = AsyncReports(client)
    client.webhook_endpoints = AsyncWebhookEndpoints(client)
    client.events = AsyncEvents(client)
    client.balance = AsyncBalance(client)
    client.transactions = AsyncTransactions(client)
    client.sandbox = AsyncSandbox(client)


__all__ = [
    "AsyncBalance",
    "AsyncBanks",
    "AsyncCheckout",
    "AsyncCheckoutSessions",
    "AsyncCustomers",
    "AsyncEvents",
    "AsyncInvoices",
    "AsyncPaymentLinks",
    "AsyncPayments",
    "AsyncPlans",
    "AsyncRefunds",
    "AsyncReports",
    "AsyncRisk",
    "AsyncSandbox",
    "AsyncSettlements",
    "AsyncSplitRules",
    "AsyncSubaccounts",
    "AsyncSubscriptions",
    "AsyncTransactions",
    "AsyncTransfers",
    "AsyncVirtualAccounts",
    "AsyncWebhookEndpoints",
    "Balance",
    "Banks",
    "Checkout",
    "CheckoutSessions",
    "Customers",
    "Events",
    "Invoices",
    "PaymentLinks",
    "Payments",
    "Plans",
    "Refunds",
    "Reports",
    "Risk",
    "Sandbox",
    "Settlements",
    "SplitRules",
    "Subaccounts",
    "Subscriptions",
    "Transactions",
    "Transfers",
    "VirtualAccounts",
    "WebhookEndpoints",
    "bind_async",
    "bind_sync",
]
