"""Query-string encoding for the API's filter syntax.

Nested dicts become bracket keys (``created[gte]=…``), lists repeat the key with ``[]``
(``expand[]=customer``), datetimes become UTC ISO-8601, booleans become ``true``/``false`` and
``None`` values are dropped. httpx percent-encodes keys and values.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Any

QueryParams = list[tuple[str, str]]


def _scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return str(value.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"))
    return str(value)


def encode_query(params: Mapping[str, Any] | None) -> QueryParams:
    out: QueryParams = []

    def add(key: str, value: Any) -> None:
        if value is None:
            return
        if isinstance(value, Mapping):
            for sub, item in value.items():
                add(f"{key}[{sub}]", item)
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            for item in value:
                add(f"{key}[]", item)
        else:
            out.append((key, _scalar(value)))

    for key, value in (params or {}).items():
        add(key, value)
    return out
