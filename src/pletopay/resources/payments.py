from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Literal

from pletopay import _operations as ops
from pletopay._client import RequestOptions
from pletopay._pagination import AsyncPage, SyncPage
from pletopay.resources._base import AsyncAPIResource, SyncAPIResource, body, query
from pletopay.types import AmountRange, DateRange, Metadata, Payment, PaymentCustomer

PaymentStatus = Literal[
    "created",
    "pending",
    "processing",
    "succeeded",
    "under_review",
    "failed",
    "expired",
    "reversed",
    "partially_refunded",
    "refunded",
]
Expand = Sequence[Literal["customer"]]


class Payments(SyncAPIResource):
    """Payments: the customer sends a bank transfer to the account in ``bank_transfer``.

    A payment is paid only when ``status`` is ``succeeded``: verify with :meth:`retrieve` or the
    ``payment.succeeded`` webhook, never from a client-side callback.
    """

    def create(
        self,
        *,
        reference: str,
        amount: int | None = None,
        currency: Literal["NGN"] = "NGN",
        amount_rule: Literal["exact", "any"] | None = None,
        customer: PaymentCustomer | None = None,
        description: str | None = None,
        metadata: Metadata | None = None,
        split: str | None = None,
        expires_in: int | None = None,
        expires_at: str | datetime | None = None,
        expand: Expand | None = None,
        idempotency_key: str | None = None,
        options: RequestOptions | None = None,
    ) -> Payment:
        """Creates a payment with transfer instructions. ``reference`` is your unique id (``409 duplicate_reference`` on reuse)."""
        return self._client._call(
            ops.CREATE_PAYMENT,
            Payment,
            body=body(
                amount=amount,
                currency=currency,
                reference=reference,
                amount_rule=amount_rule,
                customer=customer,
                description=description,
                metadata=metadata,
                split=split,
                expires_in=expires_in,
                expires_at=expires_at,
            ),
            query=query(expand=expand),
            idempotency_key=idempotency_key,
            options=options,
        )

    def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        ending_before: str | None = None,
        created: DateRange | None = None,
        status: PaymentStatus | None = None,
        customer: str | None = None,
        reference: str | None = None,
        q: str | None = None,
        amount: AmountRange | None = None,
        virtual_account: str | None = None,
        expand: Expand | None = None,
        options: RequestOptions | None = None,
    ) -> SyncPage[Payment]:
        return self._client._list(
            ops.LIST_PAYMENTS,
            Payment,
            query=query(
                limit=limit,
                starting_after=starting_after,
                ending_before=ending_before,
                created=created,
                status=status,
                customer=customer,
                reference=reference,
                q=q,
                amount=amount,
                virtual_account=virtual_account,
                expand=expand,
            ),
            options=options,
        )

    def retrieve(self, id: str, *, expand: Expand | None = None, options: RequestOptions | None = None) -> Payment:
        return self._client._call(
            ops.GET_PAYMENT, Payment, path_params={"id": id}, query=query(expand=expand), options=options
        )

    def retrieve_by_reference(
        self, reference: str, *, expand: Expand | None = None, options: RequestOptions | None = None
    ) -> Payment:
        """Looks a payment up by your ``reference``, e.g. after a timeout when you never got its id."""
        return self._client._call(
            ops.GET_PAYMENT_BY_REFERENCE,
            Payment,
            path_params={"reference": reference},
            query=query(expand=expand),
            options=options,
        )


class AsyncPayments(AsyncAPIResource):
    """Payments: the customer sends a bank transfer to the account in ``bank_transfer``."""

    async def create(
        self,
        *,
        reference: str,
        amount: int | None = None,
        currency: Literal["NGN"] = "NGN",
        amount_rule: Literal["exact", "any"] | None = None,
        customer: PaymentCustomer | None = None,
        description: str | None = None,
        metadata: Metadata | None = None,
        split: str | None = None,
        expires_in: int | None = None,
        expires_at: str | datetime | None = None,
        expand: Expand | None = None,
        idempotency_key: str | None = None,
        options: RequestOptions | None = None,
    ) -> Payment:
        return await self._client._call(
            ops.CREATE_PAYMENT,
            Payment,
            body=body(
                amount=amount,
                currency=currency,
                reference=reference,
                amount_rule=amount_rule,
                customer=customer,
                description=description,
                metadata=metadata,
                split=split,
                expires_in=expires_in,
                expires_at=expires_at,
            ),
            query=query(expand=expand),
            idempotency_key=idempotency_key,
            options=options,
        )

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        ending_before: str | None = None,
        created: DateRange | None = None,
        status: PaymentStatus | None = None,
        customer: str | None = None,
        reference: str | None = None,
        q: str | None = None,
        amount: AmountRange | None = None,
        virtual_account: str | None = None,
        expand: Expand | None = None,
        options: RequestOptions | None = None,
    ) -> AsyncPage[Payment]:
        return await self._client._list(
            ops.LIST_PAYMENTS,
            Payment,
            query=query(
                limit=limit,
                starting_after=starting_after,
                ending_before=ending_before,
                created=created,
                status=status,
                customer=customer,
                reference=reference,
                q=q,
                amount=amount,
                virtual_account=virtual_account,
                expand=expand,
            ),
            options=options,
        )

    async def retrieve(
        self, id: str, *, expand: Expand | None = None, options: RequestOptions | None = None
    ) -> Payment:
        return await self._client._call(
            ops.GET_PAYMENT, Payment, path_params={"id": id}, query=query(expand=expand), options=options
        )

    async def retrieve_by_reference(
        self, reference: str, *, expand: Expand | None = None, options: RequestOptions | None = None
    ) -> Payment:
        return await self._client._call(
            ops.GET_PAYMENT_BY_REFERENCE,
            Payment,
            path_params={"reference": reference},
            query=query(expand=expand),
            options=options,
        )
