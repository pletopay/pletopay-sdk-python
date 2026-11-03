from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from pletopay import _operations as ops
from pletopay._client import RequestOptions
from pletopay._pagination import AsyncPage, SyncPage
from pletopay.resources._base import AsyncAPIResource, SyncAPIResource, body, query
from pletopay.types import DateRange, Metadata, SplitAllocation, SplitRule


class SplitRules(SyncAPIResource):
    """Split rules: how a payment is shared between you and your subaccounts (``split="spl_…"`` on a payment)."""

    def create(
        self,
        *,
        name: str,
        type: Literal["percentage", "flat"],
        allocations: Sequence[SplitAllocation],
        metadata: Metadata | None = None,
        idempotency_key: str | None = None,
        options: RequestOptions | None = None,
    ) -> SplitRule:
        return self._client._call(
            ops.CREATE_SPLIT_RULE,
            SplitRule,
            body=body(name=name, type=type, allocations=list(allocations), metadata=metadata),
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
    ) -> SyncPage[SplitRule]:
        return self._client._list(
            ops.LIST_SPLIT_RULES,
            SplitRule,
            query=query(limit=limit, starting_after=starting_after, ending_before=ending_before, created=created),
            options=options,
        )

    def retrieve(self, id: str, *, options: RequestOptions | None = None) -> SplitRule:
        return self._client._call(ops.GET_SPLIT_RULE, SplitRule, path_params={"id": id}, options=options)

    def update(self, id: str, *, active: bool, options: RequestOptions | None = None) -> SplitRule:
        return self._client._call(
            ops.UPDATE_SPLIT_RULE, SplitRule, path_params={"id": id}, body=body(active=active), options=options
        )


class AsyncSplitRules(AsyncAPIResource):
    """Split rules: how a payment is shared between you and your subaccounts."""

    async def create(
        self,
        *,
        name: str,
        type: Literal["percentage", "flat"],
        allocations: Sequence[SplitAllocation],
        metadata: Metadata | None = None,
        idempotency_key: str | None = None,
        options: RequestOptions | None = None,
    ) -> SplitRule:
        return await self._client._call(
            ops.CREATE_SPLIT_RULE,
            SplitRule,
            body=body(name=name, type=type, allocations=list(allocations), metadata=metadata),
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
    ) -> AsyncPage[SplitRule]:
        return await self._client._list(
            ops.LIST_SPLIT_RULES,
            SplitRule,
            query=query(limit=limit, starting_after=starting_after, ending_before=ending_before, created=created),
            options=options,
        )

    async def retrieve(self, id: str, *, options: RequestOptions | None = None) -> SplitRule:
        return await self._client._call(ops.GET_SPLIT_RULE, SplitRule, path_params={"id": id}, options=options)

    async def update(self, id: str, *, active: bool, options: RequestOptions | None = None) -> SplitRule:
        return await self._client._call(
            ops.UPDATE_SPLIT_RULE, SplitRule, path_params={"id": id}, body=body(active=active), options=options
        )
