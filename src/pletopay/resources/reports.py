from __future__ import annotations

from datetime import datetime
from typing import Literal, cast

from pletopay import _operations as ops
from pletopay._client import RequestOptions
from pletopay._pagination import AsyncPage, SyncPage
from pletopay.resources._base import AsyncAPIResource, SyncAPIResource, body, query
from pletopay.types import DateRange, Report, Statement

ReportType = Literal[
    "payments", "transfers", "refunds", "settlements", "balance_statement", "customers", "invoices", "subscriptions"
]
ReportStatus = Literal["pending", "running", "succeeded", "failed"]


class Reports(SyncAPIResource):
    """Reports (CSV, generated asynchronously: wait for ``report.ready``) and the account statement."""

    def create(
        self,
        *,
        type: ReportType,
        period_start: str | datetime,
        period_end: str | datetime,
        options: RequestOptions | None = None,
    ) -> Report:
        return self._client._call(
            ops.CREATE_REPORT,
            Report,
            body=body(type=type, period_start=period_start, period_end=period_end),
            options=options,
        )

    def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        ending_before: str | None = None,
        created: DateRange | None = None,
        type: ReportType | None = None,
        status: ReportStatus | None = None,
        options: RequestOptions | None = None,
    ) -> SyncPage[Report]:
        return self._client._list(
            ops.LIST_REPORTS,
            Report,
            query=query(
                limit=limit,
                starting_after=starting_after,
                ending_before=ending_before,
                created=created,
                type=type,
                status=status,
            ),
            options=options,
        )

    def retrieve(self, id: str, *, options: RequestOptions | None = None) -> Report:
        return self._client._call(ops.GET_REPORT, Report, path_params={"id": id}, options=options)

    def download(self, id: str, *, options: RequestOptions | None = None) -> str:
        """The CSV of a ``succeeded`` report, as text (``409 report_not_ready`` before that)."""
        return cast(str, self._client._call_any(ops.DOWNLOAD_REPORT, path_params={"id": id}, options=options))

    def statement(
        self, *, period_start: str | datetime, period_end: str | datetime, options: RequestOptions | None = None
    ) -> Statement:
        """Opening balance, movements and closing balance for a period."""
        return self._client._call(
            ops.GET_STATEMENT, Statement, query=query(period_start=period_start, period_end=period_end), options=options
        )


class AsyncReports(AsyncAPIResource):
    """Reports and the account statement."""

    async def create(
        self,
        *,
        type: ReportType,
        period_start: str | datetime,
        period_end: str | datetime,
        options: RequestOptions | None = None,
    ) -> Report:
        return await self._client._call(
            ops.CREATE_REPORT,
            Report,
            body=body(type=type, period_start=period_start, period_end=period_end),
            options=options,
        )

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        ending_before: str | None = None,
        created: DateRange | None = None,
        type: ReportType | None = None,
        status: ReportStatus | None = None,
        options: RequestOptions | None = None,
    ) -> AsyncPage[Report]:
        return await self._client._list(
            ops.LIST_REPORTS,
            Report,
            query=query(
                limit=limit,
                starting_after=starting_after,
                ending_before=ending_before,
                created=created,
                type=type,
                status=status,
            ),
            options=options,
        )

    async def retrieve(self, id: str, *, options: RequestOptions | None = None) -> Report:
        return await self._client._call(ops.GET_REPORT, Report, path_params={"id": id}, options=options)

    async def download(self, id: str, *, options: RequestOptions | None = None) -> str:
        return cast(str, await self._client._call_any(ops.DOWNLOAD_REPORT, path_params={"id": id}, options=options))

    async def statement(
        self, *, period_start: str | datetime, period_end: str | datetime, options: RequestOptions | None = None
    ) -> Statement:
        return await self._client._call(
            ops.GET_STATEMENT, Statement, query=query(period_start=period_start, period_end=period_end), options=options
        )
