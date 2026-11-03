from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pletopay import _operations as ops
from pletopay._client import RequestOptions
from pletopay._pagination import AsyncPage, SyncPage
from pletopay.resources._base import AsyncAPIResource, SyncAPIResource, body, query
from pletopay.types import CheckoutSession, DateRange, Metadata

if TYPE_CHECKING:
    from pletopay._client import AsyncPletopay, Pletopay

CheckoutSessionStatus = Literal["open", "complete", "expired"]


class CheckoutSessions(SyncAPIResource):
    """Checkout sessions: a hosted page (``url``) or the popup (``token`` with pletopay.js).

    Confirm fulfilment from ``status == "complete"`` on the server, never from the browser.
    """

    def create(
        self,
        *,
        amount: int,
        currency: Literal["NGN"] = "NGN",
        reference: str | None = None,
        description: str | None = None,
        customer: str | None = None,
        customer_email: str | None = None,
        success_url: str | None = None,
        cancel_url: str | None = None,
        expires_in: int | None = None,
        split: str | None = None,
        metadata: Metadata | None = None,
        idempotency_key: str | None = None,
        options: RequestOptions | None = None,
    ) -> CheckoutSession:
        return self._client._call(
            ops.CREATE_CHECKOUT_SESSION,
            CheckoutSession,
            body=body(
                amount=amount,
                currency=currency,
                reference=reference,
                description=description,
                customer=customer,
                customer_email=customer_email,
                success_url=success_url,
                cancel_url=cancel_url,
                expires_in=expires_in,
                split=split,
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
        status: CheckoutSessionStatus | None = None,
        payment_link: str | None = None,
        options: RequestOptions | None = None,
    ) -> SyncPage[CheckoutSession]:
        return self._client._list(
            ops.LIST_CHECKOUT_SESSIONS,
            CheckoutSession,
            query=query(
                limit=limit,
                starting_after=starting_after,
                ending_before=ending_before,
                created=created,
                status=status,
                payment_link=payment_link,
            ),
            options=options,
        )

    def retrieve(self, id: str, *, options: RequestOptions | None = None) -> CheckoutSession:
        return self._client._call(ops.GET_CHECKOUT_SESSION, CheckoutSession, path_params={"id": id}, options=options)

    def retrieve_by_reference(self, reference: str, *, options: RequestOptions | None = None) -> CheckoutSession:
        """Only sessions created with a ``reference``."""
        return self._client._call(
            ops.GET_CHECKOUT_SESSION_BY_REFERENCE,
            CheckoutSession,
            path_params={"reference": reference},
            options=options,
        )

    def expire(self, id: str, *, options: RequestOptions | None = None) -> CheckoutSession:
        """Expires an open session so it can no longer be paid."""
        return self._client._call(ops.EXPIRE_CHECKOUT_SESSION, CheckoutSession, path_params={"id": id}, options=options)


class AsyncCheckoutSessions(AsyncAPIResource):
    """Checkout sessions: a hosted page (``url``) or the popup (``token`` with pletopay.js)."""

    async def create(
        self,
        *,
        amount: int,
        currency: Literal["NGN"] = "NGN",
        reference: str | None = None,
        description: str | None = None,
        customer: str | None = None,
        customer_email: str | None = None,
        success_url: str | None = None,
        cancel_url: str | None = None,
        expires_in: int | None = None,
        split: str | None = None,
        metadata: Metadata | None = None,
        idempotency_key: str | None = None,
        options: RequestOptions | None = None,
    ) -> CheckoutSession:
        return await self._client._call(
            ops.CREATE_CHECKOUT_SESSION,
            CheckoutSession,
            body=body(
                amount=amount,
                currency=currency,
                reference=reference,
                description=description,
                customer=customer,
                customer_email=customer_email,
                success_url=success_url,
                cancel_url=cancel_url,
                expires_in=expires_in,
                split=split,
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
        status: CheckoutSessionStatus | None = None,
        payment_link: str | None = None,
        options: RequestOptions | None = None,
    ) -> AsyncPage[CheckoutSession]:
        return await self._client._list(
            ops.LIST_CHECKOUT_SESSIONS,
            CheckoutSession,
            query=query(
                limit=limit,
                starting_after=starting_after,
                ending_before=ending_before,
                created=created,
                status=status,
                payment_link=payment_link,
            ),
            options=options,
        )

    async def retrieve(self, id: str, *, options: RequestOptions | None = None) -> CheckoutSession:
        return await self._client._call(
            ops.GET_CHECKOUT_SESSION, CheckoutSession, path_params={"id": id}, options=options
        )

    async def retrieve_by_reference(self, reference: str, *, options: RequestOptions | None = None) -> CheckoutSession:
        return await self._client._call(
            ops.GET_CHECKOUT_SESSION_BY_REFERENCE,
            CheckoutSession,
            path_params={"reference": reference},
            options=options,
        )

    async def expire(self, id: str, *, options: RequestOptions | None = None) -> CheckoutSession:
        return await self._client._call(
            ops.EXPIRE_CHECKOUT_SESSION, CheckoutSession, path_params={"id": id}, options=options
        )


class Checkout(SyncAPIResource):
    def __init__(self, client: Pletopay) -> None:
        super().__init__(client)
        self.sessions = CheckoutSessions(client)


class AsyncCheckout(AsyncAPIResource):
    def __init__(self, client: AsyncPletopay) -> None:
        super().__init__(client)
        self.sessions = AsyncCheckoutSessions(client)
