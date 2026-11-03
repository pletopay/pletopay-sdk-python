#!/usr/bin/env python
"""Regenerates src/pletopay/types/_generated.py and _events.py from spec/public.v1.yaml.

    python scripts/generate_models.py          write
    python scripts/generate_models.py --check  fail when the committed files are stale

Models come from datamodel-code-generator (pydantic v2, ``extra='allow'``). Two post-processing
steps keep responses from breaking on harmless drift: value constraints (id patterns, lengths,
ranges) are dropped because they describe what the API enforces on *input*, and ``float`` becomes
``int`` because every number in the contract is an integer (kobo, seconds, counts).
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "spec" / "public.v1.yaml"
OUT_DIR = ROOT / "src" / "pletopay" / "types"
GENERATED = OUT_DIR / "_generated.py"
EVENTS = OUT_DIR / "_events.py"
HEADER = "# Generated from spec/public.v1.yaml by scripts/generate_models.py. Do not edit by hand.\n# ruff: noqa\n# fmt: off\n"
CONSTRAINT_NAMES = r"(?:pattern|ge|le|gt|lt|min_length|max_length|min_items|max_items|multiple_of)"
CONSTRAINT = re.compile(r"^\s+(pattern|ge|le|gt|lt|min_length|max_length|min_items|max_items|multiple_of)=.*,\s*$")


def camel(event_type: str) -> str:
    return "Event" + "".join(part.capitalize() for part in event_type.replace(".", "_").split("_"))


def generate() -> dict[Path, str]:
    raw = subprocess.run(
        [
            sys.executable,
            "-W",
            "ignore",
            "-m",
            "datamodel_code_generator",
            "--input",
            str(SPEC),
            "--input-file-type",
            "openapi",
            "--output-model-type",
            "pydantic_v2.BaseModel",
            "--base-class",
            "pletopay.types._base.PletopayModel",
            "--openapi-scopes",
            "schemas",
            "--target-python-version",
            "3.10",
            "--use-standard-collections",
            "--use-union-operator",
            "--use-annotated",
            "--field-constraints",
            "--allow-extra-fields",
            "--use-schema-description",
            "--snake-case-field",
            "--enum-field-as-literal",
            "all",
            "--collapse-root-models",
            "--disable-timestamp",
            "--use-double-quotes",
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    lines = [line for line in raw.splitlines() if not CONSTRAINT.match(line)]
    body = "\n".join(lines) + "\n"
    value = r'(?:"[^"]*"|[^,)\n]+)'
    body = re.sub(rf",\s*{CONSTRAINT_NAMES}={value}", "", body)
    body = re.sub(rf"Field\({CONSTRAINT_NAMES}={value}\)", "Field()", body)
    body = re.sub(r"Annotated\[([^\[\]]+), Field\(\)\]", r"\1", body)
    body = re.sub(r"\bfloat\b", "int", body)
    # `string | Customer` unions produce RootModel[str] wrappers (Customer1, Payment1, …): plain str reads better.
    wrappers = re.findall(r"^class (\w+)\(RootModel\[str\]\):\n", body, flags=re.M)
    body = re.sub(r"^class \w+\(RootModel\[str\]\):\n(?:(?:    .*|)\n)*?(?=^class |\Z)", "", body, flags=re.M)
    for name in wrappers:
        body = re.sub(rf"\b{name}\b", "str", body)
    body = body.replace("from pydantic import Field, RootModel", "from pydantic import Field")
    # A wrapper that took a schema's name pushes the real schema to `Name1`: give the name back.
    spec_names = yaml.safe_load(SPEC.read_text())["components"]["schemas"].keys()
    for name in spec_names:
        if f"class {name}(" not in body and f"class {name}1(" in body:
            body = re.sub(rf"\b{name}1\b", name, body)
    # Plain Python types for timestamps, emails and URLs: no extra dependency, no over-strict parsing.
    body = re.sub(
        r"from pydantic import ([^\n]+)",
        lambda m: (
            "from pydantic import "
            + ", ".join(
                sorted(
                    {
                        n.strip()
                        for n in m.group(1).split(",")
                        if n.strip() not in {"AwareDatetime", "EmailStr", "AnyUrl", "ConfigDict", "BaseModel"}
                    }
                )
            )
        ),
        body,
        count=1,
    )
    body = body.replace("AwareDatetime", "datetime").replace("EmailStr", "str").replace("AnyUrl", "str")
    body = body.replace(
        "from __future__ import annotations\n",
        "from __future__ import annotations\n\nfrom datetime import datetime\n",
        1,
    )
    # Our base class already sets extra='allow'; drop the per-model repetition.
    body = re.sub(r"\n    model_config = ConfigDict\(\n        extra=\"allow\",\n    \)\n", "\n", body)
    generated = HEADER + body

    spec = yaml.safe_load(SPEC.read_text())
    types = sorted(spec.get("webhooks", {}))
    names = [camel(t) for t in types]
    missing = [n for n in names if f"class {n}(" not in generated]
    if missing:
        raise SystemExit(f"generator: event classes not found in output: {missing}")
    events = HEADER + (
        '"""Webhook event types and the discriminated union over them."""\n\n'
        "from __future__ import annotations\n\n"
        "from typing import Annotated, Literal, Union\n\n"
        "from pydantic import Field\n\n"
        "from pletopay.types._generated import (\n" + "".join(f"    {n},\n" for n in names) + ")\n\n"
        "EVENT_TYPES: tuple[str, ...] = (\n" + "".join(f'    "{t}",\n' for t in types) + ")\n\n"
        "EventType = Literal[\n" + "".join(f'    "{t}",\n' for t in types) + "]\n\n"
        "KnownEvent = Annotated[\n    Union[\n"
        + "".join(f"        {n},\n" for n in names)
        + '    ],\n    Field(discriminator="type"),\n]\n\n'
        "EVENT_CLASSES: dict[str, type] = {\n"
        + "".join(f'    "{t}": {n},\n' for t, n in zip(types, names, strict=False))
        + "}\n\n"
        f'SPEC_API_VERSION = "{spec["info"]["version"]}"\n'
    )
    return {GENERATED: generated, EVENTS: events}


def main() -> None:
    check = "--check" in sys.argv
    files = generate()
    stale: list[str] = []
    for path, content in files.items():
        current = path.read_text() if path.exists() else None
        if check:
            if current != content:
                stale.append(str(path.relative_to(ROOT)))
        elif current != content:
            path.write_text(content)
            print(f"generate: wrote {path.relative_to(ROOT)}")
        else:
            print(f"generate: {path.relative_to(ROOT)} unchanged")
    if stale:
        raise SystemExit(
            f"generate: stale {', '.join(stale)}. Run `python scripts/generate_models.py` and commit the result."
        )
    if check:
        print("generate: up to date")


if __name__ == "__main__":
    main()
