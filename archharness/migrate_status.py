#!/usr/bin/env python3
"""migrate_status.py — report how far each example has moved to the req/v2 model.

`docs/example-rebuild-guide.md` describes the migration; this command measures
it, so the backlog is machine-readable instead of prose that drifts. Each
example resolves to one status:

    scaffold         no registry yet (reference input missing)
    reqv1            legacy single-table ``SYS-nn`` registry
    reqv2-partial     typed registry and req/v2 requirements, but legacy ids
                      remain in the blueprint or in the documents
    reqv2-complete    typed registry, req/v2 requirements, typed blueprint,
                      and no legacy citations anywhere

The ``migrate-ok`` status additionally requires the objective checks to pass
(registry ↔ docs consistency and the req/v2 cross-field rules).

Usage
    archharness migrate-status
    archharness migrate-status --json
    archharness migrate-status examples/05-supply-chain-order-private-cloud

Exit codes: 0 = every example at or beyond its declared status, 1 = a
migrated example still fails its checks, 2 = bad invocation.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import re
import sys
from pathlib import Path

SCAFFOLD = "scaffold"
REQV1 = "reqv1"
REQV2_PARTIAL = "reqv2-partial"
REQV2_COMPLETE = "reqv2-complete"

# Documented status tokens, in the order an example passes through them.
STATUS_ORDER = (SCAFFOLD, REQV1, REQV2_PARTIAL, REQV2_COMPLETE)

TYPED_PREFIXES = ("INF", "APP", "CMP", "SUB", "STK", "DEP", "FLOW", "LNK", "AUTH")
LEGACY_PATTERN = re.compile(r"\bSYS-\d{1,4}\b", re.IGNORECASE)
ROW_PATTERN = re.compile(r"^\|\s*([A-Z]{2,5})-(\d{1,4})\s*\|")


def _registry_rows(registry: Path) -> tuple[dict[str, int], int]:
    """Return (typed rows per prefix, legacy row count)."""
    counts: dict[str, int] = {}
    legacy = 0
    for line in registry.read_text(encoding="utf-8").splitlines():
        match = ROW_PATTERN.match(line.strip())
        if not match:
            continue
        prefix = match.group(1)
        if prefix in TYPED_PREFIXES:
            counts[prefix] = counts.get(prefix, 0) + 1
        elif prefix == "SYS":
            legacy += 1
    return counts, legacy


def _schema_version(path: Path) -> str | None:
    if not path.is_file():
        return None
    match = re.search(r"^schema_version:\s*(\S+)", path.read_text(encoding="utf-8"), re.MULTILINE)
    return match.group(1) if match else None


def _legacy_citations(root: Path) -> list[str]:
    """Documents (outside the registry and output/) that still cite SYS codes."""
    from .registry import collect_docs

    hits = []
    for doc in collect_docs(root):
        if LEGACY_PATTERN.search(doc.read_text(encoding="utf-8", errors="replace")):
            hits.append(str(doc.relative_to(root)))
    return hits


def example_status(root: str | Path) -> dict:
    """Measure one example directory against the req/v2 migration."""
    root = Path(root)
    registry = root / "input" / "systems-registry.md"
    req_yaml = root / "output" / "requirements" / "req.yaml"
    blueprint = root / "output" / "designs" / "blueprint.yaml"

    if not registry.is_file():
        return {
            "example": root.name, "status": SCAFFOLD, "registry_rows": {},
            "legacy_registry_rows": 0, "requirements_schema": None,
            "blueprint_legacy_ids": 0, "legacy_documents": [],
            "registry_check": None, "requirements_check": None,
        }

    typed_rows, legacy_rows = _registry_rows(registry)
    schema = _schema_version(req_yaml)

    blueprint_legacy = 0
    if blueprint.is_file():
        blueprint_legacy = len(
            LEGACY_PATTERN.findall(blueprint.read_text(encoding="utf-8", errors="replace")))

    documents = _legacy_citations(root)

    if legacy_rows or not typed_rows:
        status = REQV1
    elif schema == "req/v2" and not blueprint_legacy and not documents:
        status = REQV2_COMPLETE
    else:
        status = REQV2_PARTIAL

    return {
        "example": root.name,
        "status": status,
        "registry_rows": typed_rows,
        "legacy_registry_rows": legacy_rows,
        "requirements_schema": schema,
        "blueprint_legacy_ids": blueprint_legacy,
        "legacy_documents": documents,
        "registry_check": _registry_check(root),
        "requirements_check": _requirements_check(req_yaml),
    }


def _registry_check(root: Path) -> dict:
    """Run registry_check without polluting stdout; report errors."""
    from .registry import check_example

    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        errors = check_example(root)
    return {"errors": errors, "ok": errors == 0}


def _requirements_check(req_yaml: Path) -> dict | None:
    """Run the req/v2 cross-field rules when a req/v2 document exists."""
    if _schema_version(req_yaml) != "req/v2":
        return None
    import yaml

    from .requirements.validator import validate_requirements

    try:
        findings = validate_requirements(yaml.safe_load(req_yaml.read_text(encoding="utf-8")))
    except Exception as exc:  # noqa: BLE001 - unreadable document is a finding
        return {"errors": 1, "ok": False, "detail": str(exc)}
    errors = [f for f in findings if getattr(f, "severity", "error") == "error"]
    return {"errors": len(errors), "ok": not errors,
            "findings": [f"{f.rule_id} {f.subject}: {f.message}" for f in errors]}


def _example_dirs(paths: list[str]) -> list[Path]:
    if paths:
        return [Path(p) for p in paths]
    from .paths import require_archharness_root

    examples = require_archharness_root() / "examples"
    if not examples.is_dir():
        return []
    return sorted(p for p in examples.iterdir() if p.is_dir())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Report each example's req/v2 migration status")
    parser.add_argument("paths", nargs="*", help="Example directories (default: all)")
    parser.add_argument("--json", action="store_true", dest="as_json",
                        help="Emit the report as JSON")
    args = parser.parse_args(argv)

    reports = [example_status(path) for path in _example_dirs(args.paths)]
    if not reports:
        print("ERROR: no example directories found", file=sys.stderr)
        return 2

    failures = [
        report for report in reports
        if report["status"] == REQV2_COMPLETE
        and not (report["registry_check"] or {}).get("ok", True)
        or (report.get("requirements_check") and not report["requirements_check"]["ok"])
    ]

    if args.as_json:
        print(json.dumps({
            "schema_version": "migrate-status/v1",
            "statuses": list(STATUS_ORDER),
            "examples": reports,
        }, indent=2))
    else:
        width = max(len(report["example"]) for report in reports)
        for report in reports:
            detail = []
            if report["status"] == REQV2_PARTIAL:
                if report["blueprint_legacy_ids"]:
                    detail.append(f"{report['blueprint_legacy_ids']} legacy id(s) in blueprint")
                if report["legacy_documents"]:
                    detail.append("legacy codes in " + ", ".join(report["legacy_documents"]))
            elif report["status"] == REQV1:
                detail.append(f"{report['legacy_registry_rows']} legacy registry row(s)")
            print(f"{report['example']:<{width}}  {report['status']}"
                  + (f"  — {'; '.join(detail)}" if detail else ""))
        if failures:
            print()
            for report in failures:
                checks = []
                if report["registry_check"] and not report["registry_check"]["ok"]:
                    checks.append(f"registry_check: {report['registry_check']['errors']} error(s)")
                if report.get("requirements_check") and not report["requirements_check"]["ok"]:
                    checks.append(f"req-validate: {report['requirements_check']['errors']} error(s)")
                print(f"FAIL {report['example']}: " + "; ".join(checks), file=sys.stderr)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
