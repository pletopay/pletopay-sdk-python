from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pletopay._client import AsyncPletopay, Pletopay


class SyncAPIResource:
    def __init__(self, client: Pletopay) -> None:
        self._client = client


class AsyncAPIResource:
    def __init__(self, client: AsyncPletopay) -> None:
        self._client = client


def body(**fields: Any) -> dict[str, Any]:
    """The request body: every keyword that is not ``None``."""
    return {k: v for k, v in fields.items() if v is not None}


def query(**fields: Any) -> dict[str, Any] | None:
    """Query parameters: every keyword that is not ``None``, or ``None`` when there are none."""
    out = {k: v for k, v in fields.items() if v is not None}
    return out or None
