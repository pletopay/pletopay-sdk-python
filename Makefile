# Development entry points. `make verify` is what CI runs.
PY ?= .venv/bin/python
RUFF ?= .venv/bin/ruff
MYPY ?= .venv/bin/mypy
PYTEST ?= .venv/bin/pytest

.PHONY: venv sync generate lint format typecheck test test-live check-brand build verify clean

venv:
	python3 -m venv .venv && .venv/bin/pip install --upgrade pip && .venv/bin/pip install -e ".[dev]"

sync:
	$(PY) scripts/sync_spec.py

generate:
	$(PY) scripts/generate_models.py && $(PY) scripts/generate_operations.py

lint:
	$(RUFF) check src tests scripts examples && $(RUFF) format --check src tests scripts examples

format:
	$(RUFF) check --fix src tests scripts examples && $(RUFF) format src tests scripts examples

typecheck:
	$(MYPY)

test:
	$(PYTEST) -q --ignore=tests/live

test-live:
	$(PYTEST) -q tests/live

check-brand:
	$(PY) scripts/check_brand.py

build:
	rm -rf dist && $(PY) -m build && $(PY) -m twine check dist/*

verify: lint typecheck check-brand
	$(PY) scripts/sync_spec.py --check
	$(PY) scripts/generate_models.py --check
	$(PY) scripts/generate_operations.py --check
	$(MAKE) test build

clean:
	rm -rf dist build .mypy_cache .ruff_cache .pytest_cache
