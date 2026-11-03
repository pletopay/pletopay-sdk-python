#!/usr/bin/env python
"""The brand is written "Pletopay"; only the PletoPay-* protocol headers keep the capital P. Merchants never see the banking partner's name."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RULES = [
    (
        re.compile(r"PletoPay(?!-)"),
        'misspells the brand (write "Pletopay"; only PletoPay-* headers keep the capital P)',
    ),
    (re.compile(r"9ja ?pay", re.I), "names the banking partner (merchants work with Pletopay)"),
]
SKIP = {ROOT / "src" / "pletopay" / "types" / "_generated.py", Path(__file__).resolve()}
ROOTS = [
    "src",
    "tests",
    "examples",
    "scripts",
    "README.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "pyproject.toml",
]

problems: list[str] = []
for r in ROOTS:
    base = ROOT / r
    files = [base] if base.is_file() else list(base.rglob("*")) if base.exists() else []
    for f in files:
        if not f.is_file() or f.suffix not in {".py", ".md", ".toml", ".yaml", ".yml", ".json"} or f in SKIP:
            continue
        for i, line in enumerate(f.read_text().splitlines(), 1):
            for rule, why in RULES:
                if rule.search(line):
                    problems.append(f"{f.relative_to(ROOT)}:{i}: {why}\n    {line.strip()}")
if problems:
    sys.exit("\n".join(problems))
print("brand: ok")
