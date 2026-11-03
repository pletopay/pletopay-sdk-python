"""A FastAPI webhook endpoint using the async client.

PLETOPAY_WEBHOOK_SECRET=whsec_... PLETOPAY_SECRET_KEY=sk_test_... uvicorn examples.fastapi_webhook:app --port 3000
"""

import os

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request

import pletopay
from pletopay.types import EventPaymentSucceeded

app = FastAPI()
webhooks = pletopay.Webhook(os.environ["PLETOPAY_WEBHOOK_SECRET"])
client = pletopay.AsyncPletopay()


async def fulfil(payment_id: str) -> None:
    payment = await client.payments.retrieve(payment_id)  # confirm the latest state before fulfilling
    if payment.status == "succeeded":
        print("fulfil", payment.reference)


@app.post("/webhooks/pletopay")
async def pletopay_webhook(request: Request, background: BackgroundTasks) -> dict[str, bool]:
    try:
        event = webhooks.construct_event(await request.body(), request.headers.get("X-PletoPay-Signature"))
    except pletopay.SignatureVerificationError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    if isinstance(event, EventPaymentSucceeded):
        background.add_task(fulfil, event.data.object.id)
    return {"received": True}
