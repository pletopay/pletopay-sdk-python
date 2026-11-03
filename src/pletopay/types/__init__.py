"""Typed objects returned by the API and received in webhooks.

Everything here is generated from the OpenAPI contract (``python scripts/generate_models.py``).
Objects keep unknown fields (``model_extra``), so additive API changes never break parsing.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, TypeAlias, TypedDict

from pletopay.types._base import PletopayModel
from pletopay.types._events import EVENT_TYPES, SPEC_API_VERSION, EventType, KnownEvent
from pletopay.types._generated import (
    AccountResolution,
    Balance,
    Bank,
    BankTransferInstructions,
    CheckoutSession,
    Customer,
    DeletedObject,
    Error,
    EventCheckoutSessionCompleted,
    EventCheckoutSessionExpired,
    EventInvoiceCreated,
    EventInvoiceFinalized,
    EventInvoiceMarkedUncollectible,
    EventInvoicePaid,
    EventInvoiceVoided,
    EventPaymentCreated,
    EventPaymentExpired,
    EventPaymentFailed,
    EventPaymentPartiallyRefunded,
    EventPaymentPending,
    EventPaymentRefunded,
    EventPaymentReversed,
    EventPaymentSucceeded,
    EventPaymentUnderReview,
    EventRefundCreated,
    EventRefundFailed,
    EventRefundSucceeded,
    EventReportFailed,
    EventReportReady,
    EventRiskEventFlagged,
    EventSettlementCompleted,
    EventSettlementCreated,
    EventSettlementFailed,
    EventSubscriptionCanceled,
    EventSubscriptionCreated,
    EventSubscriptionPastDue,
    EventSubscriptionUpdated,
    EventTransferCreated,
    EventTransferFailed,
    EventTransferProcessing,
    EventTransferReversed,
    EventTransferSucceeded,
    EventVirtualAccountClosed,
    EventVirtualAccountCreated,
    EventVirtualAccountUpdated,
    EventWebhookTest,
    Invoice,
    InvoiceItem,
    InvoiceTax,
    LedgerTransaction,
    ListMeta,
    Payment,
    PaymentLink,
    Plan,
    Refund,
    Report,
    RiskEvent,
    RiskLimits,
    Settlement,
    SettlementItem,
    SimulatedTransfer,
    SplitRule,
    Statement,
    Subaccount,
    SubaccountBalance,
    Subscription,
    Transfer,
    VirtualAccount,
    WebhookDelivery,
    WebhookEndpoint,
    WebhookTest,
)
from pletopay.types._generated import (
    Event as StoredEvent,
)


class UnknownEventData(PletopayModel):
    object: dict[str, Any]


class UnknownEvent(PletopayModel):
    """An event whose ``type`` this SDK version does not know. Handle it as data, or ignore it."""

    id: str
    object: Literal["event"]
    type: str
    api_version: str
    livemode: bool
    created_at: datetime
    data: UnknownEventData


Event: TypeAlias = KnownEvent | UnknownEvent
"""Any webhook event: one of the typed event classes, or :class:`UnknownEvent` for new types."""


# ───────────── request shapes (keyword arguments of the resource methods) ─────────────


class DateRange(TypedDict, total=False):
    """``created={"gte": …}`` filters. Values are ISO-8601 strings or datetimes."""

    gt: str | datetime
    gte: str | datetime
    lt: str | datetime
    lte: str | datetime


class AmountRange(TypedDict, total=False):
    """``amount={"gte": …}`` filters, in kobo."""

    gte: int
    lte: int


class PaymentCustomer(TypedDict, total=False):
    """Who pays: an existing customer ``id``, or an ``email`` (creates or reuses the customer)."""

    id: str
    email: str
    name: str
    phone: str


class Beneficiary(TypedDict):
    bank_code: str
    account_number: str


class RefundDestination(TypedDict):
    bank_code: str
    account_number: str


class SplitAllocation(TypedDict):
    subaccount: str
    share: int


class InvoiceItemParams(TypedDict):
    description: str
    quantity: int
    unit_amount: int


class InvoiceTaxParams(TypedDict):
    name: str
    bps: int


Metadata: TypeAlias = "dict[str, str]"

__all__ = [
    "EVENT_TYPES",
    "SPEC_API_VERSION",
    "AccountResolution",
    "AmountRange",
    "Balance",
    "Bank",
    "BankTransferInstructions",
    "Beneficiary",
    "CheckoutSession",
    "Customer",
    "DateRange",
    "DeletedObject",
    "Error",
    "Event",
    "EventCheckoutSessionCompleted",
    "EventCheckoutSessionExpired",
    "EventInvoiceCreated",
    "EventInvoiceFinalized",
    "EventInvoiceMarkedUncollectible",
    "EventInvoicePaid",
    "EventInvoiceVoided",
    "EventPaymentCreated",
    "EventPaymentExpired",
    "EventPaymentFailed",
    "EventPaymentPartiallyRefunded",
    "EventPaymentPending",
    "EventPaymentRefunded",
    "EventPaymentReversed",
    "EventPaymentSucceeded",
    "EventPaymentUnderReview",
    "EventRefundCreated",
    "EventRefundFailed",
    "EventRefundSucceeded",
    "EventReportFailed",
    "EventReportReady",
    "EventRiskEventFlagged",
    "EventSettlementCompleted",
    "EventSettlementCreated",
    "EventSettlementFailed",
    "EventSubscriptionCanceled",
    "EventSubscriptionCreated",
    "EventSubscriptionPastDue",
    "EventSubscriptionUpdated",
    "EventTransferCreated",
    "EventTransferFailed",
    "EventTransferProcessing",
    "EventTransferReversed",
    "EventTransferSucceeded",
    "EventType",
    "EventVirtualAccountClosed",
    "EventVirtualAccountCreated",
    "EventVirtualAccountUpdated",
    "EventWebhookTest",
    "Invoice",
    "InvoiceItem",
    "InvoiceItemParams",
    "InvoiceTax",
    "InvoiceTaxParams",
    "KnownEvent",
    "LedgerTransaction",
    "ListMeta",
    "Metadata",
    "Payment",
    "PaymentCustomer",
    "PaymentLink",
    "Plan",
    "PletopayModel",
    "Refund",
    "RefundDestination",
    "Report",
    "RiskEvent",
    "RiskLimits",
    "Settlement",
    "SettlementItem",
    "SimulatedTransfer",
    "SplitAllocation",
    "SplitRule",
    "Statement",
    "StoredEvent",
    "Subaccount",
    "SubaccountBalance",
    "Subscription",
    "Transfer",
    "UnknownEvent",
    "VirtualAccount",
    "WebhookDelivery",
    "WebhookEndpoint",
    "WebhookTest",
]
