from __future__ import annotations

from typing import Literal

from pletopay import _operations as ops
from pletopay._client import RequestOptions
from pletopay._pagination import AsyncPage, SyncPage
from pletopay.resources._base import AsyncAPIResource, SyncAPIResource, body, query
from pletopay.types import AccountResolution, Bank, Beneficiary, DateRange, Metadata, Transfer

TransferStatus = Literal["pending", "processing", "succeeded", "failed", "reversed"]


class Transfers(SyncAPIResource):
    """Transfers (payouts) from your available balance to any Nigerian bank account.

    A transfer stays ``processing`` until the outcome is known and is never reported ``failed`` prematurely.
    """

    def create(
        self,
        *,
        amount: int,
        reference: str,
        narration: str,
        beneficiary: Beneficiary,
        currency: Literal["NGN"] = "NGN",
        metadata: Metadata | None = None,
        idempotency_key: str | None = None,
        options: RequestOptions | None = None,
    ) -> Transfer:
        """Sends money. The API requires an ``Idempotency-Key``: pass a deterministic ``idempotency_key``
        (e.g. ``payout-<your id>``) so a retry from a crashed process cannot pay twice. The SDK generates a
        random one only when you omit it.

        The API answers once the bank has, so the default timeout is 90 s. A timeout or connection error does
        not mean the transfer failed: retry with the raised error's ``idempotency_key``.
        """
        return self._client._call(
            ops.CREATE_TRANSFER,
            Transfer,
            body=body(
                amount=amount,
                currency=currency,
                reference=reference,
                narration=narration,
                beneficiary=beneficiary,
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
        status: TransferStatus | None = None,
        options: RequestOptions | None = None,
    ) -> SyncPage[Transfer]:
        return self._client._list(
            ops.LIST_TRANSFERS,
            Transfer,
            query=query(
                limit=limit, starting_after=starting_after, ending_before=ending_before, created=created, status=status
            ),
            options=options,
        )

    def retrieve(self, id: str, *, options: RequestOptions | None = None) -> Transfer:
        return self._client._call(ops.GET_TRANSFER, Transfer, path_params={"id": id}, options=options)

    def retrieve_by_reference(self, reference: str, *, options: RequestOptions | None = None) -> Transfer:
        """Your payouts only; the transfers behind refunds and settlements are not returned."""
        return self._client._call(
            ops.GET_TRANSFER_BY_REFERENCE, Transfer, path_params={"reference": reference}, options=options
        )

    def resolve_account(
        self, *, bank_code: str, account_number: str, options: RequestOptions | None = None
    ) -> AccountResolution:
        """Name enquiry: shows the account holder's name before you send."""
        return self._client._call(
            ops.RESOLVE_ACCOUNT,
            AccountResolution,
            body=body(bank_code=bank_code, account_number=account_number),
            options=options,
        )


class AsyncTransfers(AsyncAPIResource):
    """Transfers (payouts) from your available balance to any Nigerian bank account."""

    async def create(
        self,
        *,
        amount: int,
        reference: str,
        narration: str,
        beneficiary: Beneficiary,
        currency: Literal["NGN"] = "NGN",
        metadata: Metadata | None = None,
        idempotency_key: str | None = None,
        options: RequestOptions | None = None,
    ) -> Transfer:
        return await self._client._call(
            ops.CREATE_TRANSFER,
            Transfer,
            body=body(
                amount=amount,
                currency=currency,
                reference=reference,
                narration=narration,
                beneficiary=beneficiary,
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
        status: TransferStatus | None = None,
        options: RequestOptions | None = None,
    ) -> AsyncPage[Transfer]:
        return await self._client._list(
            ops.LIST_TRANSFERS,
            Transfer,
            query=query(
                limit=limit, starting_after=starting_after, ending_before=ending_before, created=created, status=status
            ),
            options=options,
        )

    async def retrieve(self, id: str, *, options: RequestOptions | None = None) -> Transfer:
        return await self._client._call(ops.GET_TRANSFER, Transfer, path_params={"id": id}, options=options)

    async def retrieve_by_reference(self, reference: str, *, options: RequestOptions | None = None) -> Transfer:
        return await self._client._call(
            ops.GET_TRANSFER_BY_REFERENCE, Transfer, path_params={"reference": reference}, options=options
        )

    async def resolve_account(
        self, *, bank_code: str, account_number: str, options: RequestOptions | None = None
    ) -> AccountResolution:
        return await self._client._call(
            ops.RESOLVE_ACCOUNT,
            AccountResolution,
            body=body(bank_code=bank_code, account_number=account_number),
            options=options,
        )


class Banks(SyncAPIResource):
    """Banks and their codes, for transfer beneficiaries."""

    def list(self, *, options: RequestOptions | None = None) -> SyncPage[Bank]:
        """The full list (not paginated)."""
        return self._client._list(ops.LIST_BANKS, Bank, options=options)


class AsyncBanks(AsyncAPIResource):
    """Banks and their codes, for transfer beneficiaries."""

    async def list(self, *, options: RequestOptions | None = None) -> AsyncPage[Bank]:
        return await self._client._list(ops.LIST_BANKS, Bank, options=options)
