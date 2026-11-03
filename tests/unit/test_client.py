from __future__ import annotations

import json
import re
import uuid

import httpx
import pytest

from pletopay import APIError, Hooks, NotFoundError, Pletopay, PletopayError, RequestOptions
from pletopay._idempotency import IDEMPOTENCY_KEY_PATTERN
from tests.conftest import BASE, LIVE_KEY, TEST_KEY, api_error, ok


class TestConstructor:
    def test_requires_a_secret_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("PLETOPAY_SECRET_KEY", raising=False)
        with pytest.raises(PletopayError, match="No secret key"):
            Pletopay()

    def test_reads_key_and_base_url_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("PLETOPAY_SECRET_KEY", LIVE_KEY)
        monkeypatch.setenv("PLETOPAY_API_URL", "https://api.example.test/")
        c = Pletopay()
        assert c.mode == "live"
        assert c.base_url == "https://api.example.test"

    def test_refuses_publishable_and_malformed_keys(self) -> None:
        with pytest.raises(PletopayError, match="publishable key"):
            Pletopay("pk_test_abc_def")
        with pytest.raises(PletopayError, match="sk_test_"):
            Pletopay("whsec_abc")

    def test_defaults(self) -> None:
        c = Pletopay(TEST_KEY)
        assert c.mode == "test"
        assert c.base_url == "https://api.pletopay.com"
        assert Pletopay.API_VERSION == "2026-09-25"
        assert c.timeout == 30.0
        assert c.max_retries == 2

    def test_validates_numeric_options(self) -> None:
        with pytest.raises(PletopayError, match="max_retries"):
            Pletopay(TEST_KEY, max_retries=-1)
        with pytest.raises(PletopayError, match="timeout"):
            Pletopay(TEST_KEY, timeout=0)


