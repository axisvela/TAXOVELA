#!/usr/bin/env python3
"""validate_check.py — deterministic checks on a validation/v1 result.

A review finding is only actionable if it points at something that exists. This
command extracts the typed codes a finding cites and joins them back to the
requirements model and the architecture blueprint, so an unverifiable or stale
finding is visible before a remediation backlog is built from it.

A finding may qualify a citation with the field it is about, as
``CMP-03.encryption_at_rest`` or ``FLOW-12.auth_method``. The field is checked
against the entity's definition in ``schemas/req-v2.schema.json``, so field-level
evidence is verified rather than asserted.

Rules
    V-01 ERROR  a cited typed code does not exist in the model
    V-02 WARN   a finding cites no model element at all
    V-03 WARN   a finding cites the retired ``SYS-nn`` id space
    V-04 ERROR  a cited ``CODE.field`` is not a field of that entity

Usage
    archharness validate-check -v output/validation/validate_result.json \\
        -r output/requirements/req.yaml [-b output/designs/blueprint.yaml] [--json]

Exit codes: 0 = no ERROR findings, 1 = ERROR findings, 2 = input error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from .diagrams import topology

#: Entity ids a finding may cite: inventory rows and the derived layers.
TYPED_CODE = re.compile(r"\b(INF|APP|CMP|SUB|STK|DEP|FLOW|LNK|AUTH)-\d{1,4}\b")
#: An optional field qualifier, e.g. ``CMP-03.encryption_at_rest``.
FIELD_CODE = re.compile(
    r"\b(INF|APP|CMP|SUB|STK|DEP|FLOW|LNK|AUTH)-(\d{1,4})\.([a-z][a-z0-9_]*)\b")
#: The id space retired by the req/v2 migration.
LEGACY_CODE = re.compile(r"\bSYS-\d{1,4}\b", re.IGNORECASE)

#: Typed prefix → the definition that describes its fields.
_ENTITY_DEFS = {
    "INF": "infra", "APP": "system", "CMP": "component", "STK": "stack",
    "DEP": "deployment", "FLOW": "flow", "LNK": "networkLink", "AUTH": "auth",
}


def entity_fields() -> dict[str, set[str]]:
    """Field names per typed prefix, read from the req/v2 schema."""
    from .schemas import load_schema

    defs = load_schema("req/v2").get("$defs", {})
    fields: dict[str, set[str]] = {}
    for prefix, definition in _ENTITY_DEFS.items():
        properties = (defs.get(definition) or {}).get("properties") or {}
        if properties:
            fields[prefix] = set(properties)
    return fields

_COLLECTIONS = ("infra", "systems", "components", "stacks", "deployments",
                "flows", "network_links", "auth")


def _finding(rule: str, message: str, severity: str = "ERROR", **evidence) -> dict:
    return {"rule": rule, "severity": severity, "message": message, "evidence": evidence}


def _load(path: Path) -> dict:
    import yaml

    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    return document if isinstance(document, dict) else {}


def model_ids(requirements: dict | None, blueprint: dict | None) -> set[str]:
    """Every id a finding may legitimately cite."""
    ids: set[str] = set()
    if isinstance(requirements, dict):
        req = requirements.get("requirements") or {}
        for collection in _COLLECTIONS:
            for row in req.get(collection) or []:
                if isinstance(row, dict) and row.get("id"):
                    ids.add(str(row["id"]))
    if isinstance(blueprint, dict):
        for region in topology.deployment_of(blueprint):
            if not isinstance(region, dict):
                continue
            ids.add(str(region.get("id") or ""))
            for zone in topology.region_zones(region):
                if not isinstance(zone, dict):
                    continue
                ids.add(str(zone.get("id") or ""))
                for node in zone.get("components", []) or []:
                    if isinstance(node, dict):
                        ids.add(str(node.get("id") or ""))
    ids.discard("")
    return ids


def check_findings(validation: dict, requirements: dict | None = None,
                   blueprint: dict | None = None) -> list[dict]:
    """Return the evidence findings for one validation result."""
    if not isinstance(validation, dict) or validation.get("schema_version") != "validation/v1":
        return [_finding("V-00", "validation input must be a validation/v1 document")]
    known = model_ids(requirements, blueprint)
    fields = entity_fields()
    findings: list[dict] = []

    for issue in validation.get("issues") or []:
        if not isinstance(issue, dict):
            continue
        issue_id = str(issue.get("id") or "?")
        text = f"{issue.get('subject') or ''} {issue.get('evidence') or ''}"
        cited = sorted({match.group(0) for match in TYPED_CODE.finditer(text)})
        legacy = sorted({match.group(0) for match in LEGACY_CODE.finditer(text)})

        unknown = [code for code in cited if code not in known]
        if unknown:
            findings.append(_finding(
                "V-01",
                f"{issue_id} cites {', '.join(unknown)}, which the model does not declare",
                issue_id=issue_id, unknown_codes=unknown))

        bad_fields = []
        for match in FIELD_CODE.finditer(text):
            prefix, number, field = match.groups()
            code = f"{prefix}-{int(number):02d}"
            allowed = fields.get(prefix)
            if code in known and allowed is not None and field not in allowed:
                bad_fields.append(f"{code}.{field}")
        if bad_fields:
            findings.append(_finding(
                "V-04",
                f"{issue_id} cites {', '.join(bad_fields)}, which are not fields of that entity",
                issue_id=issue_id, unknown_fields=bad_fields))
        if not cited and not legacy:
            findings.append(_finding(
                "V-02",
                f"{issue_id} is not anchored to any model element",
                severity="WARN", issue_id=issue_id, subject=issue.get("subject")))
        if legacy:
            findings.append(_finding(
                "V-03",
                f"{issue_id} cites the retired id space ({', '.join(legacy)})",
                severity="WARN", issue_id=issue_id, legacy_codes=legacy))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check validation findings against the model")
    parser.add_argument("--validation", "-v", required=True, help="validation/v1 result file")
    parser.add_argument("--requirements", "-r", default=None, help="req/v2 requirements YAML")
    parser.add_argument("--blueprint", "-b", default=None, help="Architecture blueprint YAML")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)

    validation_path = Path(args.validation)
    if not validation_path.is_file():
        print(f"ERROR: validation file not found: {validation_path}", file=sys.stderr)
        return 2
    try:
        validation = _load(validation_path)
        requirements = _load(Path(args.requirements)) if args.requirements else None
        blueprint = _load(Path(args.blueprint)) if args.blueprint else None
    except Exception as exc:  # noqa: BLE001 - any read failure is an input error
        print(f"ERROR: cannot read inputs: {exc}", file=sys.stderr)
        return 2

    findings = check_findings(validation, requirements, blueprint)
    errors = [finding for finding in findings if finding["severity"] == "ERROR"]

    if args.as_json:
        print(json.dumps({"schema_version": "validate-check/v1",
                          "errors": len(errors),
                          "warnings": len(findings) - len(errors),
                          "findings": findings}, indent=2))
    elif findings:
        for finding in findings:
            print(f"{finding['severity']} {finding['rule']}: {finding['message']}")
        print(f"\n{len(errors)} error(s), {len(findings) - len(errors)} warning(s)")
    else:
        print("OK — every finding is anchored to a model element")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
