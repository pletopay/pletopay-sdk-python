"""A Flask webhook endpoint that verifies signatures, answers fast and de-duplicates.

PLETOPAY_WEBHOOK_SECRET=whsec_... flask --app examples/flask_webhook run --port 3000
"""

import os

from flask import Flask, abort, request

import pletopay
from pletopay.types import EventPaymentSucceeded, EventTransferFailed

app = Flask(__name__)
webhooks = pletopay.Webhook(os.environ["PLETOPAY_WEBHOOK_SECRET"])
seen: set[str] = set()  # use your database in production


@app.post("/webhooks/pletopay")
def pletopay_webhook() -> tuple[str, int]:
    try:
        event = webhooks.construct_event(request.get_data(), request.headers.get("X-PletoPay-Signature"))
    except pletopay.SignatureVerificationError as error:
        abort(400, str(error))

    if event.id in seen:  # deliveries are at least once
        return "", 200
    seen.add(event.id)

    match event:
        case EventPaymentSucceeded():
            print("paid", event.data.object.reference, event.data.object.amount_received)
        case EventTransferFailed():
            print("payout failed", event.data.object.reference, event.data.object.failure_reason)
        case _:
            print("ignored", event.type)
    return "", 200  # do slow work in a background job
