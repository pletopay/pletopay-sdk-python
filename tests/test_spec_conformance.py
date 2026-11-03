"""The operation table and the resource methods must match the committed OpenAPI contract exactly."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from pletopay import OPERATIONS, AsyncPletopay, Pletopay
from pletopay.types import _generated
from pletopay.types._events import EVENT_TYPES
from tests.conftest import TEST_KEY

ROOT = Path(__file__).resolve().parent.parent
spec = yaml.safe_load((ROOT / "spec" / "public.v1.yaml").read_text())

expected: dict[str, dict] = {}
for path, item in spec["paths"].items():
    for method, op in item.items():
        if method not in ("get", "post", "patch", "delete", "put"):
            continue
        params = op.get("parameters", [])
        idem = next((p for p in params if p["in"] == "header" and p["name"] == "Idempotency-Key"), None)
        code, success = next(((c, r) for c, r in op["responses"].items() if str(c).startswith("2")), (None, {}))
        content = next(iter(success.get("content", {})), "")
        data = (
            success.get("content", {})
            .get("application/json", {})
            .get("schema", {})
            .get("properties", {})
            .get("data", {})
        )
        is_list = data.get("type") == "array"
        ref = (data.get("items", {}) if is_list else data).get("$ref", "")
        expected[op["operationId"]] = {
            "method": method.upper(),
            "path": path.removeprefix("/api/v1"),
            "idempotency": "required" if idem and idem.get("required") else "optional" if idem else "none",
            "query": tuple(p["name"].removesuffix("[]") for p in params if p["in"] == "query"),
            "is_list": is_list,
            "model": ref.rsplit("/", 1)[-1] if ref else None,
            "accept": content or "application/json",
            "test_mode_only": bool(op.get("x-test-mode-only")),
        }


def resolve(client: object, dotted: str) -> object:
    obj = client
    for part in dotted.split("."):
        obj = getattr(obj, part)
    return obj


def test_covers_every_operation_and_nothing_else() -> None:
    assert sorted(expected) == sorted(OPERATIONS)
    assert len(expected) >= 82


@pytest.mark.parametrize("op_id", sorted(expected))
def test_operation_matches_spec(op_id: str) -> None:
    op = OPERATIONS[op_id]
    exp = expected[op_id]
    assert op.id == op_id
    assert (op.method, op.path, op.idempotency, op.query, op.is_list, op.model, op.accept, op.test_mode_only) == tuple(
        exp.values()
    )
    if op.model:
        assert hasattr(_generated, op.model), f"{op.model} missing from generated models"
    sync_client = Pletopay(TEST_KEY)
    async_client = AsyncPletopay(TEST_KEY)
    assert callable(resolve(sync_client, op.sdk)), f"{op.sdk} missing on Pletopay"
    assert callable(resolve(async_client, op.sdk)), f"{op.sdk} missing on AsyncPletopay"


def test_one_method_per_operation() -> None:
    methods = [op.sdk for op in OPERATIONS.values()]
    assert len(set(methods)) == len(methods)


def test_query_parameters_are_keyword_arguments() -> None:
    """Every query parameter in the spec is a keyword argument of the SDK method (and nothing extra, bar options)."""
    import inspect

    client = Pletopay(TEST_KEY)
    for op in OPERATIONS.values():
        if not op.query:
            continue
        sig = inspect.signature(resolve(client, op.sdk))  # type: ignore[arg-type]
        kwargs = {n for n, p in sig.parameters.items() if p.kind is inspect.Parameter.KEYWORD_ONLY}
        missing = set(op.query) - kwargs
        assert not missing, f"{op.sdk} lacks query parameters {missing}"


def test_event_types_match_spec() -> None:
    assert list(EVENT_TYPES) == sorted(spec["webhooks"])
