from __future__ import annotations

from typing import Literal

from pletopay import _operations as ops
from pletopay._client import RequestOptions
from pletopay._pagination import AsyncPage, SyncPage
from pletopay.resources._base import AsyncAPIResource, SyncAPIResource, body, query
from pletopay.types import DateRange, Metadata, Plan

Interval = Literal["day", "week", "month", "year"]


class Plans(SyncAPIResource):
    """Plans: what a subscription charges and how often."""

    def create(
        self,
        *,
        name: str,
        amount: int,
        interval: Interval,
        interval_count: int | None = None,
        description: str | None = None,
        metadata: Metadata | None = None,
        idempotency_key: str | None = None,
        options: RequestOptions | None = None,
    ) -> Plan:
        return self._client._call(
            ops.CREATE_PLAN,
            Plan,
            body=body(
                name=name,
                description=description,
                amount=amount,
                interval=interval,
                interval_count=interval_count,
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
        options: RequestOptions | None = None,
    ) -> SyncPage[Plan]:
        return self._client._list(
            ops.LIST_PLANS,
            Plan,
            query=query(limit=limit, starting_after=starting_after, ending_before=ending_before, created=created),
            options=options,
        )

    def retrieve(self, id: str, *, options: RequestOptions | None = None) -> Plan:
        return self._client._call(ops.GET_PLAN, Plan, path_params={"id": id}, options=options)

    def update(
        self,
        id: str,
        *,
        active: bool | None = None,
        name: str | None = None,
        description: str | None = None,
        options: RequestOptions | None = None,
    ) -> Plan:
        return self._client._call(
            ops.UPDATE_PLAN,
            Plan,
            path_params={"id": id},
            body=body(active=active, name=name, description=description),
            options=options,
        )


class AsyncPlans(AsyncAPIResource):
    """Plans: what a subscription charges and how often."""

    async def create(
        self,
        *,
        name: str,
        amount: int,
        interval: Interval,
        interval_count: int | None = None,
        description: str | None = None,
        metadata: Metadata | None = None,
        idempotency_key: str | None = None,
        options: RequestOptions | None = None,
    ) -> Plan:
        return await self._client._call(
            ops.CREATE_PLAN,
            Plan,
            body=body(
                name=name,
                description=description,
                amount=amount,
                interval=interval,
                interval_count=interval_count,
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
        options: RequestOptions | None = None,
    ) -> AsyncPage[Plan]:
        return await self._client._list(
            ops.LIST_PLANS,
            Plan,
            query=query(limit=limit, starting_after=starting_after, ending_before=ending_before, created=created),
            options=options,
        )

    async def retrieve(self, id: str, *, options: RequestOptions | None = None) -> Plan:
        return await self._client._call(ops.GET_PLAN, Plan, path_params={"id": id}, options=options)

    async def update(
        self,
        id: str,
        *,
        active: bool | None = None,
        name: str | None = None,
        description: str | None = None,
        options: RequestOptions | None = None,
    ) -> Plan:
        return await self._client._call(
            ops.UPDATE_PLAN,
            Plan,
            path_params={"id": id},
            body=body(active=active, name=name, description=description),
            options=options,
        )
