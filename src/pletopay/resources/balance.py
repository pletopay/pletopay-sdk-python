from __future__ import annotations

from typing import Literal

from pletopay import _operations as ops
from pletopay._client import RequestOptions
from pletopay._pagination import AsyncPage, SyncPage
from pletopay.resources._base import AsyncAPIResource, SyncAPIResource, body, query
from pletopay.types import Balance as BalanceObject
from pletopay.types import DateRange, LedgerTransaction, SimulatedTransfer

TransactionSource = Literal["payment", "transfer", "account_transaction", "adjustment"]


class Balance(SyncAPIResource):
    """Your balance: ``available`` (can be paid out), ``pending``, ``held``, ``settling``, … in kobo."""

    def retrieve(self, *, options: RequestOptions | None = None) -> BalanceObject:
        return self._client._call(ops.GET_BALANCE, BalanceObject, options=options)


class AsyncBalance(AsyncAPIResource):
    """Your balance in kobo."""

    async def retrieve(self, *, options: RequestOptions | None = None) -> BalanceObject:
        return await self._client._call(ops.GET_BALANCE, BalanceObject, options=options)


class Transactions(SyncAPIResource):
    """The ledger: every movement on your balance, newest first."""

    def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        ending_before: str | None = None,
        created: DateRange | None = None,
        type: str | None = None,
        source: TransactionSource | None = None,
        options: RequestOptions | None = None,
    ) -> SyncPage[LedgerTransaction]:
        return self._client._list(
            ops.LIST_TRANSACTIONS,
            LedgerTransaction,
            query=query(
                limit=limit,
                starting_after=starting_after,
                ending_before=ending_before,
                created=created,
                type=type,
                source=source,
            ),
            options=options,
        )


class AsyncTransactions(AsyncAPIResource):
    """The ledger: every movement on your balance, newest first."""

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        ending_before: str | None = None,
        created: DateRange | None = None,
        type: str | None = None,
        source: TransactionSource | None = None,
        options: RequestOptions | None = None,
    ) -> AsyncPage[LedgerTransaction]:
        return await self._client._list(
            ops.LIST_TRANSACTIONS,
            LedgerTransaction,
            query=query(
                limit=limit,
                starting_after=starting_after,
                ending_before=ending_before,
                created=created,
                type=type,
                source=source,
            ),
            options=options,
        )


class Sandbox(SyncAPIResource):
    """Test-mode helpers. The SDK refuses these locally with a live key."""

    def simulate_transfer(
        self, *, account_number: str, amount: int, options: RequestOptions | None = None
    ) -> SimulatedTransfer:
        """Simulates an incoming bank transfer to a virtual account, so the payment succeeds without real money."""
        return self._client._call(
            ops.SIMULATE_TRANSFER,
            SimulatedTransfer,
            body=body(account_number=account_number, amount=amount),
            options=options,
        )


class AsyncSandbox(AsyncAPIResource):
    """Test-mode helpers."""

    async def simulate_transfer(
        self, *, account_number: str, amount: int, options: RequestOptions | None = None
    ) -> SimulatedTransfer:
        return await self._client._call(
            ops.SIMULATE_TRANSFER,
            SimulatedTransfer,
            body=body(account_number=account_number, amount=amount),
            options=options,
        )
