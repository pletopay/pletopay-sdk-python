from __future__ import annotations

from pletopay import _operations as ops
from pletopay._client import RequestOptions
from pletopay._pagination import AsyncPage, SyncPage
from pletopay.resources._base import AsyncAPIResource, SyncAPIResource, body, query
from pletopay.types import DateRange, StoredEvent, WebhookDelivery


class Events(SyncAPIResource):
    """Events: everything that happened on your account, and their webhook deliveries."""

    def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        ending_before: str | None = None,
        created: DateRange | None = None,
        type: str | None = None,
        resource_id: str | None = None,
        options: RequestOptions | None = None,
    ) -> SyncPage[StoredEvent]:
        return self._client._list(
            ops.LIST_EVENTS,
            StoredEvent,
            query=query(
                limit=limit,
                starting_after=starting_after,
                ending_before=ending_before,
                created=created,
                type=type,
                resource_id=resource_id,
            ),
            options=options,
        )

    def retrieve(self, id: str, *, options: RequestOptions | None = None) -> StoredEvent:
        return self._client._call(ops.GET_EVENT, StoredEvent, path_params={"id": id}, options=options)

    def list_deliveries(self, id: str, *, options: RequestOptions | None = None) -> SyncPage[WebhookDelivery]:
        """Every delivery attempt group of this event (not paginated)."""
        return self._client._list(ops.LIST_EVENT_DELIVERIES, WebhookDelivery, path_params={"id": id}, options=options)

    def replay(
        self,
        id: str,
        *,
        endpoint: str | None = None,
        idempotency_key: str | None = None,
        options: RequestOptions | None = None,
    ) -> SyncPage[WebhookDelivery]:
        """Delivers the event again, to every subscribed endpoint or to one ``endpoint``. Rate limited."""
        return self._client._list(
            ops.REPLAY_EVENT,
            WebhookDelivery,
            path_params={"id": id},
            body=body(endpoint=endpoint),
            idempotency_key=idempotency_key,
            options=options,
        )


class AsyncEvents(AsyncAPIResource):
    """Events: everything that happened on your account, and their webhook deliveries."""

    async def list(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        ending_before: str | None = None,
        created: DateRange | None = None,
        type: str | None = None,
        resource_id: str | None = None,
        options: RequestOptions | None = None,
    ) -> AsyncPage[StoredEvent]:
        return await self._client._list(
            ops.LIST_EVENTS,
            StoredEvent,
            query=query(
                limit=limit,
                starting_after=starting_after,
                ending_before=ending_before,
                created=created,
                type=type,
                resource_id=resource_id,
            ),
            options=options,
        )

    async def retrieve(self, id: str, *, options: RequestOptions | None = None) -> StoredEvent:
        return await self._client._call(ops.GET_EVENT, StoredEvent, path_params={"id": id}, options=options)

    async def list_deliveries(self, id: str, *, options: RequestOptions | None = None) -> AsyncPage[WebhookDelivery]:
        return await self._client._list(
            ops.LIST_EVENT_DELIVERIES, WebhookDelivery, path_params={"id": id}, options=options
        )

    async def replay(
        self,
        id: str,
        *,
        endpoint: str | None = None,
        idempotency_key: str | None = None,
        options: RequestOptions | None = None,
    ) -> AsyncPage[WebhookDelivery]:
        return await self._client._list(
            ops.REPLAY_EVENT,
            WebhookDelivery,
            path_params={"id": id},
            body=body(endpoint=endpoint),
            idempotency_key=idempotency_key,
            options=options,
        )
