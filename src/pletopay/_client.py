"""The HTTP clients: :class:`Pletopay` (sync, ``httpx.Client``) and :class:`AsyncPletopay`.

Both share the request building, retry policy and response parsing in :class:`_BaseClient`; the
resource classes in :mod:`pletopay.resources` are thin wrappers over ``_call``/``_list``.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import platform
import re
import time
import warnings
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal, TypeVar

import httpx
from pydantic import ValidationError

from pletopay import _constants as c
from pletopay._idempotency import assert_idempotency_key, generate_idempotency_key
from pletopay._lenient import construct_lenient
from pletopay._operations import Operation
from pletopay._pagination import AsyncPage, SyncPage
from pletopay._query import encode_query
from pletopay._response import ListMeta, RawResponse, ResponseInfo
from pletopay._retry import in_progress_delay, is_in_progress, is_retryable_status, retry_delay
from pletopay._version import __version__
from pletopay.errors import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    PletopayError,
    rate_limit_from_headers,
    retry_after_seconds,
)
from pletopay.types import _generated
from pletopay.types._base import PletopayModel
from pletopay.types._events import SPEC_API_VERSION
from pletopay.webhook import Webhook

if TYPE_CHECKING:
    from pletopay.resources import (
        AsyncBalance,
        AsyncBanks,
        AsyncCheckout,
        AsyncCustomers,
        AsyncEvents,
        AsyncInvoices,
        AsyncPaymentLinks,
        AsyncPayments,
        AsyncPlans,
        AsyncRefunds,
        AsyncReports,
        AsyncRisk,
        AsyncSandbox,
        AsyncSettlements,
        AsyncSplitRules,
        AsyncSubaccounts,
        AsyncSubscriptions,
        AsyncTransactions,
        AsyncTransfers,
        AsyncVirtualAccounts,
        AsyncWebhookEndpoints,
        Balance,
        Banks,
        Checkout,
        Customers,
        Events,
        Invoices,
        PaymentLinks,
        Payments,
        Plans,
        Refunds,
        Reports,
        Risk,
        Sandbox,
        Settlements,
        SplitRules,
        Subaccounts,
        Subscriptions,
        Transactions,
        Transfers,
        VirtualAccounts,
        WebhookEndpoints,
    )

M = TypeVar("M", bound=PletopayModel)
Mode = Literal["test", "live"]
_SECRET_KEY = re.compile(r"^sk_(test|live)_[A-Za-z0-9_]+$")
_log = logging.getLogger("pletopay")


@dataclass
class RequestOptions:
    """Per-call options accepted by every resource method (``options=RequestOptions(...)``).

    ``timeout`` overrides the client's timeout and the 90 s default of ``transfers.create`` / ``refunds.create``.
    """

    timeout: float | None = None
    max_retries: int | None = None
    correlation_id: str | None = None
    api_version: str | None = None
    headers: Mapping[str, str] | None = None
    extra_query: Mapping[str, Any] | None = None
    extra_body: Mapping[str, Any] | None = None


@dataclass
class Hooks:
    """Observability callbacks. Headers passed to them have ``authorization`` redacted."""

    on_request: Callable[[dict[str, Any]], None] | None = None
    on_response: Callable[[dict[str, Any]], None] | None = None
    on_retry: Callable[[dict[str, Any]], None] | None = None


@dataclass
class _Prepared:
    method: str
    url: str
    params: list[tuple[str, Any]]
    headers: dict[str, str]
    content: bytes | None
    timeout: float
    max_retries: int
    retryable: bool
    idempotency_key: str | None
    accept: str
    path: str

    @property
    def redacted_headers(self) -> dict[str, str]:
        return {k: ("Bearer sk_***" if k.lower() == "authorization" else v) for k, v in self.headers.items()}


@dataclass
class _Outcome:
    data: Any
    info: ResponseInfo
    error: APIError | None = field(default=None)


class _BaseClient:
    API_VERSION: str = SPEC_API_VERSION
    DEFAULT_BASE_URL = c.DEFAULT_BASE_URL

    def __init__(
        self,
        *,
        secret_key: str | None,
        base_url: str | None,
        api_version: str | Literal[False] | None,
        timeout: float | None,
        max_retries: int,
        correlation_id: str | Callable[[], str] | None,
        webhook_secret: str | None,
        webhook_tolerance: int,
        hooks: Hooks | None,
        app_info: Mapping[str, str] | None,
    ) -> None:
        key = secret_key or os.environ.get(c.ENV_SECRET_KEY)
        if not key:
            raise PletopayError(
                "No secret key. Pass secret_key= or set PLETOPAY_SECRET_KEY (Dashboard → Settings → Developers → API keys)."
            )
        if key.startswith("pk_"):
            raise PletopayError(
                "A publishable key (pk_…) cannot call the API. Use your secret key (sk_test_… / sk_live_…) on the server only."
            )
        if not _SECRET_KEY.match(key):
            raise PletopayError("The secret key must look like sk_test_… or sk_live_…")
        if not isinstance(max_retries, int) or max_retries < 0:
            raise PletopayError("max_retries must be a non-negative integer")
        if timeout is not None and (not timeout or timeout <= 0):
            raise PletopayError("timeout must be a positive number of seconds")
        self._secret_key = key
        self.mode: Mode = "live" if key.startswith("sk_live_") else "test"
        self.base_url = (base_url or os.environ.get(c.ENV_API_URL) or c.DEFAULT_BASE_URL).rstrip("/")
        # api_version: None → the SDK's pinned version; False → send none (the organization's pin applies).
        self.api_version: str | None = SPEC_API_VERSION if api_version is None else (api_version or None)
        self.timeout = c.DEFAULT_TIMEOUT_SECONDS if timeout is None else timeout
        # A timeout the caller chose also overrides the per-operation defaults.
        self._timeout_is_explicit = timeout is not None
        self.max_retries = max_retries
        self._correlation_id = correlation_id
        self._hooks = hooks or Hooks()
        app = ""
        if app_info:
            app = f" {app_info.get('name', 'app')}"
            if app_info.get("version"):
                app += f"/{app_info['version']}"
            if app_info.get("url"):
                app += f" ({app_info['url']})"
        self.user_agent = (
            f"pletopay-python/{__version__} python/{platform.python_version()} httpx/{httpx.__version__}{app}"
        )
        self.webhooks = Webhook(webhook_secret or os.environ.get(c.ENV_WEBHOOK_SECRET), tolerance=webhook_tolerance)

    # ───────────── request building ─────────────

    def _prepare(
        self,
        method: str,
        path: str,
        *,
        query: Mapping[str, Any] | None,
        body: Mapping[str, Any] | None,
        idempotency: str,
        idempotency_key: str | None,
        options: RequestOptions | None,
        accept: str,
        test_mode_only: bool,
        default_timeout: float | None = None,
    ) -> _Prepared:
        options = options or RequestOptions()
        if test_mode_only and self.mode == "live":
            raise PletopayError(f"{method} {path} is only available in test mode (use an sk_test_ key)")
        key: str | None = None
        if idempotency_key is not None:
            key = assert_idempotency_key(idempotency_key)
        elif idempotency != "none":
            key = generate_idempotency_key()
        headers: dict[str, str] = {
            "accept": accept,
            "user-agent": self.user_agent,
        }
        api_version = options.api_version or self.api_version
        if api_version:
            headers["pletopay-version"] = api_version
        if key is not None:
            headers["idempotency-key"] = key
        correlation = options.correlation_id or (
            self._correlation_id() if callable(self._correlation_id) else self._correlation_id
        )
        if correlation:
            headers["x-correlation-id"] = correlation
        for name, value in (options.headers or {}).items():
            if name.lower() != "authorization":
                headers[name] = value
        headers["authorization"] = f"Bearer {self._secret_key}"
        content: bytes | None = None
        if body is not None or options.extra_body:
            merged = {**(body or {}), **(options.extra_body or {})}
            content = json.dumps(merged, separators=(",", ":"), ensure_ascii=False, default=_json_default).encode(
                "utf-8"
            )
            headers["content-type"] = "application/json"
        params = encode_query({**(query or {}), **(options.extra_query or {})})
        max_retries = self.max_retries if options.max_retries is None else options.max_retries
        if options.timeout is not None:
            timeout = options.timeout
        elif default_timeout is not None and not self._timeout_is_explicit:
            timeout = default_timeout
        else:
            timeout = self.timeout
        return _Prepared(
            method=method,
            url=f"{self.base_url}{path}",
            params=params,
            headers=headers,
            content=content,
            timeout=timeout,
            max_retries=max_retries,
            retryable=method in ("GET", "DELETE") or key is not None,
            idempotency_key=key,
            accept=accept,
            path=path,
        )

    @staticmethod
    def _default_timeout(op: Operation) -> float | None:
        return c.MONEY_OUT_TIMEOUT_SECONDS if op.id in c.MONEY_OUT_OPERATIONS else None

    @staticmethod
    def _fill_path(template: str, params: Mapping[str, str] | None) -> str:
        from urllib.parse import quote

        def sub(match: re.Match[str]) -> str:
            name = match.group(1)
            value = (params or {}).get(name)
            if not isinstance(value, str) or not value:
                raise PletopayError(f"{name} is required and must be a non-empty string")
            return quote(value, safe="")

        return re.sub(r"\{(\w+)\}", sub, template)

    # ───────────── response handling ─────────────

    def _outcome(self, prepared: _Prepared, response: httpx.Response) -> _Outcome:
        headers = response.headers
        request_id = headers.get("x-request-id")
        info_kwargs: dict[str, Any] = {
            "status_code": response.status_code,
            "headers": headers,
            "request_id": request_id,
            "api_version": headers.get("pletopay-version"),
            "idempotency_key": prepared.idempotency_key,
            "idempotent_replayed": headers.get("idempotent-replayed") == "true",
            "rate_limit": rate_limit_from_headers(headers),
            "deprecation": headers.get("deprecation"),
            "sunset": headers.get("sunset"),
        }
        if response.is_success:
            if prepared.accept == "text/csv":
                return _Outcome(response.text, ResponseInfo(message="OK", meta=None, **info_kwargs))
            body = _parse_json(response)
            if isinstance(body, dict) and "status" in body and "data" in body:
                meta_raw = body.get("meta")
                meta = (
                    ListMeta(
                        has_more=bool(meta_raw.get("has_more")),
                        next_cursor=meta_raw.get("next_cursor"),
                        url=str(meta_raw.get("url", "")),
                    )
                    if isinstance(meta_raw, dict) and "has_more" in meta_raw
                    else None
                )
                message = body.get("message")
                info = ResponseInfo(message=message if isinstance(message, str) else "", meta=meta, **info_kwargs)
                return _Outcome(body["data"], info)
            error = APIError(response.status_code, body, headers, "The API returned an unexpected response body")
        else:
            error = APIError.from_response(response.status_code, _parse_json(response), headers)
        error.idempotency_key = prepared.idempotency_key
        return _Outcome(None, ResponseInfo(message="", meta=None, **info_kwargs), error)

    @staticmethod
    def _retry_decision(
        prepared: _Prepared, retries: int, error: APIError, headers: httpx.Headers, elapsed: float
    ) -> tuple[float, int] | None:
        """The wait before the next attempt and the retries spent once it is made, or ``None`` to raise.

        ``elapsed`` is the time since the first attempt of the call started.
        """
        retry_after = retry_after_seconds(headers)
        if (
            is_in_progress(error.status_code, error.code)
            and prepared.idempotency_key is not None
            and prepared.max_retries > 0
        ):
            # The first attempt is still running on the API (a slow bank, usually): keep asking with the
            # same key until it answers or the wait runs out. This does not spend the retry budget.
            wait = in_progress_delay(elapsed, retry_after=retry_after)
            return None if wait is None else (wait, retries)
        if not prepared.retryable or retries >= prepared.max_retries:
            return None
        if not is_retryable_status(error.status_code, error.code):
            return None
        return retry_delay(retries, retry_after=retry_after), retries + 1

    @staticmethod
    def _transport_error(prepared: _Prepared, exc: Exception) -> APIConnectionError:
        error: APIConnectionError
        if isinstance(exc, httpx.TimeoutException):
            error = APITimeoutError(f"{prepared.method} {prepared.path} timed out after {prepared.timeout} s")
        else:
            error = APIConnectionError(f"{prepared.method} {prepared.path} failed: {exc}")
        error.idempotency_key = prepared.idempotency_key
        return error

    def _emit(self, hook: Callable[[dict[str, Any]], None] | None, payload: dict[str, Any]) -> None:
        if hook is not None:
            hook(payload)

    @staticmethod
    def _model(name: str | None) -> type[PletopayModel] | None:
        return getattr(_generated, name) if name else None

    @staticmethod
    def _to_model(model: type[M], data: Any, info: ResponseInfo) -> M:
        if not isinstance(data, dict):
            error = APIError(info.status_code, data, info.headers, f"Expected an object for {model.__name__}")
            error.idempotency_key = info.idempotency_key
            raise error
        try:
            obj = model.model_validate(data)
        except ValidationError as exc:
            # The API changed in a way this SDK version does not describe: keep going with the raw data.
            warnings.warn(
                f"pletopay: {model.__name__} did not match this SDK's schema ({exc.error_count()} issue(s)); "
                "update the SDK. Fields are available via dict access.",
                stacklevel=2,
            )
            obj = construct_lenient(model, data)
        obj._last_response = info
        return obj

    @classmethod
    def _materialise(cls, op: Operation, data: Any, info: ResponseInfo) -> Any:
        model = cls._model(op.model)
        if op.is_list:
            items = data if isinstance(data, list) else []
            return [cls._to_model(model, item, info) if model else item for item in items]
        if model is None or data is None:
            return data
        return cls._to_model(model, data, info)


def _json_default(value: Any) -> Any:
    from datetime import datetime, timezone

    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _parse_json(response: httpx.Response) -> Any:
    text = response.text
    if not text:
        return None
    try:
        return response.json()
    except ValueError:
        return text


def _is_backward(query: Mapping[str, Any] | None) -> bool:
    """A list that starts with ``ending_before`` walks towards newer items and continues with ``ending_before``
    too; every other list continues with ``starting_after``."""
    return isinstance((query or {}).get("ending_before"), str)


def _next_query(query: Mapping[str, Any] | None, cursor: str, backward: bool) -> dict[str, Any]:
    if backward:
        return {**(query or {}), "ending_before": cursor, "starting_after": None}
    return {**(query or {}), "starting_after": cursor, "ending_before": None}


def _build(client: httpx.Client | httpx.AsyncClient, prepared: _Prepared) -> httpx.Request:
    return client.build_request(
        prepared.method,
        prepared.url,
        params=prepared.params or None,
        headers=prepared.headers,
        content=prepared.content,
        timeout=prepared.timeout,
    )


class Pletopay(_BaseClient):
    """Synchronous client.

    >>> pletopay = Pletopay(secret_key="sk_test_…")
    >>> payment = pletopay.payments.create(amount=5000000, currency="NGN", reference="ORDER-1")

    Args:
        secret_key: ``sk_test_…`` or ``sk_live_…``. Defaults to ``PLETOPAY_SECRET_KEY``.
        base_url: Defaults to ``PLETOPAY_API_URL``, then ``https://api.pletopay.com``.
        api_version: Dated ``PletoPay-Version`` to send. Defaults to the version this SDK's types describe
            (``Pletopay.API_VERSION``); ``False`` sends none so your organization's pin applies.
        timeout: Per-request timeout in seconds. Default 30, and 90 for the calls that pay out inline
            (``transfers.create``, ``refunds.create``); a value set here applies to every call.
        max_retries: Automatic retries of safe requests on network errors, 429 and 5xx (default 2).
        http_client: Your own ``httpx.Client`` (proxies, custom transports, instrumentation).
        webhook_secret: ``whsec_…`` for ``pletopay.webhooks.construct_event``; defaults to ``PLETOPAY_WEBHOOK_SECRET``.
    """

    customers: Customers
    payments: Payments
    virtual_accounts: VirtualAccounts
    subaccounts: Subaccounts
    split_rules: SplitRules
    transfers: Transfers
    banks: Banks
    settlements: Settlements
    refunds: Refunds
    checkout: Checkout
    payment_links: PaymentLinks
    invoices: Invoices
    risk: Risk
    plans: Plans
    subscriptions: Subscriptions
    reports: Reports
    webhook_endpoints: WebhookEndpoints
    events: Events
    balance: Balance
    transactions: Transactions
    sandbox: Sandbox

    def __init__(
        self,
        secret_key: str | None = None,
        *,
        base_url: str | None = None,
        api_version: str | Literal[False] | None = None,
        timeout: float | None = None,
        max_retries: int = c.DEFAULT_MAX_RETRIES,
        http_client: httpx.Client | None = None,
        correlation_id: str | Callable[[], str] | None = None,
        webhook_secret: str | None = None,
        webhook_tolerance: int = 300,
        hooks: Hooks | None = None,
        app_info: Mapping[str, str] | None = None,
    ) -> None:
        super().__init__(
            secret_key=secret_key,
            base_url=base_url,
            api_version=api_version,
            timeout=timeout,
            max_retries=max_retries,
            correlation_id=correlation_id,
            webhook_secret=webhook_secret,
            webhook_tolerance=webhook_tolerance,
            hooks=hooks,
            app_info=app_info,
        )
        self._http = http_client or httpx.Client(timeout=self.timeout)
        self._owns_http = http_client is None
        from pletopay.resources import bind_sync

        bind_sync(self)

    def close(self) -> None:
        if self._owns_http:
            self._http.close()

    def __enter__(self) -> Pletopay:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def request(
        self,
        method: str,
        path: str,
        *,
        query: Mapping[str, Any] | None = None,
        body: Mapping[str, Any] | None = None,
        idempotency: Literal["none", "optional", "required"] = "none",
        idempotency_key: str | None = None,
        options: RequestOptions | None = None,
        accept: str = "application/json",
        test_mode_only: bool = False,
    ) -> RawResponse:
        """Sends one request and returns the unwrapped ``data`` plus the response metadata.

        ``path`` is relative to the base URL (e.g. ``/api/v1/payments``). Use it for endpoints newer
        than this SDK; the resource methods wrap it.
        """
        prepared = self._prepare(
            method.upper(),
            path,
            query=query,
            body=body,
            idempotency=idempotency,
            idempotency_key=idempotency_key,
            options=options,
            accept=accept,
            test_mode_only=test_mode_only,
        )
        outcome = self._send(prepared)
        return RawResponse(outcome.data, outcome.info)

    def _send(self, prepared: _Prepared) -> _Outcome:
        # `attempt` counts requests sent, `retries` the retry budget spent: waiting for a request that is
        # still in progress sends more requests without spending any.
        attempt = retries = 0
        call_started = time.monotonic()
        while True:
            started = time.monotonic()
            self._emit(
                self._hooks.on_request,
                {
                    "method": prepared.method,
                    "url": prepared.url,
                    "headers": prepared.redacted_headers,
                    "attempt": attempt,
                },
            )
            _log.debug("pletopay: %s %s (attempt %s)", prepared.method, prepared.path, attempt)
            try:
                response = self._http.send(_build(self._http, prepared))
            except httpx.TransportError as exc:
                error = self._transport_error(prepared, exc)
                if prepared.retryable and retries < prepared.max_retries:
                    delay = retry_delay(retries)
                    self._emit(
                        self._hooks.on_retry, {"attempt": attempt, "reason": type(error).__name__, "delay": delay}
                    )
                    _log.warning(
                        "pletopay: retrying %s %s after %s", prepared.method, prepared.path, type(error).__name__
                    )
                    time.sleep(delay)
                    attempt += 1
                    retries += 1
                    continue
                raise error from exc
            outcome = self._outcome(prepared, response)
            self._emit(
                self._hooks.on_response,
                {
                    "method": prepared.method,
                    "url": prepared.url,
                    "status_code": response.status_code,
                    "request_id": outcome.info.request_id,
                    "duration": time.monotonic() - started,
                    "attempt": attempt,
                },
            )
            if outcome.error is None:
                return outcome
            decision = self._retry_decision(
                prepared, retries, outcome.error, response.headers, time.monotonic() - call_started
            )
            if decision is None:
                raise outcome.error
            delay, retries = decision
            self._emit(
                self._hooks.on_retry,
                {
                    "attempt": attempt,
                    "reason": "status",
                    "status_code": response.status_code,
                    "code": outcome.error.code,
                    "delay": delay,
                },
            )
            _log.warning("pletopay: retrying %s %s after HTTP %s", prepared.method, prepared.path, response.status_code)
            time.sleep(delay)
            attempt += 1

    def _call(
        self,
        op: Operation,
        model: type[M],
        *,
        path_params: Mapping[str, str] | None = None,
        query: Mapping[str, Any] | None = None,
        body: Mapping[str, Any] | None = None,
        idempotency_key: str | None = None,
        options: RequestOptions | None = None,
    ) -> M:
        obj: M = self._call_any(
            op, path_params=path_params, query=query, body=body, idempotency_key=idempotency_key, options=options
        )
        return obj

    def _call_any(
        self,
        op: Operation,
        *,
        path_params: Mapping[str, str] | None = None,
        query: Mapping[str, Any] | None = None,
        body: Mapping[str, Any] | None = None,
        idempotency_key: str | None = None,
        options: RequestOptions | None = None,
    ) -> Any:
        prepared = self._prepare(
            op.method,
            f"/api/v1{self._fill_path(op.path, path_params)}",
            query=query,
            body=body,
            idempotency=op.idempotency,
            idempotency_key=idempotency_key,
            options=options,
            accept=op.accept,
            test_mode_only=op.test_mode_only,
            default_timeout=self._default_timeout(op),
        )
        outcome = self._send(prepared)
        return self._materialise(op, outcome.data, outcome.info)

    def _list(
        self,
        op: Operation,
        model: type[M],
        *,
        path_params: Mapping[str, str] | None = None,
        query: Mapping[str, Any] | None = None,
        body: Mapping[str, Any] | None = None,
        idempotency_key: str | None = None,
        options: RequestOptions | None = None,
    ) -> SyncPage[M]:
        backward = _is_backward(query)

        def fetch(q: Mapping[str, Any] | None) -> SyncPage[M]:
            prepared = self._prepare(
                op.method,
                f"/api/v1{self._fill_path(op.path, path_params)}",
                query=q,
                body=body,
                idempotency=op.idempotency,
                idempotency_key=idempotency_key,
                options=options,
                accept=op.accept,
                test_mode_only=op.test_mode_only,
            )
            outcome = self._send(prepared)
            items: list[M] = self._materialise(op, outcome.data, outcome.info)
            return SyncPage(
                items, outcome.info, lambda cursor: fetch(_next_query(q, cursor, backward)), backward=backward
            )

        return fetch(query)


class AsyncPletopay(_BaseClient):
    """Asynchronous client with the same resources and options as :class:`Pletopay`.

    >>> async with AsyncPletopay() as pletopay:
    ...     balance = await pletopay.balance.retrieve()
    """

    customers: AsyncCustomers
    payments: AsyncPayments
    virtual_accounts: AsyncVirtualAccounts
    subaccounts: AsyncSubaccounts
    split_rules: AsyncSplitRules
    transfers: AsyncTransfers
    banks: AsyncBanks
    settlements: AsyncSettlements
    refunds: AsyncRefunds
    checkout: AsyncCheckout
    payment_links: AsyncPaymentLinks
    invoices: AsyncInvoices
    risk: AsyncRisk
    plans: AsyncPlans
    subscriptions: AsyncSubscriptions
    reports: AsyncReports
    webhook_endpoints: AsyncWebhookEndpoints
    events: AsyncEvents
    balance: AsyncBalance
    transactions: AsyncTransactions
    sandbox: AsyncSandbox

    def __init__(
        self,
        secret_key: str | None = None,
        *,
        base_url: str | None = None,
        api_version: str | Literal[False] | None = None,
        timeout: float | None = None,
        max_retries: int = c.DEFAULT_MAX_RETRIES,
        http_client: httpx.AsyncClient | None = None,
        correlation_id: str | Callable[[], str] | None = None,
        webhook_secret: str | None = None,
        webhook_tolerance: int = 300,
        hooks: Hooks | None = None,
        app_info: Mapping[str, str] | None = None,
    ) -> None:
        super().__init__(
            secret_key=secret_key,
            base_url=base_url,
            api_version=api_version,
            timeout=timeout,
            max_retries=max_retries,
            correlation_id=correlation_id,
            webhook_secret=webhook_secret,
            webhook_tolerance=webhook_tolerance,
            hooks=hooks,
            app_info=app_info,
        )
        self._http = http_client or httpx.AsyncClient(timeout=self.timeout)
        self._owns_http = http_client is None
        from pletopay.resources import bind_async

        bind_async(self)

    async def close(self) -> None:
        if self._owns_http:
            await self._http.aclose()

    async def __aenter__(self) -> AsyncPletopay:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    async def request(
        self,
        method: str,
        path: str,
        *,
        query: Mapping[str, Any] | None = None,
        body: Mapping[str, Any] | None = None,
        idempotency: Literal["none", "optional", "required"] = "none",
        idempotency_key: str | None = None,
        options: RequestOptions | None = None,
        accept: str = "application/json",
        test_mode_only: bool = False,
    ) -> RawResponse:
        prepared = self._prepare(
            method.upper(),
            path,
            query=query,
            body=body,
            idempotency=idempotency,
            idempotency_key=idempotency_key,
            options=options,
            accept=accept,
            test_mode_only=test_mode_only,
        )
        outcome = await self._send(prepared)
        return RawResponse(outcome.data, outcome.info)

    async def _send(self, prepared: _Prepared) -> _Outcome:
        # `attempt` counts requests sent, `retries` the retry budget spent: waiting for a request that is
        # still in progress sends more requests without spending any.
        attempt = retries = 0
        call_started = time.monotonic()
        while True:
            started = time.monotonic()
            self._emit(
                self._hooks.on_request,
                {
                    "method": prepared.method,
                    "url": prepared.url,
                    "headers": prepared.redacted_headers,
                    "attempt": attempt,
                },
            )
            _log.debug("pletopay: %s %s (attempt %s)", prepared.method, prepared.path, attempt)
            try:
                response = await self._http.send(_build(self._http, prepared))
            except httpx.TransportError as exc:
                error = self._transport_error(prepared, exc)
                if prepared.retryable and retries < prepared.max_retries:
                    delay = retry_delay(retries)
                    self._emit(
                        self._hooks.on_retry, {"attempt": attempt, "reason": type(error).__name__, "delay": delay}
                    )
                    _log.warning(
                        "pletopay: retrying %s %s after %s", prepared.method, prepared.path, type(error).__name__
                    )
                    await asyncio.sleep(delay)
                    attempt += 1
                    retries += 1
                    continue
                raise error from exc
            outcome = self._outcome(prepared, response)
            self._emit(
                self._hooks.on_response,
                {
                    "method": prepared.method,
                    "url": prepared.url,
                    "status_code": response.status_code,
                    "request_id": outcome.info.request_id,
                    "duration": time.monotonic() - started,
                    "attempt": attempt,
                },
            )
            if outcome.error is None:
                return outcome
            decision = self._retry_decision(
                prepared, retries, outcome.error, response.headers, time.monotonic() - call_started
            )
            if decision is None:
                raise outcome.error
            delay, retries = decision
            self._emit(
                self._hooks.on_retry,
                {
                    "attempt": attempt,
                    "reason": "status",
                    "status_code": response.status_code,
                    "code": outcome.error.code,
                    "delay": delay,
                },
            )
            _log.warning("pletopay: retrying %s %s after HTTP %s", prepared.method, prepared.path, response.status_code)
            await asyncio.sleep(delay)
            attempt += 1

    async def _call(
        self,
        op: Operation,
        model: type[M],
        *,
        path_params: Mapping[str, str] | None = None,
        query: Mapping[str, Any] | None = None,
        body: Mapping[str, Any] | None = None,
        idempotency_key: str | None = None,
        options: RequestOptions | None = None,
    ) -> M:
        obj: M = await self._call_any(
            op, path_params=path_params, query=query, body=body, idempotency_key=idempotency_key, options=options
        )
        return obj

    async def _call_any(
        self,
        op: Operation,
        *,
        path_params: Mapping[str, str] | None = None,
        query: Mapping[str, Any] | None = None,
        body: Mapping[str, Any] | None = None,
        idempotency_key: str | None = None,
        options: RequestOptions | None = None,
    ) -> Any:
        prepared = self._prepare(
            op.method,
            f"/api/v1{self._fill_path(op.path, path_params)}",
            query=query,
            body=body,
            idempotency=op.idempotency,
            idempotency_key=idempotency_key,
            options=options,
            accept=op.accept,
            test_mode_only=op.test_mode_only,
            default_timeout=self._default_timeout(op),
        )
        outcome = await self._send(prepared)
        return self._materialise(op, outcome.data, outcome.info)

    async def _list(
        self,
        op: Operation,
        model: type[M],
        *,
        path_params: Mapping[str, str] | None = None,
        query: Mapping[str, Any] | None = None,
        body: Mapping[str, Any] | None = None,
        idempotency_key: str | None = None,
        options: RequestOptions | None = None,
    ) -> AsyncPage[M]:
        backward = _is_backward(query)

        async def fetch(q: Mapping[str, Any] | None) -> AsyncPage[M]:
            prepared = self._prepare(
                op.method,
                f"/api/v1{self._fill_path(op.path, path_params)}",
                query=q,
                body=body,
                idempotency=op.idempotency,
                idempotency_key=idempotency_key,
                options=options,
                accept=op.accept,
                test_mode_only=op.test_mode_only,
            )
            outcome = await self._send(prepared)
            items: list[M] = self._materialise(op, outcome.data, outcome.info)

            async def next_page(cursor: str) -> AsyncPage[M]:
                return await fetch(_next_query(q, cursor, backward))

            return AsyncPage(items, outcome.info, next_page, backward=backward)

        return await fetch(query)
