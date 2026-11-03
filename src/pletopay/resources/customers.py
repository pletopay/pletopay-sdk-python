from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from pletopay import _operations as ops
from pletopay._client import RequestOptions
from pletopay._pagination import AsyncPage, SyncPage
from pletopay.resources._base import AsyncAPIResource, SyncAPIResource, body, query
from pletopay.types import Customer, DateRange, Metadata


class Customers(SyncAPIResource):
    """Customers: the people or businesses that pay you."""

    def create(
        self,
        *,
        email: str | None = None,
        name: str | None = None,
        phone: str | None = None,
        external_id: str | None = None,
        metadata: Metadata | None = None,
        idempotency_key: str | None = None,
        options: RequestOptions | None = None,
    ) -> Customer:
        """Creates a customer. ``email`` is unique per mode (``409 customer_exists``)."""
        return self._client._call(
            ops.CREATE_CUSTOMER,
            Customer,
            body=body(email=email, name=name, phone=phone, external_id=external_id, metadata=metadata),
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
        email: str | None = None,
        options: RequestOptions | None = None,
    ) -> SyncPage[Customer]:
        return self._client._list(
            ops.LIST_CUSTOMERS,
            Customer,
            query=query(
                limit=limit, starting_after=starting_after, ending_before=ending_before, created=created, email=email
            ),
            options=options,
        )

    def retrieve(self, id: str, *, options: RequestOptions | None = None) -> Customer:
        return self._client._call(ops.GET_CUSTOMER, Customer, path_params={"id": id}, options=options)

    def update(
        self,
        id: str,
        *,
        email: str | None = None,
        name: str | None = None,
        phone: str | None = None,
        metadata: Metadata | None = None,
        idempotency_key: str | None = None,
        options: RequestOptions | None = None,
    ) -> Customer:
        """Updates a customer. ``metadata`` merges; set a key to ``""`` to delete it."""
        return self._client._call(
            ops.UPDATE_CUSTOMER,
            Customer,
            path_params={"id": id},
            body=body(email=email, name=name, phone=phone, metadata=metadata),
            idempotency_key=idempotency_key,
            options=options,
        )

    def set_risk_status(
        self,
        id: str,
        *,
        status: Literal["normal", "elevated", "blocked"],
        reason: str | None = None,
        options: RequestOptions | None = None,
    ) -> Customer:
        """Blocks or unblocks a customer. Blocked customers cannot pay."""
        return self._client._call(
            ops.SET_CUSTOMER_RISK_STATUS,
            Customer,
            path_params={"id": id},
            body=body(status=status, reason=reason),
            options=options,
        )


class AsyncCustomers(AsyncAPIResource):
    """Customers: the people or businesses that pay you."""

    async def create(
        self,
        *,
        email: str | None = None,
        name: str | None = None,
        phone: str | None = None,
        external_id: str | None = None,
        metadata: Metadata | None = None,
        idempotency_key: str | None = None,
        options: RequestOptions | None = None,
    ) -> Customer:
        return await self._client._call(
            ops.CREATE_CUSTOMER,
            Customer,
            body=body(email=email, name=name, phone=phone, external_id=external_id, metadata=metadata),
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
        email: str | None = None,
        options: RequestOptions | None = None,
    ) -> AsyncPage[Customer]:
        return await self._client._list(
            ops.LIST_CUSTOMERS,
            Customer,
            query=query(
                limit=limit, starting_after=starting_after, ending_before=ending_before, created=created, email=email
            ),
            options=options,
        )

    async def retrieve(self, id: str, *, options: RequestOptions | None = None) -> Customer:
        return await self._client._call(ops.GET_CUSTOMER, Customer, path_params={"id": id}, options=options)

    async def update(
        self,
        id: str,
        *,
        email: str | None = None,
        name: str | None = None,
        phone: str | None = None,
        metadata: Metadata | None = None,
        idempotency_key: str | None = None,
        options: RequestOptions | None = None,
    ) -> Customer:
        return await self._client._call(
            ops.UPDATE_CUSTOMER,
            Customer,
            path_params={"id": id},
            body=body(email=email, name=name, phone=phone, metadata=metadata),
            idempotency_key=idempotency_key,
            options=options,
        )

    async def set_risk_status(
        self,
        id: str,
        *,
        status: Literal["normal", "elevated", "blocked"],
        reason: str | None = None,
        options: RequestOptions | None = None,
    ) -> Customer:
        return await self._client._call(
            ops.SET_CUSTOMER_RISK_STATUS,
            Customer,
            path_params={"id": id},
            body=body(status=status, reason=reason),
            options=options,
        )


__all__ = ["AsyncCustomers", "Customers", "Sequence"]
