from __future__ import annotations

import pytest

import pletopay
from pletopay import PletopayError, SignatureVerificationError, Webhook
from pletopay.types import EventPaymentSucceeded, UnknownEvent
from pletopay.webhook import (
    assert_signature,
    compute_signature,
    construct_event,
    generate_test_header,
    parse_event,
    parse_signature_header,
    verify_signature,
)
from tests.conftest import FIXTURES, TEST_KEY, load_fixture

fixture = load_fixture("webhook-signature.json")
payload_bytes = (FIXTURES / fixture["payload_file"]).read_bytes()
payload = payload_bytes.decode()
NOW = fixture["now_inside"]
SECRET = fixture["secret"]


def test_parse_header() -> None:
    parsed = parse_signature_header(fixture["header_rotated"])
    assert parsed.timestamp == fixture["timestamp"]
    assert len(parsed.signatures) == 2
    for bad in (None, "", "v1=abc", "t=abc,v1=def", "t=1", "garbage"):
        with pytest.raises(SignatureVerificationError):
            parse_signature_header(bad)


def test_fixture_verifies_with_str_and_bytes() -> None:
    assert verify_signature(payload, fixture["header"], SECRET, now=NOW)
    assert verify_signature(payload_bytes, fixture["header"], SECRET, now=NOW)
    assert compute_signature(SECRET, fixture["timestamp"], payload) == fixture["header"].split("v1=")[1]
    assert verify_signature(payload, fixture["header_rotated"], SECRET, now=NOW)


def test_rejects_wrong_signature_secret_or_payload() -> None:
    assert not verify_signature(payload, fixture["header_wrong"], SECRET, now=NOW)
    assert not verify_signature(payload, fixture["header"], "whsec_other", now=NOW)
    assert not verify_signature(payload.replace("5000000", "5000001"), fixture["header"], SECRET, now=NOW)
    assert not verify_signature(payload + "\n", fixture["header"], SECRET, now=NOW)


def test_tolerance() -> None:
    assert verify_signature(payload, fixture["header"], SECRET, now=fixture["now_inside"])
    assert not verify_signature(payload, fixture["header"], SECRET, now=fixture["now_outside"])
    assert not verify_signature(payload, fixture["header"], SECRET, now=fixture["timestamp"] - 301)
    assert verify_signature(payload, fixture["header"], SECRET, now=fixture["now_outside"], tolerance=600)
    assert not verify_signature(payload, fixture["header"], SECRET)  # real "now" is far away


def test_construct_event_typed() -> None:
    event = construct_event(payload_bytes, fixture["header"], SECRET, now=NOW)
    assert isinstance(event, EventPaymentSucceeded)
    assert event.id == fixture["event_id"]
    assert event.type == "payment.succeeded"
    assert event.data.object.amount_received == 5000000
    assert event.data.object.created_at.year == 2026
    with pytest.raises(SignatureVerificationError, match="tolerance"):
        construct_event(payload, fixture["header"], SECRET, now=fixture["now_outside"])
    with pytest.raises(SignatureVerificationError, match="No signature found"):
        construct_event(payload, fixture["header_wrong"], SECRET, now=NOW)


def test_rejects_non_event_payloads() -> None:
    header = generate_test_header('{"hello":1}', SECRET)
    with pytest.raises(SignatureVerificationError, match="not an event object"):
        construct_event('{"hello":1}', header, SECRET)
    with pytest.raises(SignatureVerificationError, match="not valid JSON"):
        construct_event("nope", generate_test_header("nope", SECRET), SECRET)


def test_configuration_errors_raise_not_false() -> None:
    with pytest.raises(PletopayError):
        verify_signature({"parsed": True}, fixture["header"], SECRET)  # type: ignore[arg-type]
    with pytest.raises(PletopayError, match="signing secret"):
        verify_signature(payload, fixture["header"], "")


def test_unknown_and_drifted_events() -> None:
    unknown = parse_event(
        {
            "id": "evt_1",
            "object": "event",
            "type": "payment.teleported",
            "api_version": "x",
            "livemode": False,
            "created_at": "2026-01-01T00:00:00Z",
            "data": {"object": {"id": "pay_1"}},
        }
    )
    assert isinstance(unknown, UnknownEvent)
    assert unknown.data.object["id"] == "pay_1"
    with pytest.warns(UserWarning, match="did not match"):
        drifted = parse_event(
            {
                "id": "evt_1",
                "object": "event",
                "type": "payment.succeeded",
                "api_version": "x",
                "livemode": False,
                "created_at": "2026-01-01T00:00:00Z",
                "data": {"object": {"id": "pay_1", "status": "new_status"}},
            }
        )
    assert isinstance(drifted, EventPaymentSucceeded)
    assert drifted.data.object.id == "pay_1"
    assert pletopay.is_known_event_type("payment.succeeded") and not pletopay.is_known_event_type("x")
    assert len(pletopay.EVENT_TYPES) == 38


def test_test_header_round_trip() -> None:
    header = generate_test_header(payload, "whsec_x", timestamp=1700000000)
    assert header == f"t=1700000000,v1={compute_signature('whsec_x', 1700000000, payload)}"
    assert verify_signature(payload, header, "whsec_x", now=1700000010)


def test_webhook_class_and_client_integration() -> None:
    wh = Webhook(SECRET, tolerance=1000)
    assert wh.verify_signature(payload, fixture["header"]) is False  # tolerance 1000 but real now is far
    assert wh.construct_event(payload, fixture["header"], tolerance=10**9).type == "payment.succeeded"
    assert wh.generate_test_header(payload, timestamp=5) == f"t=5,v1={compute_signature(SECRET, 5, payload)}"
    with pytest.raises(PletopayError, match="No webhook secret"):
        Webhook().construct_event(payload, fixture["header"])
    c = pletopay.Pletopay(TEST_KEY, webhook_secret=SECRET)
    assert c.webhooks.construct_event(payload, fixture["header"], tolerance=10**9).id == fixture["event_id"]


def test_non_hex_signature_is_a_verification_failure_not_a_crash() -> None:
    # Regression (SDK-01): a non-ASCII v1 value made hmac.compare_digest raise TypeError, which
    # verify_signature does not catch, so a forged request crashed the merchant's handler.
    for bad in ("é", "abc", "zz" * 32, "0" * 63, "0" * 65):
        header = f"t={NOW},v1={bad}"
        assert not verify_signature(payload, header, SECRET, now=NOW)
        with pytest.raises(SignatureVerificationError):
            assert_signature(payload, header, SECRET, now=NOW)
    # Upper-case hex of the right signature still verifies; a bad one next to a good one still passes.
    ts, good = fixture["timestamp"], fixture["header"].split("v1=")[1]
    assert verify_signature(payload, f"t={ts},v1={good.upper()}", SECRET, now=NOW)
    assert verify_signature(payload, f"t={ts},v1=é,v1={good}", SECRET, now=NOW)


def test_webhook_class_honours_zero_tolerance() -> None:
    import time as _time

    hook = Webhook(SECRET)
    header = generate_test_header(payload, SECRET, timestamp=int(_time.time()) - 5)
    assert hook.verify_signature(payload, header)  # default tolerance (300 s)
    assert not hook.verify_signature(payload, header, tolerance=0)  # 0 must not fall back to the default
