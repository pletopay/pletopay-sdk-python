from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

import pytest

from pletopay import Pletopay, SignatureVerificationError, construct_event
from pletopay.types import EventWebhookTest
from tests.live.conftest import poll

deliveries: list[dict[str, Any]] = []
state: dict[str, Any] = {}


class Handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        length = int(self.headers.get("content-length", "0"))
        deliveries.append({"headers": {k.lower(): v for k, v in self.headers.items()}, "body": self.rfile.read(length)})
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *_: Any) -> None:
        return


@pytest.fixture(scope="module")
def server() -> Any:
    httpd = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield httpd
    httpd.shutdown()


def test_register_endpoint(live: Pletopay, server: HTTPServer) -> None:
    url = f"http://127.0.0.1:{server.server_port}/hooks/pletopay"
    endpoint = live.webhook_endpoints.create(
        url=url, enabled_events=["webhook.test", "payment.succeeded"], description="SDK live test"
    )
    assert endpoint.status == "enabled"
    assert endpoint.secret is not None and endpoint.secret.startswith("whsec_")
    state["endpoint"] = endpoint
    state["secret"] = endpoint.secret
    assert live.webhook_endpoints.retrieve(endpoint.id).secret is None


def test_signed_test_delivery(live: Pletopay) -> None:
    endpoint = state["endpoint"]
    delivery = live.webhook_endpoints.test(endpoint.id)
    assert delivery.endpoint == endpoint.id
    poll(lambda: len(deliveries), lambda n: n > 0)
    received = deliveries[0]
    assert received["headers"]["x-pletopay-event-type"] == "webhook.test"
    event = construct_event(received["body"], received["headers"]["x-pletopay-signature"], state["secret"])
    assert isinstance(event, EventWebhookTest)
    assert event.id == received["headers"]["x-pletopay-event-id"]
    assert event.livemode is False
    with pytest.raises(SignatureVerificationError):
        construct_event(received["body"], received["headers"]["x-pletopay-signature"], "whsec_wrong")


def test_deliveries_events_rotate_update(live: Pletopay) -> None:
    endpoint = state["endpoint"]
    page = poll(
        lambda: live.webhook_endpoints.list_deliveries(endpoint.id, limit=10),
        lambda p: any(d.status == "succeeded" for d in p),
    )
    assert page[0].endpoint == endpoint.id
    events = live.events.list(type="webhook.test", limit=5)
    assert len(events) > 0
    event_id = events[0].id
    assert live.events.retrieve(event_id).id == event_id
    assert len(live.events.list_deliveries(event_id)) > 0
    rotated = live.webhook_endpoints.rotate_secret(endpoint.id)
    assert rotated.secret and rotated.secret != state["secret"]
    updated = live.webhook_endpoints.update(endpoint.id, description="rotated", status="disabled")
    assert updated.status == "disabled" and updated.description == "rotated"
    assert live.webhook_endpoints.update(endpoint.id, status="enabled").status == "enabled"
    assert endpoint.id in [e.id for e in live.webhook_endpoints.list()]


def test_delete_endpoint(live: Pletopay) -> None:
    endpoint = state["endpoint"]
    deleted = live.webhook_endpoints.delete(endpoint.id)
    assert deleted.id == endpoint.id and deleted.deleted is True
