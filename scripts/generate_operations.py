#!/usr/bin/env python
"""Writes src/pletopay/_operations.py from spec/public.v1.yaml: one entry per operation (method, path,
idempotency, query parameters, list-ness, response type, test-mode-only) and the SDK method that
implements it. tests/test_spec_conformance.py checks the result against the spec.

    python scripts/generate_operations.py          write
    python scripts/generate_operations.py --check  fail when stale
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "spec" / "public.v1.yaml"
OUT = ROOT / "src" / "pletopay" / "_operations.py"

SDK = {
    "createCustomer": "customers.create",
    "listCustomers": "customers.list",
    "getCustomer": "customers.retrieve",
    "updateCustomer": "customers.update",
    "setCustomerRiskStatus": "customers.set_risk_status",
    "createPayment": "payments.create",
    "listPayments": "payments.list",
    "getPayment": "payments.retrieve",
    "getPaymentByReference": "payments.retrieve_by_reference",
    "createVirtualAccount": "virtual_accounts.create",
    "listVirtualAccounts": "virtual_accounts.list",
    "getVirtualAccount": "virtual_accounts.retrieve",
    "getVirtualAccountByReference": "virtual_accounts.retrieve_by_reference",
    "closeVirtualAccount": "virtual_accounts.close",
    "createSubaccount": "subaccounts.create",
    "listSubaccounts": "subaccounts.list",
    "getSubaccount": "subaccounts.retrieve",
    "updateSubaccount": "subaccounts.update",
    "getSubaccountBalance": "subaccounts.retrieve_balance",
    "createSplitRule": "split_rules.create",
    "listSplitRules": "split_rules.list",
    "getSplitRule": "split_rules.retrieve",
    "updateSplitRule": "split_rules.update",
    "createTransfer": "transfers.create",
    "listTransfers": "transfers.list",
    "getTransfer": "transfers.retrieve",
    "getTransferByReference": "transfers.retrieve_by_reference",
    "resolveAccount": "transfers.resolve_account",
    "listBanks": "banks.list",
    "listSettlements": "settlements.list",
    "getSettlement": "settlements.retrieve",
    "listSettlementItems": "settlements.list_items",
    "createRefund": "refunds.create",
    "listRefunds": "refunds.list",
    "getRefund": "refunds.retrieve",
    "getRefundByReference": "refunds.retrieve_by_reference",
    "createCheckoutSession": "checkout.sessions.create",
    "listCheckoutSessions": "checkout.sessions.list",
    "getCheckoutSession": "checkout.sessions.retrieve",
    "getCheckoutSessionByReference": "checkout.sessions.retrieve_by_reference",
    "expireCheckoutSession": "checkout.sessions.expire",
    "createPaymentLink": "payment_links.create",
    "listPaymentLinks": "payment_links.list",
    "getPaymentLink": "payment_links.retrieve",
    "updatePaymentLink": "payment_links.update",
    "createInvoice": "invoices.create",
    "listInvoices": "invoices.list",
    "getInvoice": "invoices.retrieve",
    "updateInvoice": "invoices.update",
    "finalizeInvoice": "invoices.finalize",
    "voidInvoice": "invoices.void",
    "markInvoiceUncollectible": "invoices.mark_uncollectible",
    "listRiskEvents": "risk.list_events",
    "getRiskLimits": "risk.retrieve_limits",
    "createPlan": "plans.create",
    "listPlans": "plans.list",
    "getPlan": "plans.retrieve",
    "updatePlan": "plans.update",
    "createSubscription": "subscriptions.create",
    "listSubscriptions": "subscriptions.list",
    "getSubscription": "subscriptions.retrieve",
    "cancelSubscription": "subscriptions.cancel",
    "createReport": "reports.create",
    "listReports": "reports.list",
    "getReport": "reports.retrieve",
    "downloadReport": "reports.download",
    "getStatement": "reports.statement",
    "createWebhookEndpoint": "webhook_endpoints.create",
    "listWebhookEndpoints": "webhook_endpoints.list",
    "getWebhookEndpoint": "webhook_endpoints.retrieve",
    "updateWebhookEndpoint": "webhook_endpoints.update",
    "deleteWebhookEndpoint": "webhook_endpoints.delete",
    "rotateWebhookSecret": "webhook_endpoints.rotate_secret",
    "testWebhookEndpoint": "webhook_endpoints.test",
    "listEndpointDeliveries": "webhook_endpoints.list_deliveries",
    "listEvents": "events.list",
    "getEvent": "events.retrieve",
    "listEventDeliveries": "events.list_deliveries",
    "replayEvent": "events.replay",
    "getBalance": "balance.retrieve",
    "listTransactions": "transactions.list",
    "simulateTransfer": "sandbox.simulate_transfer",
}


def snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).upper()


def build() -> str:
    spec = yaml.safe_load(SPEC.read_text())
    entries: list[str] = []
    names: list[tuple[str, str]] = []
    for path, item in spec["paths"].items():
        for method, op in item.items():
            if method not in ("get", "post", "patch", "delete", "put"):
                continue
            op_id = op["operationId"]
            if op_id not in SDK:
                raise SystemExit(f"generate: no SDK mapping for {op_id}")
            params = op.get("parameters", [])
            idem = next((p for p in params if p["in"] == "header" and p["name"] == "Idempotency-Key"), None)
            idempotency = "required" if idem and idem.get("required") else "optional" if idem else "none"
            query = [p["name"].removesuffix("[]") for p in params if p["in"] == "query"]
            _code, success = next(((c, r) for c, r in op["responses"].items() if str(c).startswith("2")), (None, {}))
            content = next(iter(success.get("content", {})), "")
            schema = success.get("content", {}).get("application/json", {}).get("schema", {})
            data = schema.get("properties", {}).get("data", {})
            is_list = data.get("type") == "array"
            ref = (data.get("items", {}) if is_list else data).get("$ref", "")
            model = ref.rsplit("/", 1)[-1] if ref else None
            const = snake(op_id)
            names.append((const, op_id))
            entries.append(
                f"{const} = Operation(\n"
                f"    id={op_id!r},\n    method={method.upper()!r},\n    path={path.removeprefix('/api/v1')!r},\n"
                f"    idempotency={idempotency!r},\n    sdk={SDK[op_id]!r},\n    query={tuple(query)!r},\n"
                f"    is_list={is_list},\n    model={model!r},\n    accept={(content or 'application/json')!r},\n"
                f"    test_mode_only={bool(op.get('x-test-mode-only'))},\n)\n"
            )
    table = (
        "OPERATIONS: dict[str, Operation] = {\n"
        + "".join(f"    {op_id!r}: {const},\n" for const, op_id in names)
        + "}\n"
    )
    return (
        '"""Every merchant API operation, generated from spec/public.v1.yaml by scripts/generate_operations.py. Do not edit."""\n\n'
        "from __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom typing import Literal\n\n"
        "Idempotency = Literal['none', 'optional', 'required']\n\n\n"
        "@dataclass(frozen=True)\nclass Operation:\n"
        "    id: str\n    method: str\n    path: str\n    idempotency: Idempotency\n    sdk: str\n"
        "    query: tuple[str, ...]\n    is_list: bool\n    model: str | None\n    accept: str\n    test_mode_only: bool\n\n\n"
        + "".join(entries)
        + "\n"
        + table
    )


def formatted(content: str) -> str:
    """Runs the generated source through ruff so the committed file is stable under `--check`."""
    import subprocess

    result = subprocess.run(
        [sys.executable, "-m", "ruff", "format", "-", "--stdin-filename", "_operations.py"],
        input=content,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def main() -> None:
    content = formatted(build())
    current = OUT.read_text() if OUT.exists() else None
    if "--check" in sys.argv:
        if current != content:
            raise SystemExit(
                "generate: src/pletopay/_operations.py is stale. Run `python scripts/generate_operations.py`."
            )
        print("operations: up to date")
        return
    if current != content:
        OUT.write_text(content)
        print(f"operations: wrote {OUT.relative_to(ROOT)}")
    else:
        print("operations: unchanged")


if __name__ == "__main__":
    main()