class TestRequestBuilding:
    def test_standard_headers(self, client: Pletopay, mock_api) -> None:
        route = mock_api.get("/api/v1/balance").mock(return_value=ok({"object": "balance", "currency": "NGN"}))
        client.balance.retrieve()
        req = route.calls.last.request
        assert req.headers["authorization"] == f"Bearer {TEST_KEY}"
        assert req.headers["accept"] == "application/json"
        assert req.headers["pletopay-version"] == "2026-09-25"
        assert re.match(r"^pletopay-python/\d+\.\d+\.\d+ python/\d", req.headers["user-agent"])
        assert "idempotency-key" not in req.headers
        assert "content-type" not in req.headers

    def test_api_version_override_app_info_and_correlation(self, mock_api) -> None:
        route = mock_api.get("/api/v1/balance").mock(return_value=ok({}))
        Pletopay(
            TEST_KEY,
            base_url=BASE,
            api_version=False,
            app_info={"name": "my-shop", "version": "2.1", "url": "https://shop.test"},
        ).balance.retrieve()
        req = route.calls[0].request
        assert "pletopay-version" not in req.headers
        assert " my-shop/2.1 (https://shop.test)" in req.headers["user-agent"]
        Pletopay(TEST_KEY, base_url=BASE, api_version="2026-09-24", correlation_id=lambda: "corr-1").balance.retrieve()
        req = route.calls[1].request
        assert req.headers["pletopay-version"] == "2026-09-24"
        assert req.headers["x-correlation-id"] == "corr-1"
        Pletopay(TEST_KEY, base_url=BASE).balance.retrieve(
            options=RequestOptions(
                api_version="2026-09-24",
                correlation_id="corr-2",
                headers={"x-extra": "1", "Authorization": "Bearer nope"},
            )
        )
        req = route.calls[2].request
        assert req.headers["pletopay-version"] == "2026-09-24"
        assert req.headers["x-correlation-id"] == "corr-2"
        assert req.headers["x-extra"] == "1"
        assert req.headers["authorization"] == f"Bearer {TEST_KEY}"

    def test_json_body_and_generated_idempotency_key(self, client: Pletopay, mock_api) -> None:
        route = mock_api.post("/api/v1/payments").mock(return_value=ok({"id": "pay_1", "object": "payment"}, 201))
        client.payments.create(
            amount=5000, currency="NGN", reference="ORDER-1", customer={"email": "a@b.c"}, description=None
        )
        req = route.calls.last.request
        assert req.headers["content-type"] == "application/json"
        assert json.loads(req.content) == {
            "amount": 5000,
            "currency": "NGN",
            "reference": "ORDER-1",
            "customer": {"email": "a@b.c"},
        }
        key = req.headers["idempotency-key"]
        assert uuid.UUID(key).version == 4
        assert IDEMPOTENCY_KEY_PATTERN.match(key)

    def test_caller_idempotency_key_is_used_and_validated(self, client: Pletopay, mock_api) -> None:
        route = mock_api.post("/api/v1/transfers").mock(return_value=ok({"id": "trf_1"}, 201))
        client.transfers.create(
            amount=100000,
            reference="P-1",
            narration="x",
            beneficiary={"bank_code": "058", "account_number": "0123456789"},
            idempotency_key="payout-P-1",
        )
        assert route.calls.last.request.headers["idempotency-key"] == "payout-P-1"
        with pytest.raises(PletopayError, match="printable ASCII"):
            client.transfers.create(
                amount=1,
                reference="r",
                narration="n",
                beneficiary={"bank_code": "058", "account_number": "0"},
                idempotency_key="has space",
            )
        with pytest.raises(PletopayError):
            client.transfers.create(
                amount=1,
                reference="r",
                narration="n",
                beneficiary={"bank_code": "058", "account_number": "0"},
                idempotency_key="x" * 256,
            )
        assert route.call_count == 1

    def test_no_idempotency_key_on_operations_without_it(self, client: Pletopay, mock_api) -> None:
        route = mock_api.post("/api/v1/transfers/name-enquiry").mock(return_value=ok({"account_name": "A"}))
        client.transfers.resolve_account(bank_code="058", account_number="0123456789")
        assert "idempotency-key" not in route.calls.last.request.headers

    def test_path_params_are_encoded_and_required(self, client: Pletopay, mock_api) -> None:
        route = mock_api.get("/api/v1/payments/reference/ORDER%2F1%202").mock(
            return_value=ok({"id": "pay_1", "object": "payment"})
        )
        client.payments.retrieve_by_reference("ORDER/1 2")
        assert route.called
        with pytest.raises(PletopayError, match="id is required"):
            client.payments.retrieve("")
        with pytest.raises(PletopayError, match="id is required"):
            client.payments.retrieve(None)  # type: ignore[arg-type]

    def test_query_filters_with_brackets_lists_and_datetimes(self, client: Pletopay, mock_api) -> None:
        from datetime import datetime, timezone

        route = mock_api.get("/api/v1/payments").mock(return_value=ok([]))
        client.payments.list(
            limit=5,
            status="succeeded",
            created={"gte": datetime(2026, 9, 1, tzinfo=timezone.utc)},
            amount={"lte": 100},
            expand=["customer"],
            q=None,
        )
        url = str(route.calls.last.request.url)
        assert url.endswith(
            "/api/v1/payments?limit=5&created%5Bgte%5D=2026-09-01T00%3A00%3A00.000Z&status=succeeded&amount%5Blte%5D=100&expand%5B%5D=customer"
        )

    def test_datetimes_in_bodies_are_serialised(self, client: Pletopay, mock_api) -> None:
        from datetime import datetime, timezone

        route = mock_api.post("/api/v1/reports").mock(return_value=ok({"id": "rpt_1"}, 201))
        client.reports.create(
            type="payments", period_start=datetime(2026, 1, 1, tzinfo=timezone.utc), period_end="2026-02-01T00:00:00Z"
        )
        assert json.loads(route.calls.last.request.content) == {
            "type": "payments",
            "period_start": "2026-01-01T00:00:00.000Z",
            "period_end": "2026-02-01T00:00:00Z",
        }

    def test_extra_body_and_extra_query(self, client: Pletopay, mock_api) -> None:
        route = mock_api.post("/api/v1/customers").mock(return_value=ok({"id": "cus_1"}, 201))
        client.customers.create(
            email="a@b.c", options=RequestOptions(extra_body={"new_field": 1}, extra_query={"debug": True})
        )
        req = route.calls.last.request
        assert json.loads(req.content) == {"email": "a@b.c", "new_field": 1}
        assert str(req.url).endswith("/customers?debug=true")


