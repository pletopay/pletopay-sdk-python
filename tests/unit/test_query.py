from __future__ import annotations

from datetime import datetime, timezone

from pletopay import encode_query


def test_empty() -> None:
    assert encode_query(None) == []
    assert encode_query({}) == []
    assert encode_query({"a": None}) == []


def test_scalars_dates_lists_and_nesting() -> None:
    q = encode_query(
        {
            "limit": 10,
            "ok": True,
            "q": "a b&c",
            "created": {"gte": datetime(2026, 1, 1, tzinfo=timezone.utc), "lt": "2026-02-01T00:00:00Z", "gt": None},
            "expand": ["customer", "x"],
            "deep": {"a": {"b": 1}},
            "naive": datetime(2026, 1, 1, 12, 0),
        }
    )
    assert q == [
        ("limit", "10"),
        ("ok", "true"),
        ("q", "a b&c"),
        ("created[gte]", "2026-01-01T00:00:00.000Z"),
        ("created[lt]", "2026-02-01T00:00:00Z"),
        ("expand[]", "customer"),
        ("expand[]", "x"),
        ("deep[a][b]", "1"),
        ("naive", "2026-01-01T12:00:00.000Z"),
    ]
