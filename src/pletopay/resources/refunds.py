from __future__ import annotations

from pletopay import _operations as ops
from pletopay._client import RequestOptions
from pletopay._pagination import AsyncPage, SyncPage
from pletopay.resources._base import AsyncAPIResource, SyncAPIResource, body, query
from pletopay.types import DateRange, Metadata, Refund, RefundDestination


class Refunds(SyncAPIResource):
    """Refunds: money back to the payer of a confirmed payment. The payment becomes ``partially_refunded`` / ``refunded`` once the refund succeeds."""

    def create(
        self,
        *,
        payment: str,
        reason: str,
        amount: int | None = None,
        reference: str | None = None,
        destination: RefundDestination | None = None,
        metadata: Metadata | None = None,
        idempotency_key: str | None = None,
        options: RequestOptions | None = None,
    ) -> Refund:
        """Refunds a payment (whole, or ``amount`` of it). The API requires an ``Idempotency-Key``: pass a
        deterministic ``idempotency_key`` (e.g. ``refund-<your id>``); the SDK generates a random one only when you omit it.

        The API answers once the bank has, so the default timeout is 90 s. A timeout or connection error does
        not mean the refund failed: retry with the raised error's ``idempotency_key``.
        """
        return self._client._call(
            ops.CREATE_REFUND,
            Refund,
            body=body(
                payment=payment,
                amount=amount,
                reason=reason,
                reference=reference,
                destination=destination,
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
        payment: str | None = None,
        options: RequestOptions | None = None,
    ) -> SyncPage[Refund]:
        return self._client._list(
            ops.LIST_REFUNDS,
            Refund,
            query=query(
                limit=limit,
                starting_after=starting_after,
                ending_before=ending_before,
                created=created,
                payment=payment,
            ),
            options=options,
        )

    def retrieve(self, id: str, *, options: RequestOptions | None = None) -> Refund:
        return self._client._call(ops.GET_REFUND, Refund, path_params={"id": id}, options=options)

    def retrieve_by_reference(self, reference: str, *, options: RequestOptions | None = None) -> Refund:
        return self._client._call(
            ops.GET_REFUND_BY_REFERENCE, Refund, path_params={"reference": reference}, options=options
        )


class AsyncRefunds(AsyncAPIResource):
    """Refunds: money back to the payer of a confirmed payment."""

    async def create(
        self,
        *,
        payment: str,
        reason: str,
        amount: int | None = None,
        reference: str | None = None,
        destination: RefundDestination | None = None,
        metadata: Metadata | None = None,
        idempotency_key: str | None = None,
        options: RequestOptions | None = None,
    ) -> Refund:
        return await self._client._call(
            ops.CREATE_REFUND,
            Refund,
            body=body(
                payment=payment,
                amount=amount,
                reason=reason,
                reference=reference,
                destination=destination,
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
        payment: str | None = None,
        options: RequestOptions | None = None,
    ) -> AsyncPage[Refund]:
        return await self._client._list(
            ops.LIST_REFUNDS,
            Refund,
            query=query(
                limit=limit,
                starting_after=starting_after,
                ending_before=ending_before,
                created=created,
                payment=payment,
            ),
            options=options,
        )

    async def retrieve(self, id: str, *, options: RequestOptions | None = None) -> Refund:
        return await self._client._call(ops.GET_REFUND, Refund, path_params={"id": id}, options=options)

    async def retrieve_by_reference(self, reference: str, *, options: RequestOptions | None = None) -> Refund:
        return await self._client._call(
            ops.GET_REFUND_BY_REFERENCE, Refund, path_params={"reference": reference}, options=options
        )
