# Changelog

All notable changes to `pletopay` are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org).

## [Unreleased]

### Security

- `verify_signature` / `construct_event`: a non-hex `v1=` value (for example non-ASCII text) is now a plain verification failure. Previously `hmac.compare_digest` raised `TypeError`, which `verify_signature` did not catch, so a forged request could crash the handler.

### Fixed

- `Webhook(...).verify_signature(..., tolerance=0)` honours `0` instead of falling back to the instance default.
- Auto-pagination of a list started with `ending_before` walked the wrong way: the second request used `starting_after`, so it returned the cursor object and everything older, and the newer objects past the first page were never returned. Such a list now continues with `ending_before` set to the first id of the current page until `meta.has_more` is false. `auto_paging_iter()` and `auto_paging_list()` yield oldest to newest across pages, `page.next_cursor` is the id to pass as `ending_before`, and `page.data` keeps the API's order. Lists without `ending_before` are unchanged. Applies to `SyncPage` and `AsyncPage`.
- `transfers.create` and `refunds.create` were reported as failed while the API went on to pay out: the request timed out after 30 s although the API can wait up to 75 s for the bank, the retries got `409 idempotency_request_in_progress` and the SDK raised about a second later. These two calls now default to a 90 s timeout (a `timeout` set on the client or in `RequestOptions` still wins), and `409 idempotency_request_in_progress` is retried with the same key about every 2 s (or after `Retry-After`) without using up `max_retries`, until the first attempt answers or 90 s have passed since the call started. Applies to both clients.

### Added

- `idempotency_key` on every error raised for a request that carried an `Idempotency-Key` (API errors of any status, `APITimeoutError`, `APIConnectionError`), whether the key was yours or generated, so a caller can retry or reconcile with it. It is `None` on other errors.

### Changed

- The `timeout` argument of `Pletopay` / `AsyncPletopay` defaults to `None` (30 s, and 90 s for the two calls above) instead of `30.0`; `client.timeout` still reads `30.0`.

## [1.0.0] - 2026-10-23

### Added

- `Pletopay` (sync) and `AsyncPletopay` clients covering all 82 operations of the merchant API (`PletoPay-Version: 2026-09-25`), with pydantic models generated from the OpenAPI contract.
- Automatic `Idempotency-Key` generation on idempotent writes, client-side key validation, and automatic retries with exponential backoff that honour `Retry-After`.
- Cursor pagination: `SyncPage` / `AsyncPage` with `auto_paging_iter()`, `next_page()`, `pages()` and `auto_paging_list()`.
- Typed errors: one class per API error type, plus connection, timeout and signature-verification errors. Every API error carries `code`, `param`, `details`, `request_id` and the rate-limit headers.
- Webhook helpers: `construct_event`, `verify_signature`, `generate_test_header`, a discriminated event union, `UnknownEvent` for new types and `EVENT_TYPES`.
- Lenient parsing: responses that no longer match this SDK's schema still load (with a warning) instead of raising.
- `RequestOptions` (timeout, retries, correlation id, extra headers/query/body), hooks, custom `httpx` clients, `last_response` metadata and `client.request()` for raw calls.
