from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Literal

from pletopay import _operations as ops
from pletopay._client import RequestOptions
from pletopay._pagination import AsyncPage, SyncPage
from pletopay.resources._base import AsyncAPIResource, SyncAPIResource, body, query
from pletopay.types import DateRange, Invoice, InvoiceItemParams, InvoiceTaxParams, Metadata

InvoiceStatus = Literal["draft", "open", "paid", "void", "uncollectible"]


class Invoices(SyncAPIResource):
    """Invoices: draft → finalize (gets a hosted page and account details) → paid / void / uncollectible."""

    def create(
        self,
        *,
        customer: str,
        items: Sequence[InvoiceItemParams],
        due_date: str | datetime,
        taxes: Sequence[InvoiceTaxParams] | None = None,
        memo: str | None = None,
        split: str | None = None,
        metadata: Metadata | None = None,
        idempotency_key: str | None = None,
        options: RequestOptions | None = None,
    ) -> Invoice:
        return self._client._call(
            ops.CREATE_INVOICE,
            Invoice,
            body=body(
                customer=customer,
                items=list(items),
                taxes=list(taxes) if taxes is not None else None,
                due_date=due_date,
                memo=memo,
                split=split,
                metadata=metadata,
            ),
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
        status: InvoiceStatus | None = None,
        customer: str | None = None,
        subscription: str | None = None,
        options: RequestOptions | None = None,
    ) -> SyncPage[Invoice]:
        return self._client._list(
            ops.LIST_INVOICES,
            Invoice,
            query=query(
                limit=limit,
                starting_after=starting_after,
                ending_before=ending_before,
                created=created,
                status=status,
                customer=customer,
                subscription=subscription,
            ),
            options=options,
        )

    def retrieve(self, id: str, *, options: RequestOptions | None = None) -> Invoice:
        return self._client._call(ops.GET_INVOICE, Invoice, path_params={"id": id}, options=options)

    def update(
        self,
        id: str,
        *,
        customer: str | None = None,
        items: Sequence[InvoiceItemParams] | None = None,
        taxes: Sequence[InvoiceTaxParams] | None = None,
        due_date: str | datetime | None = None,
        memo: str | None = None,
        metadata: Metadata | None = None,
        options: RequestOptions | None = None,
    ) -> Invoice:
        """Drafts only (``409 invoice_not_draft``)."""
        return self._client._call(
            ops.UPDATE_INVOICE,
            Invoice,
            path_params={"id": id},
            body=body(
                customer=customer,
                items=list(items) if items is not None else None,
                taxes=list(taxes) if taxes is not None else None,
                due_date=due_date,
                memo=memo,
                metadata=metadata,
            ),
            options=options,
        )

    def finalize(self, id: str, *, options: RequestOptions | None = None) -> Invoice:
        return self._client._call(ops.FINALIZE_INVOICE, Invoice, path_params={"id": id}, options=options)

    def void(self, id: str, *, options: RequestOptions | None = None) -> Invoice:
        return self._client._call(ops.VOID_INVOICE, Invoice, path_params={"id": id}, options=options)

    def mark_uncollectible(self, id: str, *, options: RequestOptions | None = None) -> Invoice:
        return self._client._call(ops.MARK_INVOICE_UNCOLLECTIBLE, Invoice, path_params={"id": id}, options=options)


class AsyncInvoices(AsyncAPIResource):
    """Invoices: draft → finalize → paid / void / uncollectible."""

    async def create(
        self,
        *,
        customer: str,
        items: Sequence[InvoiceItemParams],
        due_date: str | datetime,
        taxes: Sequence[InvoiceTaxParams] | None = None,
        memo: str | None = None,
        split: str | None = None,
        metadata: Metadata | None = None,
        idempotency_key: str | None = None,
        options: RequestOptions | None = None,
    ) -> Invoice:
        return await self._client._call(
            ops.CREATE_INVOICE,
            Invoice,
            body=body(
                customer=customer,
                items=list(items),
                taxes=list(taxes) if taxes is not None else None,
                due_date=due_date,
                memo=memo,
                split=split,
                metadata=metadata,
            ),
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
        status: InvoiceStatus | None = None,
        customer: str | None = None,
        subscription: str | None = None,
        options: RequestOptions | None = None,
    ) -> AsyncPage[Invoice]:
        return await self._client._list(
            ops.LIST_INVOICES,
            Invoice,
            query=query(
                limit=limit,
                starting_after=starting_after,
                ending_before=ending_before,
                created=created,
                status=status,
                customer=customer,
                subscription=subscription,
            ),
            options=options,
        )

    async def retrieve(self, id: str, *, options: RequestOptions | None = None) -> Invoice:
        return await self._client._call(ops.GET_INVOICE, Invoice, path_params={"id": id}, options=options)

    async def update(
        self,
        id: str,
        *,
        customer: str | None = None,
        items: Sequence[InvoiceItemParams] | None = None,
        taxes: Sequence[InvoiceTaxParams] | None = None,
        due_date: str | datetime | None = None,
        memo: str | None = None,
        metadata: Metadata | None = None,
        options: RequestOptions | None = None,
    ) -> Invoice:
        return await self._client._call(
            ops.UPDATE_INVOICE,
            Invoice,
            path_params={"id": id},
            body=body(
                customer=customer,
                items=list(items) if items is not None else None,
                taxes=list(taxes) if taxes is not None else None,
                due_date=due_date,
                memo=memo,
                metadata=metadata,
            ),
            options=options,
        )

    async def finalize(self, id: str, *, options: RequestOptions | None = None) -> Invoice:
        return await self._client._call(ops.FINALIZE_INVOICE, Invoice, path_params={"id": id}, options=options)

    async def void(self, id: str, *, options: RequestOptions | None = None) -> Invoice:
        return await self._client._call(ops.VOID_INVOICE, Invoice, path_params={"id": id}, options=options)

    async def mark_uncollectible(self, id: str, *, options: RequestOptions | None = None) -> Invoice:
        return await self._client._call(
            ops.MARK_INVOICE_UNCOLLECTIBLE, Invoice, path_params={"id": id}, options=options
        )
