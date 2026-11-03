from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from pletopay.errors import RateLimitInfo


@dataclass(frozen=True)
class ListMeta:
    has_more: bool
    next_cursor: str | None
    url: str


@dataclass(frozen=True)
class ResponseInfo:
    """What the API said around ``data``: the envelope's message and the headers worth reading."""

    status_code: int
    headers: httpx.Headers
    message: str
    meta: ListMeta | None
    request_id: str | None
    api_version: str | None
    idempotency_key: str | None
    idempotent_replayed: bool
    rate_limit: RateLimitInfo | None
    deprecation: str | None
    sunset: str | None


@dataclass(frozen=True)
class RawResponse:
    """What :meth:`Pletopay.request` returns: the unwrapped ``data`` plus the response metadata."""

    data: Any
    response: ResponseInfo

    @property
    def message(self) -> str:
        return self.response.message

    @property
    def meta(self) -> ListMeta | None:
        return self.response.meta

    @property
    def request_id(self) -> str | None:
        return self.response.request_id
