from __future__ import annotations

import httpx

from pletopay import Pletopay, SyncPage
from tests.conftest import list_api, page


def ids(first: int, last: int) -> list[str]:
    step = 1 if last >= first else -1
    return [f"pay_{n}" for n in range(first, last + step, step)]


def test_iterates_pages_and_passes_cursor(client: Pletopay, mock_api) -> None:
    route = mock_api.get("/api/v1/payments").mock(
        side_effect=[
            page([{"id": "pay_3", "object": "payment"}, {"id": "pay_2", "object": "payment"}], True, "pay_2"),
            page([{"id": "pay_1", "object": "payment"}], False, None),
        ]
    )
    first = client.payments.list(limit=2, status="succeeded")
    assert isinstance(first, SyncPage)
    assert [p.id for p in first] == ["pay_3", "pay_2"]
    assert len(first) == 2 and first[0].id == "pay_3"
    assert [p.id for p in first.auto_paging_iter()] == ["pay_3", "pay_2", "pay_1"]
    assert str(route.calls[0].request.url).endswith("/payments?limit=2&status=succeeded")
    assert str(route.calls[1].request.url).endswith("/payments?limit=2&status=succeeded&starting_after=pay_2")


def test_ending_before_walks_towards_newer_items_oldest_first(client: Pletopay, mock_api) -> None:
    route = mock_api.get("/api/v1/payments").mock(side_effect=list_api(20))
    first = client.payments.list(limit=3, ending_before="pay_9")
    assert [p.id for p in first.auto_paging_iter()] == ids(10, 20)
    cursors = [call.request.url.params.get("ending_before") for call in route.calls]
    assert cursors == ["pay_9", "pay_12", "pay_15", "pay_18"]
    assert not any("starting_after" in call.request.url.params for call in route.calls)


def test_backward_pages_keep_api_order_and_continue_from_their_first_item(client: Pletopay, mock_api) -> None:
    mock_api.get("/api/v1/payments").mock(side_effect=list_api(20))
    first = client.payments.list(limit=3, ending_before="pay_9")
    assert [p.id for p in first] == ["pay_12", "pay_11", "pay_10"]
    assert first.has_more and first.next_cursor == "pay_12"
    second = first.next_page()
    assert second is not None and [p.id for p in second.data] == ["pay_15", "pay_14", "pay_13"]
    pages = list(first.pages())
    assert [[p.id for p in pg.data] for pg in pages] == [ids(12, 10), ids(15, 13), ids(18, 16), ids(20, 19)]
    last = pages[-1]
    assert not last.has_more and last.next_cursor is None and last.next_page() is None
    assert [p.id for p in first.auto_paging_list(limit=4)] == ids(10, 13)


def test_backward_list_does_not_need_next_cursor(client: Pletopay, mock_api) -> None:
    mock_api.get("/api/v1/payments").mock(side_effect=list_api(20, backward_cursor=False))
    items = client.payments.list(limit=3, ending_before="pay_9").auto_paging_list()
    assert [p.id for p in items] == ids(10, 20)


def test_forward_paging_against_the_same_api_is_unchanged(client: Pletopay, mock_api) -> None:
    route = mock_api.get("/api/v1/payments").mock(side_effect=list_api(20))
    assert [p.id for p in client.payments.list(limit=6).auto_paging_iter()] == ids(20, 1)
    assert [p.id for p in client.payments.list(limit=3, starting_after="pay_9").auto_paging_iter()] == ids(8, 1)
    assert not any("ending_before" in call.request.url.params for call in route.calls)


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
