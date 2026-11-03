from __future__ import annotations

from typing import Literal

from pletopay import _operations as ops
from pletopay._client import RequestOptions
from pletopay._pagination import AsyncPage, SyncPage
from pletopay.resources._base import AsyncAPIResource, SyncAPIResource, query
from pletopay.types import DateRange, RiskEvent, RiskLimits


class Risk(SyncAPIResource):
    """Risk: flagged events and the limits that apply to your account."""

    def list_events(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        ending_before: str | None = None,
        created: DateRange | None = None,
        review_status: Literal["open", "cleared", "confirmed"] | None = None,
        options: RequestOptions | None = None,
    ) -> SyncPage[RiskEvent]:
        return self._client._list(
            ops.LIST_RISK_EVENTS,
            RiskEvent,
            query=query(
                limit=limit,
                starting_after=starting_after,
                ending_before=ending_before,
                created=created,
                review_status=review_status,
            ),
            options=options,
        )

    def retrieve_limits(self, *, options: RequestOptions | None = None) -> RiskLimits:
        return self._client._call(ops.GET_RISK_LIMITS, RiskLimits, options=options)


class AsyncRisk(AsyncAPIResource):
    """Risk: flagged events and the limits that apply to your account."""

    async def list_events(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        ending_before: str | None = None,
        created: DateRange | None = None,
        review_status: Literal["open", "cleared", "confirmed"] | None = None,
        options: RequestOptions | None = None,
    ) -> AsyncPage[RiskEvent]:
        return await self._client._list(
            ops.LIST_RISK_EVENTS,
            RiskEvent,
            query=query(
                limit=limit,
                starting_after=starting_after,
                ending_before=ending_before,
                created=created,
                review_status=review_status,
            ),
            options=options,
        )

    async def retrieve_limits(self, *, options: RequestOptions | None = None) -> RiskLimits:
        return await self._client._call(ops.GET_RISK_LIMITS, RiskLimits, options=options)
