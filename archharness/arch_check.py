#!/usr/bin/env python3
"""arch_check.py — deterministic checks on an Architecture YAML model.

Objective, high-confidence rules that can be decided from the structured model
alone, before any image review. Every finding carries a stable rule id and the
evidence it was derived from, so a report or a gate can cite it.

Rules
    A-01 ERROR  duplicate region/zone/component id
    A-02 ERROR  interaction endpoint is not declared anywhere
    A-03 ERROR  interaction has no protocol label
    A-04 ERROR  interaction has no authentication label
    A-05 WARN   interaction points at itself
    A-06 WARN   component declares a lifecycle status the standard does not define

Labels come from standards/diagram-style.yaml §2: a communication arrow must
carry both a protocol and an authentication method. An explicit "TBD" or
"Not applicable" is a valid value; an absent field is not.

Usage
    archharness arch-check -i blueprint.yaml
    archharness arch-check -i blueprint.yaml --json

Exit codes: 0 = no ERROR findings, 1 = ERROR findings, 2 = input error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .diagrams import labels, topology
from .diagrams import styles

SEVERITY_ERROR = "ERROR"
SEVERITY_WARN = "WARN"

# Lifecycle values the colour scale in standards/diagram-style.yaml defines.
KNOWN_STATUSES = frozenset(labels.STATUS_FILL)

# ``shape`` values the renderers act on; anything else silently falls back.
KNOWN_SHAPES = frozenset(styles.STANDARD_SHAPES) | {
    "hexagon", "trapezoid", "parallelogram", "message_queue", "cylinder",
    "circle", "bastion", "cloud_rect",
}


def _finding(rule: str, severity: str, message: str, **evidence) -> dict:
    return {"rule": rule, "severity": severity, "message": message, "evidence": evidence}


def _components(arch: dict):
    """Yield (region, zone, component) for every declared component."""
    for region in topology.deployment_of(arch):
        if not isinstance(region, dict):
            continue
        for zone in topology.region_zones(region):
            if not isinstance(zone, dict):
                continue
            for comp in zone.get("components", []) or []:
                if isinstance(comp, dict):
                    yield region, zone, comp


def check_architecture(arch: dict) -> list[dict]:
    """Return the findings for one architecture document."""
    findings: list[dict] = []
    if not isinstance(arch, dict):
        return [_finding("A-00", SEVERITY_ERROR, "architecture document must be a mapping")]

    declared, duplicates = topology.collect_declared_ids(arch)
    for duplicate in sorted(duplicates):
        findings.append(_finding(
            "A-01", SEVERITY_ERROR, f"duplicate id {duplicate!r}", id=duplicate))

    allowed = declared | set(topology.RESERVED_NODES)
    for interaction in topology.interactions_of(arch):
        if not isinstance(interaction, dict):
            continue
        source = interaction.get("from", "")
        target = interaction.get("to", "")
        edge = {"from": source, "to": target}
        if source not in allowed or target not in allowed:
            findings.append(_finding(
                "A-02", SEVERITY_ERROR,
                f"interaction {source or '?'} -> {target or '?'} references an "
                "undeclared endpoint", **edge))
        if not str(interaction.get("protocol") or "").strip():
            findings.append(_finding(
                "A-03", SEVERITY_ERROR,
                f"interaction {source or '?'} -> {target or '?'} has no protocol label", **edge))
        if not str(interaction.get("auth") or "").strip():
            findings.append(_finding(
                "A-04", SEVERITY_ERROR,
                f"interaction {source or '?'} -> {target or '?'} has no authentication label", **edge))
        if source and source == target:
            findings.append(_finding(
                "A-05", SEVERITY_WARN,
                f"interaction {source} points at itself", **edge))

    for _region, _zone, comp in _components(arch):
        declared_status = comp.get("status")
        if declared_status and labels.component_status(comp) is None:
            findings.append(_finding(
                "A-06", SEVERITY_WARN,
                f"component {comp.get('id', '?')!r} declares unknown status "
                f"{declared_status!r}", id=comp.get("id", ""), status=str(declared_status)))

    return findings


def _load_arch(path: Path) -> dict:
    import yaml

    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if isinstance(document, dict) and isinstance(document.get("arch"), dict):
        return document["arch"]
    return document


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Deterministic architecture model checks")
    parser.add_argument("-i", "--input", required=True, help="Architecture YAML file")
    parser.add_argument("--json", action="store_true", dest="as_json",
                        help="Emit findings as JSON")
    args = parser.parse_args(argv)

    path = Path(args.input)
    if not path.is_file():
        print(f"ERROR: input file not found: {path}", file=sys.stderr)
        return 2
    try:
        arch = _load_arch(path)
    except Exception as exc:  # noqa: BLE001 - report any parse failure as input error
        print(f"ERROR: cannot read {path}: {exc}", file=sys.stderr)
        return 2

    findings = check_architecture(arch)
    errors = [f for f in findings if f["severity"] == SEVERITY_ERROR]

    if args.as_json:
        print(json.dumps({
            "schema_version": "arch-check/v1",
            "path": str(path),
            "errors": len(errors),
            "warnings": len(findings) - len(errors),
            "findings": findings,
        }, indent=2))
    else:
        for finding in findings:
            print(f"{finding['severity']} {finding['rule']}: {finding['message']}")
        if findings:
            print(f"\n{len(errors)} error(s), {len(findings) - len(errors)} warning(s)")
        else:
            print(f"{path}: OK — no findings")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
