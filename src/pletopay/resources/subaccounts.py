from __future__ import annotations

from typing import Literal

from pletopay import _operations as ops
from pletopay._client import RequestOptions
from pletopay._pagination import AsyncPage, SyncPage
from pletopay.resources._base import AsyncAPIResource, SyncAPIResource, body, query
from pletopay.types import DateRange, Metadata, Subaccount, SubaccountBalance


class Subaccounts(SyncAPIResource):
    """Subaccounts: the parties that receive a share of split payments and are settled separately."""

    def create(
        self,
        *,
        name: str,
        bank_code: str,
        account_number: str,
        email: str | None = None,
        metadata: Metadata | None = None,
        idempotency_key: str | None = None,
        options: RequestOptions | None = None,
    ) -> Subaccount:
        return self._client._call(
            ops.CREATE_SUBACCOUNT,
            Subaccount,
            body=body(name=name, email=email, bank_code=bank_code, account_number=account_number, metadata=metadata),
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
    ) -> SyncPage[Subaccount]:
        return self._client._list(
            ops.LIST_SUBACCOUNTS,
            Subaccount,
            query=query(limit=limit, starting_after=starting_after, ending_before=ending_before, created=created),
            options=options,
        )

    def retrieve(self, id: str, *, options: RequestOptions | None = None) -> Subaccount:
        return self._client._call(ops.GET_SUBACCOUNT, Subaccount, path_params={"id": id}, options=options)

    def update(
        self,
        id: str,
        *,
        name: str | None = None,
        email: str | None = None,
        status: Literal["active", "inactive"] | None = None,
        bank_code: str | None = None,
        account_number: str | None = None,
        metadata: Metadata | None = None,
        options: RequestOptions | None = None,
    ) -> Subaccount:
        return self._client._call(
            ops.UPDATE_SUBACCOUNT,
            Subaccount,
            path_params={"id": id},
            body=body(
                name=name,
                email=email,
                status=status,
                bank_code=bank_code,
                account_number=account_number,
                metadata=metadata,
            ),
            options=options,
        )

    def retrieve_balance(self, id: str, *, options: RequestOptions | None = None) -> SubaccountBalance:
        return self._client._call(
            ops.GET_SUBACCOUNT_BALANCE, SubaccountBalance, path_params={"id": id}, options=options
        )


class AsyncSubaccounts(AsyncAPIResource):
    """Subaccounts: the parties that receive a share of split payments and are settled separately."""

    async def create(
        self,
        *,
        name: str,
        bank_code: str,
        account_number: str,
        email: str | None = None,
        metadata: Metadata | None = None,
        idempotency_key: str | None = None,
        options: RequestOptions | None = None,
    ) -> Subaccount:
        return await self._client._call(
            ops.CREATE_SUBACCOUNT,
            Subaccount,
            body=body(name=name, email=email, bank_code=bank_code, account_number=account_number, metadata=metadata),
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
    ) -> AsyncPage[Subaccount]:
        return await self._client._list(
            ops.LIST_SUBACCOUNTS,
            Subaccount,
            query=query(limit=limit, starting_after=starting_after, ending_before=ending_before, created=created),
            options=options,
        )

    async def retrieve(self, id: str, *, options: RequestOptions | None = None) -> Subaccount:
        return await self._client._call(ops.GET_SUBACCOUNT, Subaccount, path_params={"id": id}, options=options)

    async def update(
        self,
        id: str,
        *,
        name: str | None = None,
        email: str | None = None,
        status: Literal["active", "inactive"] | None = None,
        bank_code: str | None = None,
        account_number: str | None = None,
        metadata: Metadata | None = None,
        options: RequestOptions | None = None,
    ) -> Subaccount:
        return await self._client._call(
            ops.UPDATE_SUBACCOUNT,
            Subaccount,
            path_params={"id": id},
            body=body(
                name=name,
                email=email,
                status=status,
                bank_code=bank_code,
                account_number=account_number,
                metadata=metadata,
            ),
            options=options,
        )

    async def retrieve_balance(self, id: str, *, options: RequestOptions | None = None) -> SubaccountBalance:
        return await self._client._call(
            ops.GET_SUBACCOUNT_BALANCE, SubaccountBalance, path_params={"id": id}, options=options
        )
