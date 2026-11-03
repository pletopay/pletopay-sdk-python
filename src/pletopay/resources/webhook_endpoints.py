from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from pletopay import _operations as ops
from pletopay._client import RequestOptions
from pletopay._pagination import AsyncPage, SyncPage
from pletopay.resources._base import AsyncAPIResource, SyncAPIResource, body, query
from pletopay.types import DateRange, DeletedObject, WebhookDelivery, WebhookEndpoint

DeliveryStatus = Literal["pending", "succeeded", "failed", "dead"]


class WebhookEndpoints(SyncAPIResource):
    """Webhook endpoints: where Pletopay sends signed events. The ``secret`` is returned only by ``create`` and ``rotate_secret``."""

    def create(
        self,
        *,
        url: str,
        enabled_events: Sequence[str],
        description: str | None = None,
        idempotency_key: str | None = None,
        options: RequestOptions | None = None,
    ) -> WebhookEndpoint:
        """Registers an endpoint. Store ``secret`` (``whsec_…``) now: it is never shown again. ``enabled_events`` accepts ``"*"``."""
        return self._client._call(
            ops.CREATE_WEBHOOK_ENDPOINT,
            WebhookEndpoint,
            body=body(url=url, enabled_events=list(enabled_events), description=description),
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
    ) -> SyncPage[WebhookEndpoint]:
        return self._client._list(
            ops.LIST_WEBHOOK_ENDPOINTS,
            WebhookEndpoint,
            query=query(limit=limit, starting_after=starting_after, ending_before=ending_before, created=created),
            options=options,
        )

    def retrieve(self, id: str, *, options: RequestOptions | None = None) -> WebhookEndpoint:
        return self._client._call(ops.GET_WEBHOOK_ENDPOINT, WebhookEndpoint, path_params={"id": id}, options=options)

    def update(
        self,
        id: str,
        *,
        url: str | None = None,
        enabled_events: Sequence[str] | None = None,
        description: str | None = None,
        status: Literal["enabled", "disabled"] | None = None,
        options: RequestOptions | None = None,
    ) -> WebhookEndpoint:
        """Changes the URL, events or description, or re-enables an auto-disabled endpoint (``status="enabled"``)."""
        return self._client._call(
            ops.UPDATE_WEBHOOK_ENDPOINT,
            WebhookEndpoint,
            path_params={"id": id},
            body=body(
                url=url,
                enabled_events=list(enabled_events) if enabled_events is not None else None,
                description=description,
                status=status,
            ),
            options=options,
        )

    def delete(self, id: str, *, options: RequestOptions | None = None) -> DeletedObject:
        """Stops deliveries; history is kept."""
        return self._client._call(ops.DELETE_WEBHOOK_ENDPOINT, DeletedObject, path_params={"id": id}, options=options)

    def rotate_secret(self, id: str, *, options: RequestOptions | None = None) -> WebhookEndpoint:
        """Issues a new ``secret``; the old one keeps signing during the grace period."""
        return self._client._call(ops.ROTATE_WEBHOOK_SECRET, WebhookEndpoint, path_params={"id": id}, options=options)

    def test(self, id: str, *, options: RequestOptions | None = None) -> WebhookDelivery:
        """Sends a signed ``webhook.test`` event to this endpoint only."""
        return self._client._call(ops.TEST_WEBHOOK_ENDPOINT, WebhookDelivery, path_params={"id": id}, options=options)

    def list_deliveries(
        self,
        id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        ending_before: str | None = None,
        created: DateRange | None = None,
        status: DeliveryStatus | None = None,
        options: RequestOptions | None = None,
    ) -> SyncPage[WebhookDelivery]:
        return self._client._list(
            ops.LIST_ENDPOINT_DELIVERIES,
            WebhookDelivery,
            path_params={"id": id},
            query=query(
                limit=limit, starting_after=starting_after, ending_before=ending_before, created=created, status=status
            ),
            options=options,
        )


class AsyncWebhookEndpoints(AsyncAPIResource):
    """Webhook endpoints: where Pletopay sends signed events."""

    async def create(
        self,
        *,
        url: str,
        enabled_events: Sequence[str],
        description: str | None = None,
        idempotency_key: str | None = None,
        options: RequestOptions | None = None,
    ) -> WebhookEndpoint:
        return await self._client._call(
            ops.CREATE_WEBHOOK_ENDPOINT,
            WebhookEndpoint,
            body=body(url=url, enabled_events=list(enabled_events), description=description),
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
    ) -> AsyncPage[WebhookEndpoint]:
        return await self._client._list(
            ops.LIST_WEBHOOK_ENDPOINTS,
            WebhookEndpoint,
            query=query(limit=limit, starting_after=starting_after, ending_before=ending_before, created=created),
            options=options,
        )

    async def retrieve(self, id: str, *, options: RequestOptions | None = None) -> WebhookEndpoint:
        return await self._client._call(
            ops.GET_WEBHOOK_ENDPOINT, WebhookEndpoint, path_params={"id": id}, options=options
        )

    async def update(
        self,
        id: str,
        *,
        url: str | None = None,
        enabled_events: Sequence[str] | None = None,
        description: str | None = None,
        status: Literal["enabled", "disabled"] | None = None,
        options: RequestOptions | None = None,
    ) -> WebhookEndpoint:
        return await self._client._call(
            ops.UPDATE_WEBHOOK_ENDPOINT,
            WebhookEndpoint,
            path_params={"id": id},
            body=body(
                url=url,
                enabled_events=list(enabled_events) if enabled_events is not None else None,
                description=description,
                status=status,
            ),
            options=options,
        )

    async def delete(self, id: str, *, options: RequestOptions | None = None) -> DeletedObject:
        return await self._client._call(
            ops.DELETE_WEBHOOK_ENDPOINT, DeletedObject, path_params={"id": id}, options=options
        )

    async def rotate_secret(self, id: str, *, options: RequestOptions | None = None) -> WebhookEndpoint:
        return await self._client._call(
            ops.ROTATE_WEBHOOK_SECRET, WebhookEndpoint, path_params={"id": id}, options=options
        )

    async def test(self, id: str, *, options: RequestOptions | None = None) -> WebhookDelivery:
        return await self._client._call(
            ops.TEST_WEBHOOK_ENDPOINT, WebhookDelivery, path_params={"id": id}, options=options
        )

    async def list_deliveries(
        self,
        id: str,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
        ending_before: str | None = None,
        created: DateRange | None = None,
        status: DeliveryStatus | None = None,
        options: RequestOptions | None = None,
    ) -> AsyncPage[WebhookDelivery]:
        return await self._client._list(
            ops.LIST_ENDPOINT_DELIVERIES,
            WebhookDelivery,
            path_params={"id": id},
            query=query(
                limit=limit, starting_after=starting_after, ending_before=ending_before, created=created, status=status
            ),
            options=options,
        )
