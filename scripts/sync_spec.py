#!/usr/bin/env python
"""Copies the merchant OpenAPI contract from the API repo into spec/public.v1.yaml.

python scripts/sync_spec.py           copy from ../pletopay-api/openapi/public.v1.yaml (or PLETOPAY_SPEC_PATH)
python scripts/sync_spec.py --check   fail when the copy differs from the source
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = Path(os.environ.get("PLETOPAY_SPEC_PATH", ROOT.parent / "pletopay-api" / "openapi" / "public.v1.yaml"))
TARGET = ROOT / "spec" / "public.v1.yaml"
check = "--check" in sys.argv

if not SOURCE.exists():
    if check and TARGET.exists():
        print(f"spec: source {SOURCE} not found; keeping the committed copy")
        sys.exit(0)
    sys.exit(f"spec: source not found at {SOURCE} (set PLETOPAY_SPEC_PATH)")

new = SOURCE.read_text()
current = TARGET.read_text() if TARGET.exists() else None
if check:
    if current != new:
        sys.exit(
            "spec: spec/public.v1.yaml is stale. Run `python scripts/sync_spec.py && python scripts/generate_models.py`."
        )
    print("spec: up to date")
elif current == new:
    print("spec: already up to date")
else:
    TARGET.write_text(new)
    print(f"spec: wrote spec/public.v1.yaml from {SOURCE}")
