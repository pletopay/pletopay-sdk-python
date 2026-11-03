from __future__ import annotations

from datetime import datetime
from typing import Literal

from pletopay import _operations as ops
from pletopay._client import RequestOptions
from pletopay._pagination import AsyncPage, SyncPage
from pletopay.resources._base import AsyncAPIResource, SyncAPIResource, body, query
from pletopay.types import DateRange, Metadata, Subscription

SubscriptionStatus = Literal["active", "past_due", "canceled"]


class Subscriptions(SyncAPIResource):
    """Subscriptions: an invoice is issued each period (there is no automatic debit on bank transfer)."""

    def create(
        self,
        *,
        customer: str,
        plan: str,
        collection_method: Literal["invoice", "dedicated_account"],
        days_until_due: int | None = None,
        start_date: str | datetime | None = None,
        split: str | None = None,
        metadata: Metadata | None = None,
        idempotency_key: str | None = None,
        options: RequestOptions | None = None,
    ) -> Subscription:
        return self._client._call(
            ops.CREATE_SUBSCRIPTION,
            Subscription,
            body=body(
                customer=customer,
                plan=plan,
                collection_method=collection_method,
                days_until_due=days_until_due,
                start_date=start_date,
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
        status: SubscriptionStatus | None = None,
        customer: str | None = None,
        options: RequestOptions | None = None,
    ) -> SyncPage[Subscription]:
        return self._client._list(
            ops.LIST_SUBSCRIPTIONS,
            Subscription,
            query=query(
                limit=limit,
                starting_after=starting_after,
                ending_before=ending_before,
                created=created,
                status=status,
                customer=customer,
            ),
            options=options,
        )

    def retrieve(self, id: str, *, options: RequestOptions | None = None) -> Subscription:
        return self._client._call(ops.GET_SUBSCRIPTION, Subscription, path_params={"id": id}, options=options)

    def cancel(
        self,
        id: str,
        *,
        at_period_end: bool | None = None,
        reason: str | None = None,
        options: RequestOptions | None = None,
    ) -> Subscription:
        return self._client._call(
            ops.CANCEL_SUBSCRIPTION,
            Subscription,
            path_params={"id": id},
            body=body(at_period_end=at_period_end, reason=reason),
            options=options,
        )


class AsyncSubscriptions(AsyncAPIResource):
    """Subscriptions: an invoice is issued each period."""

    async def create(
        self,
        *,
        customer: str,
        plan: str,
        collection_method: Literal["invoice", "dedicated_account"],
        days_until_due: int | None = None,
        start_date: str | datetime | None = None,
        split: str | None = None,
        metadata: Metadata | None = None,
        idempotency_key: str | None = None,
        options: RequestOptions | None = None,
    ) -> Subscription:
        return await self._client._call(
            ops.CREATE_SUBSCRIPTION,
            Subscription,
            body=body(
                customer=customer,
                plan=plan,
                collection_method=collection_method,
                days_until_due=days_until_due,
                start_date=start_date,
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
        status: SubscriptionStatus | None = None,
        customer: str | None = None,
        options: RequestOptions | None = None,
    ) -> AsyncPage[Subscription]:
        return await self._client._list(
            ops.LIST_SUBSCRIPTIONS,
            Subscription,
            query=query(
                limit=limit,
                starting_after=starting_after,
                ending_before=ending_before,
                created=created,
                status=status,
                customer=customer,
            ),
            options=options,
        )

    async def retrieve(self, id: str, *, options: RequestOptions | None = None) -> Subscription:
        return await self._client._call(ops.GET_SUBSCRIPTION, Subscription, path_params={"id": id}, options=options)

    async def cancel(
        self,
        id: str,
        *,
        at_period_end: bool | None = None,
        reason: str | None = None,
        options: RequestOptions | None = None,
    ) -> Subscription:
        return await self._client._call(
            ops.CANCEL_SUBSCRIPTION,
            Subscription,
            path_params={"id": id},
            body=body(at_period_end=at_period_end, reason=reason),
            options=options,
        )
