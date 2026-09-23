#!/usr/bin/env python3
"""Deterministic req/v2 → blueprint traceability checks.

Diagram node ids are the join key between a req/v2 requirements model and an
architecture blueprint.  A component deployed in more than one country may use
the documented view suffix (``CMP-03-CN`` / ``CMP-03-NA``); its base id is still
the requirement component and each suffix must have a matching deployment.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from .diagrams import topology

_TYPED_NODE = re.compile(r"^(CMP|INF)-(\d+)(?:-([A-Z]{2}))?$")

# Diagram suffixes describe the business site, while req/v2 deployments store
# ISO countries.  NA is deliberately a site group rather than the non-existent
# ISO country "NA"; expand it before comparing a deployment's infra country.
_SITE_COUNTRIES = {"NA": {"US", "CA", "MX"}}


def _finding(rule: str, message: str, **evidence) -> dict:
    return {"rule": rule, "severity": "ERROR", "message": message, "evidence": evidence}


def _load(path: Path) -> dict:
    import yaml

    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    return document.get("arch", document) if isinstance(document, dict) else document


def check_traceability(requirements: dict, blueprint: dict) -> list[dict]:
    """Check typed blueprint nodes resolve to req/v2 inventory and deployments.

    T-01: a ``CMP-*`` / ``INF-*`` node's base id exists in the corresponding
    req/v2 collection.
    T-02: a country-suffixed component node has at least one deployment of its
    base component on infra in that country.
    """
    if not isinstance(requirements, dict) or requirements.get("schema_version") != "req/v2":
        return [_finding("T-00", "requirements input must be a req/v2 document")]
    req = requirements.get("requirements") or {}
    components = {row.get("id") for row in req.get("components", []) or []}
    infra = {row.get("id"): row for row in req.get("infra", []) or []}
    deployments = req.get("deployments", []) or []
    findings: list[dict] = []

    for _region, _zone, node in _nodes(blueprint):
        node_id = str(node.get("id") or "")
        match = _TYPED_NODE.match(node_id)
        if not match:
            continue
        kind, number, country = match.groups()
        base = f"{kind}-{number}"
        known = base in components if kind == "CMP" else base in infra
        if not known:
            findings.append(_finding("T-01", f"blueprint node {node_id!r} has no req/v2 {kind} row",
                                     node_id=node_id, base_id=base))
            continue
        if kind == "CMP" and country:
            countries = _SITE_COUNTRIES.get(country, {country})
            matches = [
                row for row in deployments
                if row.get("component_id") == base
                and (infra.get(row.get("infra_id")) or {}).get("country") in countries
            ]
            if not matches:
                findings.append(_finding(
                    "T-02", f"site-qualified node {node_id!r} has no {country} deployment for {base}",
                    node_id=node_id, component_id=base, country=country,
                ))
    return findings


def _nodes(blueprint: dict):
    for region in topology.deployment_of(blueprint):
        if not isinstance(region, dict):
            continue
        for zone in topology.region_zones(region):
            if not isinstance(zone, dict):
                continue
            for node in zone.get("components", []) or []:
                if isinstance(node, dict):
                    yield region, zone, node


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check req/v2 to blueprint traceability")
    parser.add_argument("--requirements", "-r", required=True, help="req/v2 requirements YAML")
    parser.add_argument("--blueprint", "-b", required=True, help="Architecture blueprint YAML")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    req_path, blueprint_path = Path(args.requirements), Path(args.blueprint)
    if not req_path.is_file() or not blueprint_path.is_file():
        print("ERROR: requirements and blueprint files must exist", file=sys.stderr)
        return 2
    try:
        findings = check_traceability(_load(req_path), _load(blueprint_path))
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: cannot read trace inputs: {exc}", file=sys.stderr)
        return 2
    if args.as_json:
        print(json.dumps({"schema_version": "trace-check/v1", "findings": findings}, indent=2))
    elif findings:
        for finding in findings:
            print(f"ERROR {finding['rule']}: {finding['message']}")
    else:
        print("OK — req/v2 inventory and blueprint nodes are traceable")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