class TestResponses:
    def test_unwraps_envelope_and_keeps_response_info(self, client: Pletopay, mock_api) -> None:
        mock_api.get("/api/v1/balance").mock(
            return_value=ok(
                {
                    "object": "balance",
                    "livemode": False,
                    "currency": "NGN",
                    "available": 1,
                    "pending": 0,
                    "held": 0,
                    "unapplied": 0,
                    "settling": 0,
                    "total": 1,
                    "settled_total": 0,
                    "new_field": "x",
                },
                headers={
                    "ratelimit-limit": "200",
                    "ratelimit-remaining": "199",
                    "ratelimit-reset": "7",
                    "idempotent-replayed": "true",
                },
                message="Balance retrieved",
            )
        )
        balance = client.balance.retrieve()
        assert balance.available == 1
        assert balance["new_field"] == "x"
        assert balance.get("missing", "d") == "d"
        info = balance.last_response
        assert info is not None
        assert info.message == "Balance retrieved"
        assert info.request_id == "req_test"
        assert info.api_version == "2026-09-25"
        assert info.status_code == 200
        assert info.idempotent_replayed is True
        assert (info.rate_limit.limit, info.rate_limit.remaining, info.rate_limit.reset) == (200, 199, 7)
        assert "new_field" in balance.model_dump()

    def test_raw_request(self, client: Pletopay, mock_api) -> None:
        route = mock_api.post("/api/v1/anything").mock(
            return_value=ok({"ok": True}, headers={"deprecation": "true", "sunset": "2028"}, message="Done")
        )
        res = client.request(
            "post", "/api/v1/anything", body={"a": 1}, query={"b": [1, 2]}, idempotency="optional", idempotency_key="k1"
        )
        assert res.data == {"ok": True}
        assert res.message == "Done"
        assert res.request_id == "req_test"
        assert res.response.idempotency_key == "k1"
        assert res.response.deprecation == "true"
        assert str(route.calls.last.request.url).endswith("/anything?b%5B%5D=1&b%5B%5D=2")

    def test_csv_download(self, client: Pletopay, mock_api) -> None:
        route = mock_api.get("/api/v1/reports/rpt_1/download").mock(
            return_value=httpx.Response(200, text="id,amount\npay_1,100\n", headers={"content-type": "text/csv"})
        )
        assert client.reports.download("rpt_1") == "id,amount\npay_1,100\n"
        assert route.calls.last.request.headers["accept"] == "text/csv"

    def test_rejects_non_envelope_success(self, client: Pletopay, mock_api) -> None:
        mock_api.get("/api/v1/balance").mock(return_value=httpx.Response(200, text="<html>proxy</html>"))
        with pytest.raises(APIError, match="unexpected response body"):
            client.balance.retrieve()

    def test_test_mode_only_guard(self, mock_api) -> None:
        c = Pletopay(LIVE_KEY, base_url=BASE)
        with pytest.raises(PletopayError, match="only available in test mode"):
            c.sandbox.simulate_transfer(account_number="1", amount=1)
        assert not mock_api.calls

    def test_typed_errors(self, client: Pletopay, mock_api) -> None:
        mock_api.get("/api/v1/payments/pay_x").mock(
            return_value=api_error(404, "not_found", "resource_missing", message="No such payment")
        )
        with pytest.raises(NotFoundError) as info:
            client.payments.retrieve("pay_x")
        err = info.value
        assert err.status_code == 404
        assert err.code == "resource_missing"
        assert err.type == "not_found"
        assert err.request_id == "req_err"
        assert str(err) == "No such payment (request_id: req_err)"

    def test_lenient_parsing_on_schema_drift(self, client: Pletopay, mock_api) -> None:
        mock_api.get("/api/v1/payments/pay_1").mock(
            return_value=ok(
                {
                    "id": "pay_1",
                    "object": "payment",
                    "status": "teleported",
                    "customer": {"id": "cus_1", "object": "customer", "email": "x"},
                }
            )
        )
        with pytest.warns(UserWarning, match="did not match this SDK's schema"):
            payment = client.payments.retrieve("pay_1")
        assert payment.id == "pay_1"
        assert payment.status == "teleported"
        assert payment.customer.id == "cus_1"  # nested dict still became a model
        assert payment.last_response is not None

    def test_hooks_get_redacted_headers(self, mock_api) -> None:
        seen: list[dict] = []
        mock_api.get("/api/v1/balance").mock(return_value=ok({"object": "balance"}))
        Pletopay(
            TEST_KEY, base_url=BASE, hooks=Hooks(on_request=seen.append, on_response=seen.append)
        ).balance.retrieve()
        assert seen[0]["headers"]["authorization"] == "Bearer sk_***"
        assert seen[1]["status_code"] == 200
        assert seen[1]["request_id"] == "req_test"

    def test_context_manager_and_custom_http_client(self) -> None:
        http = httpx.Client(
            transport=httpx.MockTransport(
                lambda req: httpx.Response(200, json={"status": True, "message": "", "data": {"object": "balance"}})
            )
        )
        with Pletopay(TEST_KEY, http_client=http) as c:
            assert c.balance.retrieve().object == "balance"
        assert not http.is_closed  # we do not close a client we were given
        http.close()
