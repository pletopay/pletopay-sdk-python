# Changelog

All notable changes to `pletopay` are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org).

## [Unreleased]

### Security

- `verify_signature` / `construct_event`: a non-hex `v1=` value (for example non-ASCII text) is now a plain verification failure. Previously `hmac.compare_digest` raised `TypeError`, which `verify_signature` did not catch, so a forged request could crash the handler.

### Fixed

- `Webhook(...).verify_signature(..., tolerance=0)` honours `0` instead of falling back to the instance default.

## [1.0.0] - 2026-10-23

### Added

- `Pletopay` (sync) and `AsyncPletopay` clients covering all 82 operations of the merchant API (`PletoPay-Version: 2026-09-25`), with pydantic models generated from the OpenAPI contract.
- Automatic `Idempotency-Key` generation on idempotent writes, client-side key validation, and automatic retries with exponential backoff that honour `Retry-After`.
- Cursor pagination: `SyncPage` / `AsyncPage` with `auto_paging_iter()`, `next_page()`, `pages()` and `auto_paging_list()`.
- Typed errors: one class per API error type, plus connection, timeout and signature-verification errors. Every API error carries `code`, `param`, `details`, `request_id` and the rate-limit headers.
- Webhook helpers: `construct_event`, `verify_signature`, `generate_test_header`, a discriminated event union, `UnknownEvent` for new types and `EVENT_TYPES`.
- Lenient parsing: responses that no longer match this SDK's schema still load (with a warning) instead of raising.
- `RequestOptions` (timeout, retries, correlation id, extra headers/query/body), hooks, custom `httpx` clients, `last_response` metadata and `client.request()` for raw calls.
