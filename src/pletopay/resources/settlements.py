from __future__ import annotations

from typing import Literal

from pletopay import _operations as ops
from pletopay._client import RequestOptions
from pletopay._pagination import AsyncPage, SyncPage
from pletopay.resources._base import AsyncAPIResource, SyncAPIResource, query
from pletopay.types import DateRange, Settlement, SettlementItem

SettlementStatus = Literal["pending", "processing", "completed", "failed"]


class Settlements(SyncAPIResource):
    """Settlements: payouts of your available balance to your settlement account, on your schedule."""

    def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        ending_before: str | None = None,
        created: DateRange | None = None,
        status: SettlementStatus | None = None,
        subaccount: str | None = None,
        options: RequestOptions | None = None,
    ) -> SyncPage[Settlement]:
        return self._client._list(
            ops.LIST_SETTLEMENTS,
            Settlement,
            query=query(
                limit=limit,
                starting_after=starting_after,
                ending_before=ending_before,
                created=created,
                status=status,
                subaccount=subaccount,
            ),
            options=options,
        )

    def retrieve(self, id: str, *, options: RequestOptions | None = None) -> Settlement:
        return self._client._call(ops.GET_SETTLEMENT, Settlement, path_params={"id": id}, options=options)

    def list_items(self, id: str, *, options: RequestOptions | None = None) -> SyncPage[SettlementItem]:
        """The payments, refunds and fees that make up a settlement (not paginated)."""
        return self._client._list(ops.LIST_SETTLEMENT_ITEMS, SettlementItem, path_params={"id": id}, options=options)


class AsyncSettlements(AsyncAPIResource):
    """Settlements: payouts of your available balance to your settlement account."""

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        ending_before: str | None = None,
        created: DateRange | None = None,
        status: SettlementStatus | None = None,
        subaccount: str | None = None,
        options: RequestOptions | None = None,
    ) -> AsyncPage[Settlement]:
        return await self._client._list(
            ops.LIST_SETTLEMENTS,
            Settlement,
            query=query(
                limit=limit,
                starting_after=starting_after,
                ending_before=ending_before,
                created=created,
                status=status,
                subaccount=subaccount,
            ),
            options=options,
        )

    async def retrieve(self, id: str, *, options: RequestOptions | None = None) -> Settlement:
        return await self._client._call(ops.GET_SETTLEMENT, Settlement, path_params={"id": id}, options=options)

    async def list_items(self, id: str, *, options: RequestOptions | None = None) -> AsyncPage[SettlementItem]:
        return await self._client._list(
            ops.LIST_SETTLEMENT_ITEMS, SettlementItem, path_params={"id": id}, options=options
        )
