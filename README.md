# Pletopay Python SDK

`pletopay` is the official Python client for the [Pletopay API](https://docs.pletopay.com): bank-transfer payments, virtual accounts, checkout, invoices, transfers, settlements and signed webhooks for Nigeria.

- Every endpoint of the merchant API, with pydantic models generated from the published OpenAPI contract.
- Sync and async clients, idempotency keys, automatic retries, cursor pagination, typed errors and webhook signature verification built in.
- Python 3.10+. Depends on `httpx` and `pydantic` v2 only. Fully typed (`py.typed`).

## Install

```bash
pip install pletopay
```

## Quick start

```python
import pletopay

client = pletopay.Pletopay(secret_key="sk_test_...")  # or set PLETOPAY_SECRET_KEY

# 1. Create a payment: the customer transfers to the account in `bank_transfer`.
payment = client.payments.create(
    amount=5000000,  # ₦50,000.00 in kobo
    reference="ORDER-123",
    customer={"email": "ada@example.com"},
    idempotency_key="create-payment-ORDER-123",
)
print(payment.bank_transfer.account_number, payment.bank_transfer.bank_name, payment.expires_at)

# 2. Confirm from the server: the payment is paid only when `status` is "succeeded".
latest = client.payments.retrieve(payment.id)
if latest.status == "succeeded":
    ...  # fulfil ORDER-123, once
```

Amounts are integers in kobo. Test and live data are separate: the key prefix (`sk_test_` / `sk_live_`) selects the mode and there is no separate sandbox host.

The secret key must stay on your server. Browsers use the publishable key with [pletopay.js](https://docs.pletopay.com/checkout/popup); this SDK refuses `pk_` keys.

## Async

```python
async with pletopay.AsyncPletopay() as client:
    balance = await client.balance.retrieve()
    async for payment in (await client.payments.list(status="succeeded")).auto_paging_iter():
        print(payment.reference)
```

`AsyncPletopay` has the same resources, parameters and behaviour as `Pletopay`.

## Configuration

```python
client = pletopay.Pletopay(
    secret_key="sk_test_...",          # default: PLETOPAY_SECRET_KEY
    base_url="https://api.pletopay.com",  # default: PLETOPAY_API_URL, then this
    api_version="2026-09-25",          # the dated version this SDK's models describe (default); False to use your organization's pin
    timeout=30.0,                      # seconds, per request
    max_retries=2,                     # see Retries
    webhook_secret="whsec_...",        # for client.webhooks.construct_event (default: PLETOPAY_WEBHOOK_SECRET)
    http_client=httpx.Client(proxy="http://proxy:3128"),  # your own httpx client: proxies, transports, instrumentation
    correlation_id=lambda: current_request_id(),          # sent as X-Correlation-Id
    app_info={"name": "my-shop-plugin", "version": "1.2.0"},  # appended to User-Agent
    hooks=pletopay.Hooks(on_retry=lambda ctx: metrics.incr("pletopay.retry")),
)
```

Every method also takes `options=pletopay.RequestOptions(timeout=..., max_retries=..., correlation_id=..., api_version=..., headers={...}, extra_query={...}, extra_body={...})`. `extra_body` lets you send fields newer than this SDK.

## Resources

Method names follow the API's operation ids. All 82 operations are covered, with keyword-only parameters named after the API's fields:

| Resource | Methods |
| --- | --- |
| `customers` | `create` `list` `retrieve` `update` `set_risk_status` |
| `payments` | `create` `list` `retrieve` `retrieve_by_reference` (all accept `expand=["customer"]`) |
| `virtual_accounts` | `create` `list` `retrieve` `retrieve_by_reference` `close` |
| `subaccounts` | `create` `list` `retrieve` `update` `retrieve_balance` |
| `split_rules` | `create` `list` `retrieve` `update` |
| `transfers` | `create` `list` `retrieve` `retrieve_by_reference` `resolve_account` |
| `banks` | `list` |
| `settlements` | `list` `retrieve` `list_items` |
| `refunds` | `create` `list` `retrieve` `retrieve_by_reference` |
| `checkout.sessions` | `create` `list` `retrieve` `retrieve_by_reference` `expire` |
| `payment_links` | `create` `list` `retrieve` `update` |
| `invoices` | `create` `list` `retrieve` `update` `finalize` `void` `mark_uncollectible` |
| `plans` | `create` `list` `retrieve` `update` |
| `subscriptions` | `create` `list` `retrieve` `cancel` |
| `risk` | `list_events` `retrieve_limits` |
| `reports` | `create` `list` `retrieve` `download` (CSV text) `statement` |
| `webhook_endpoints` | `create` `list` `retrieve` `update` `delete` `rotate_secret` `test` `list_deliveries` |
| `events` | `list` `retrieve` `list_deliveries` `replay` |
| `balance` | `retrieve` |
| `transactions` | `list` |
| `sandbox` | `simulate_transfer` (test mode only; refused locally with a live key) |

Every parameter is documented in the method's signature and docstring (your editor shows them), and the full field reference for each operation is in the [API reference](https://docs.pletopay.com/reference). Responses are pydantic models (`pletopay.types.Payment`, `Transfer`, `CheckoutSession`, …) with the API's `snake_case` field names; timestamps are `datetime` objects. Fields this SDK version does not know are kept and reachable with `payment["new_field"]` or `payment.model_extra`.

### Checkout

```python
session = client.checkout.sessions.create(
    amount=250000, reference="ORDER-124", success_url="https://shop.test/thanks", idempotency_key="checkout-ORDER-124"
)
# Hosted page: redirect to session.url. Popup: hand session.token to pletopay.js in the browser.
# Later, on your server:
if client.checkout.sessions.retrieve(session.id).status == "complete":
    ...  # fulfil
```

### Transfers (payouts)

```python
who = client.transfers.resolve_account(bank_code="058", account_number="0123456789")
transfer = client.transfers.create(
    amount=2500000,
    reference="PAYOUT-2026-0001",
    narration="Vendor payout",
    beneficiary={"bank_code": "058", "account_number": "0123456789"},
    idempotency_key="payout-PAYOUT-2026-0001",
)
```

The API requires an `Idempotency-Key` on transfers and refunds. Pass your own, deterministic key (your payout id) so a retry from a crashed process can never pay twice. The SDK generates a random key only when you omit it.

## Pagination

List methods return the first page. Iterate it for that page's items, or `auto_paging_iter()` for every item across pages:

```python
page = client.payments.list(limit=50, status="succeeded", created={"gte": "2026-09-01T00:00:00Z"})
page.data, page.has_more, page.next_cursor
nxt = page.next_page()  # None on the last page

for payment in client.payments.list(status="succeeded").auto_paging_iter():
    print(payment.id)

first_hundred = client.transfers.list().auto_paging_list(limit=100)
```

Filters use the API's bracket syntax under the hood (`created[gte]`, `amount[lte]`, `expand[]`); pass plain dicts, lists and `datetime` objects.

## Errors

Every failed request raises a subclass of `pletopay.APIError` chosen from the API's `error.type`. Branch on `code`, which is stable; the message is for people.

```python
try:
    client.payments.create(amount=100, reference="ORDER-1")
except pletopay.ConflictError as error:
    if error.code == "duplicate_reference":
        payment = client.payments.retrieve_by_reference("ORDER-1")
except pletopay.RateLimitError as error:
    print("retry after", error.retry_after, "s")
except pletopay.APIError as error:
    print(error.status_code, error.code, error.param, error.request_id)
```

| Class | When |
| --- | --- |
| `InvalidRequestError` | 400: a field is missing, invalid or unknown (`param` names it) |
| `AuthenticationError` | 401: bad or missing key |
| `PermissionDeniedError` | 403: not allowed in this mode or for this account |
| `NotFoundError` | 404 |
| `ConflictError` | 409: wrong state, duplicate reference |
| `IdempotencyError` | 409/422: key reused with a different body, or still in progress |
| `RateLimitError` | 429, with `retry_after` |
| `APIServerError` | 5xx |
| `APIConnectionError` / `APITimeoutError` | no response / timeout exceeded |
| `SignatureVerificationError` | a webhook did not verify |

All of them extend `PletopayError`. `request_id` is on every API error: quote it to support. The full catalogue of codes is in the [API reference](https://docs.pletopay.com/reference/errors).

## Retries and idempotency

Network errors, timeouts, `429`, `500`, `502`, `503` and `409 idempotency_request_in_progress` are retried up to `max_retries` times (default 2) with exponential backoff and jitter, honouring `Retry-After`. A request is retried only when that is safe: `GET`/`DELETE`, or a write that carries an `Idempotency-Key`. Writes to endpoints that accept the header get a generated UUID key when you do not pass one, so the retry replays the same request instead of acting twice.

## Webhooks

Verify every delivery against the raw request body, then act on the event. Deliveries are at least once and unordered: de-duplicate on `event.id`.

```python
from flask import Flask, abort, request
import pletopay
from pletopay.types import EventPaymentSucceeded

webhooks = pletopay.Webhook(os.environ["PLETOPAY_WEBHOOK_SECRET"])

@app.post("/webhooks/pletopay")
def pletopay_webhook():
    try:
        event = webhooks.construct_event(request.get_data(), request.headers.get("X-PletoPay-Signature"))
    except pletopay.SignatureVerificationError as error:
        abort(400, str(error))

    if isinstance(event, EventPaymentSucceeded):
        fulfil(event.data.object.reference, event.data.object.amount_received)  # typed as Payment
    return "", 200  # answer within 10 s; do slow work in a background job
```

`construct_event` raises `SignatureVerificationError` for a missing, malformed, stale (more than 300 s old) or wrong signature. `verify_signature` returns a boolean instead. To test your handler, sign a payload with `pletopay.generate_test_header(payload, secret)`.

Events are typed classes (`EventPaymentSucceeded`, `EventTransferFailed`, …) that work with `isinstance` and `match`; `event.data.object` is the resource. New event types may appear at any time and parse to `pletopay.UnknownEvent`.

## Lower-level access

```python
balance = client.balance.retrieve()
balance.last_response.request_id   # and rate_limit, api_version, idempotent_replayed, headers

# Any endpoint, with the unwrapped data and the response metadata back:
res = client.request("GET", "/api/v1/payments", query={"limit": 5})
res.data, res.meta, res.request_id
```

## Versioning

The SDK follows [semantic versioning](https://semver.org). It sends `PletoPay-Version: 2026-09-25` (`pletopay.API_VERSION`) so responses match its models; set `api_version` to pin a different dated version. New fields, parameters, event types and enum values can appear without a major release: unknown fields are kept, and a response that no longer matches the models still loads (with a `UserWarning`) instead of raising. See [CHANGELOG.md](CHANGELOG.md).

## Development

```bash
make venv                 # .venv with the package and dev tools
make sync generate        # refresh spec/public.v1.yaml from ../pletopay-api and regenerate models and the operation table
make verify               # lint, mypy, brand and generated-code checks, unit tests, build
PLETOPAY_API_URL=http://localhost:8080 PLETOPAY_SECRET_KEY=sk_test_... make test-live   # against a running API
```

`tests/test_spec_conformance.py` fails whenever the contract gains or changes an operation that the SDK does not implement.

## License

[MIT](LICENSE)
