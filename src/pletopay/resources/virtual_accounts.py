from __future__ import annotations

from datetime import datetime
from typing import Literal

from pletopay import _operations as ops
from pletopay._client import RequestOptions
from pletopay._pagination import AsyncPage, SyncPage
from pletopay.resources._base import AsyncAPIResource, SyncAPIResource, body, query
from pletopay.types import DateRange, Metadata, VirtualAccount

VirtualAccountStatus = Literal["requested", "active", "blocked", "expired", "consumed", "closed", "failed"]


class VirtualAccounts(SyncAPIResource):
    """Virtual accounts: ``dedicated`` (one per customer, every transfer in creates a succeeded payment) or ``dynamic`` (one payment, expires)."""

    def create(
        self,
        *,
        type: Literal["dedicated", "dynamic"],
        customer_id: str | None = None,
        amount: int | None = None,
        currency: Literal["NGN"] | None = None,
        reference: str | None = None,
        expires_at: str | datetime | None = None,
        metadata: Metadata | None = None,
        idempotency_key: str | None = None,
        options: RequestOptions | None = None,
    ) -> VirtualAccount:
        return self._client._call(
            ops.CREATE_VIRTUAL_ACCOUNT,
            VirtualAccount,
            body=body(
                type=type,
                customer_id=customer_id,
                amount=amount,
                currency=currency,
                reference=reference,
                expires_at=expires_at,
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
        type: Literal["dedicated", "dynamic"] | None = None,
        customer: str | None = None,
        status: VirtualAccountStatus | None = None,
        account_number: str | None = None,
        options: RequestOptions | None = None,
    ) -> SyncPage[VirtualAccount]:
        return self._client._list(
            ops.LIST_VIRTUAL_ACCOUNTS,
            VirtualAccount,
            query=query(
                limit=limit,
                starting_after=starting_after,
                ending_before=ending_before,
                created=created,
                type=type,
                customer=customer,
                status=status,
                account_number=account_number,
            ),
            options=options,
        )

    def retrieve(self, id: str, *, options: RequestOptions | None = None) -> VirtualAccount:
        return self._client._call(ops.GET_VIRTUAL_ACCOUNT, VirtualAccount, path_params={"id": id}, options=options)

    def retrieve_by_reference(self, reference: str, *, options: RequestOptions | None = None) -> VirtualAccount:
        """Dynamic accounts only: their reference is their payment's."""
        return self._client._call(
            ops.GET_VIRTUAL_ACCOUNT_BY_REFERENCE, VirtualAccount, path_params={"reference": reference}, options=options
        )

    def close(
        self, id: str, *, reason: str, idempotency_key: str | None = None, options: RequestOptions | None = None
    ) -> VirtualAccount:
        """Closes an account; money sent to it afterwards is not credited."""
        return self._client._call(
            ops.CLOSE_VIRTUAL_ACCOUNT,
            VirtualAccount,
            path_params={"id": id},
            body=body(reason=reason),
            idempotency_key=idempotency_key,
            options=options,
        )


class AsyncVirtualAccounts(AsyncAPIResource):
    """Virtual accounts: ``dedicated`` or ``dynamic``."""

    async def create(
        self,
        *,
        type: Literal["dedicated", "dynamic"],
        customer_id: str | None = None,
        amount: int | None = None,
        currency: Literal["NGN"] | None = None,
        reference: str | None = None,
        expires_at: str | datetime | None = None,
        metadata: Metadata | None = None,
        idempotency_key: str | None = None,
        options: RequestOptions | None = None,
    ) -> VirtualAccount:
        return await self._client._call(
            ops.CREATE_VIRTUAL_ACCOUNT,
            VirtualAccount,
            body=body(
                type=type,
                customer_id=customer_id,
                amount=amount,
                currency=currency,
                reference=reference,
                expires_at=expires_at,
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
        type: Literal["dedicated", "dynamic"] | None = None,
        customer: str | None = None,
        status: VirtualAccountStatus | None = None,
        account_number: str | None = None,
        options: RequestOptions | None = None,
    ) -> AsyncPage[VirtualAccount]:
        return await self._client._list(
            ops.LIST_VIRTUAL_ACCOUNTS,
            VirtualAccount,
            query=query(
                limit=limit,
                starting_after=starting_after,
                ending_before=ending_before,
                created=created,
                type=type,
                customer=customer,
                status=status,
                account_number=account_number,
            ),
            options=options,
        )

    async def retrieve(self, id: str, *, options: RequestOptions | None = None) -> VirtualAccount:
        return await self._client._call(
            ops.GET_VIRTUAL_ACCOUNT, VirtualAccount, path_params={"id": id}, options=options
        )

    async def retrieve_by_reference(self, reference: str, *, options: RequestOptions | None = None) -> VirtualAccount:
        return await self._client._call(
            ops.GET_VIRTUAL_ACCOUNT_BY_REFERENCE, VirtualAccount, path_params={"reference": reference}, options=options
        )

    async def close(
        self, id: str, *, reason: str, idempotency_key: str | None = None, options: RequestOptions | None = None
    ) -> VirtualAccount:
        return await self._client._call(
            ops.CLOSE_VIRTUAL_ACCOUNT,
            VirtualAccount,
            path_params={"id": id},
            body=body(reason=reason),
            idempotency_key=idempotency_key,
            options=options,
        )
