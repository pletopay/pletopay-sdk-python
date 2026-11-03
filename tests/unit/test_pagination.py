from __future__ import annotations

import httpx

from pletopay import Pletopay, SyncPage
from tests.conftest import page


def test_iterates_pages_and_passes_cursor(client: Pletopay, mock_api) -> None:
    route = mock_api.get("/api/v1/payments").mock(
        side_effect=[
            page([{"id": "pay_3", "object": "payment"}, {"id": "pay_2", "object": "payment"}], True, "pay_2"),
            page([{"id": "pay_1", "object": "payment"}], False, None),
        ]
    )
    first = client.payments.list(limit=2, status="succeeded", ending_before="pay_9")
    assert isinstance(first, SyncPage)
    assert [p.id for p in first] == ["pay_3", "pay_2"]
    assert len(first) == 2 and first[0].id == "pay_3"
    assert [p.id for p in first.auto_paging_iter()] == ["pay_3", "pay_2", "pay_1"]
    assert str(route.calls[0].request.url).endswith("/payments?limit=2&ending_before=pay_9&status=succeeded")
    assert str(route.calls[1].request.url).endswith("/payments?limit=2&status=succeeded&starting_after=pay_2")


def test_next_page_meta_and_response(client: Pletopay, mock_api) -> None:
    second = page([{"id": "b", "object": "customer"}], False, None)
    mock_api.get("/api/v1/customers").mock(
        side_effect=[page([{"id": "a", "object": "customer"}], True, "a"), second, second]
    )
    first = client.customers.list()
    assert first.has_more and first.next_cursor == "a"
    assert first.response.request_id == "req_test"
    assert first.meta.url == "/api/v1/x"
    assert first.data[0].last_response is first.response
    nxt = first.next_page()
    assert nxt is not None and nxt.data[0].id == "b" and not nxt.has_more
    assert nxt.next_page() is None
    assert len(list(first.pages())) == 2


def test_auto_paging_list_limit(client: Pletopay, mock_api) -> None:
    route = mock_api.get("/api/v1/transactions").mock(
        side_effect=[page([{"id": "1"}, {"id": "2"}], True, "c1"), page([{"id": "3"}, {"id": "4"}], True, "c2")]
    )
    items = client.transactions.list().auto_paging_list(limit=3)
    assert [i.id for i in items] == ["1", "2", "3"]
    assert route.call_count == 2


def test_missing_meta_is_single_page(client: Pletopay, mock_api) -> None:
    mock_api.get("/api/v1/banks").mock(
        return_value=httpx.Response(
            200, json={"status": True, "message": "ok", "data": [{"code": "058", "name": "GTB"}]}
        )
    )
    banks = client.banks.list()
    assert [b.code for b in banks] == ["058"]
    assert not banks.has_more
    assert banks.auto_paging_list() == banks.data
