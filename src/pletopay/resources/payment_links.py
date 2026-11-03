from __future__ import annotations

from datetime import datetime
from typing import Literal

from pletopay import _operations as ops
from pletopay._client import RequestOptions
from pletopay._pagination import AsyncPage, SyncPage
from pletopay.resources._base import AsyncAPIResource, SyncAPIResource, body, query
from pletopay.types import DateRange, Metadata, PaymentLink


class PaymentLinks(SyncAPIResource):
    """Payment links: reusable hosted pages you can share anywhere."""

    def create(
        self,
        *,
        name: str,
        description: str | None = None,
        amount: int | None = None,
        min_amount: int | None = None,
        max_amount: int | None = None,
        max_uses: int | None = None,
        success_url: str | None = None,
        cancel_url: str | None = None,
        split: str | None = None,
        expires_at: str | datetime | None = None,
        metadata: Metadata | None = None,
        idempotency_key: str | None = None,
        options: RequestOptions | None = None,
    ) -> PaymentLink:
        return self._client._call(
            ops.CREATE_PAYMENT_LINK,
            PaymentLink,
            body=body(
                name=name,
                description=description,
                amount=amount,
                min_amount=min_amount,
                max_amount=max_amount,
                max_uses=max_uses,
                success_url=success_url,
                cancel_url=cancel_url,
                split=split,
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
        status: Literal["active", "inactive"] | None = None,
        options: RequestOptions | None = None,
    ) -> SyncPage[PaymentLink]:
        return self._client._list(
            ops.LIST_PAYMENT_LINKS,
            PaymentLink,
            query=query(
                limit=limit, starting_after=starting_after, ending_before=ending_before, created=created, status=status
            ),
            options=options,
        )

    def retrieve(self, id: str, *, options: RequestOptions | None = None) -> PaymentLink:
        return self._client._call(ops.GET_PAYMENT_LINK, PaymentLink, path_params={"id": id}, options=options)

    def update(
        self,
        id: str,
        *,
        active: bool | None = None,
        name: str | None = None,
        description: str | None = None,
        options: RequestOptions | None = None,
    ) -> PaymentLink:
        return self._client._call(
            ops.UPDATE_PAYMENT_LINK,
            PaymentLink,
            path_params={"id": id},
            body=body(active=active, name=name, description=description),
            options=options,
        )


class AsyncPaymentLinks(AsyncAPIResource):
    """Payment links: reusable hosted pages you can share anywhere."""

    async def create(
        self,
        *,
        name: str,
        description: str | None = None,
        amount: int | None = None,
        min_amount: int | None = None,
        max_amount: int | None = None,
        max_uses: int | None = None,
        success_url: str | None = None,
        cancel_url: str | None = None,
        split: str | None = None,
        expires_at: str | datetime | None = None,
        metadata: Metadata | None = None,
        idempotency_key: str | None = None,
        options: RequestOptions | None = None,
    ) -> PaymentLink:
        return await self._client._call(
            ops.CREATE_PAYMENT_LINK,
            PaymentLink,
            body=body(
                name=name,
                description=description,
                amount=amount,
                min_amount=min_amount,
                max_amount=max_amount,
                max_uses=max_uses,
                success_url=success_url,
                cancel_url=cancel_url,
                split=split,
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
        status: Literal["active", "inactive"] | None = None,
        options: RequestOptions | None = None,
    ) -> AsyncPage[PaymentLink]:
        return await self._client._list(
            ops.LIST_PAYMENT_LINKS,
            PaymentLink,
            query=query(
                limit=limit, starting_after=starting_after, ending_before=ending_before, created=created, status=status
            ),
            options=options,
        )

    async def retrieve(self, id: str, *, options: RequestOptions | None = None) -> PaymentLink:
        return await self._client._call(ops.GET_PAYMENT_LINK, PaymentLink, path_params={"id": id}, options=options)

    async def update(
        self,
        id: str,
        *,
        active: bool | None = None,
        name: str | None = None,
        description: str | None = None,
        options: RequestOptions | None = None,
    ) -> PaymentLink:
        return await self._client._call(
            ops.UPDATE_PAYMENT_LINK,
            PaymentLink,
            path_params={"id": id},
            body=body(active=active, name=name, description=description),
            options=options,
        )
