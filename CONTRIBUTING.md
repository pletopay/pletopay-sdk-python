# Contributing

Thanks for helping improve the Pletopay Python SDK.

## Setup

```bash
make venv      # creates .venv and installs the package with dev extras
make verify    # lint, mypy, brand and generated-code checks, unit tests, build
```

Python 3.10+ is supported; development uses the newest CPython.

## How the SDK is built

- `spec/public.v1.yaml` is a committed copy of the merchant API contract. `make sync` refreshes it from a sibling `pletopay-api` checkout (or `PLETOPAY_SPEC_PATH`).
- `make generate` writes `src/pletopay/types/_generated.py` (pydantic models), `types/_events.py` (the event union) and `src/pletopay/_operations.py` (the operation table) from the spec. Never edit generated files; `make verify` fails when they are stale.
- `src/pletopay/resources/` holds one module per resource with a sync class and an async twin. The twins must keep identical signatures: `tests/unit/test_async_client.py` compares them.
- `tests/test_spec_conformance.py` checks the operation table against the spec and that every operation has exactly one resource method whose keyword arguments cover the spec's query parameters.

## Adding or changing an operation

1. `make sync generate`.
2. Add the method to the sync and async resource classes (keyword-only parameters named after the API fields; `idempotency_key` only where the contract accepts the header).
3. Add the mapping in `scripts/generate_operations.py` (`SDK` table) if the operation is new, and regenerate.
4. Add unit tests (mock the API with `respx`, see `tests/conftest.py`) and, where it matters, a live test.
5. Add a line to `CHANGELOG.md` under *Unreleased*.
6. `make verify`.

## Style

Ruff formats and lints; mypy runs in strict mode. The brand is spelled "Pletopay"; only the protocol headers (`X-PletoPay-Signature`, `PletoPay-Version`) keep the capital P, and `make check-brand` enforces this.

## Releasing

1. Bump `version` in `pyproject.toml` and `src/pletopay/_version.py`, move the *Unreleased* changelog entries under the new version and date.
2. Tag `vX.Y.Z` and push the tag. The release workflow builds the wheel and sdist and publishes to PyPI through trusted publishing.
