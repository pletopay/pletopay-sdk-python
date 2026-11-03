# Examples

Each file is a small, runnable script. Install the SDK (`pip install pletopay`) plus `flask` or `fastapi` for the webhook ones.

- `create_checkout_session.py`: server-created session for the hosted page or the popup.
- `payout.py`: name enquiry, then a transfer with a deterministic idempotency key and error handling.
- `flask_webhook.py`: raw-body signature verification, fast 200, de-duplication and typed event handling with `match`.
- `fastapi_webhook.py`: the same with the async client and a background task.
