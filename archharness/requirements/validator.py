#!/usr/bin/env python3
"""validator.py — cross-field validation for a finalized req/v2 document.

`schemas/req-v2.schema.json` checks each field in isolation. This module checks
the rules that span fields, as listed in
`standards/requirements-model-v2.yaml > validation`:

    V1  every id's prefix matches its collection
    V2  every reference resolves to an existing id of the right kind
    V3  infra.parent_id respects the node_kind containment matrix
    V4  an infrastructure/security role never appears as a component
    V5  flow endpoints are components; network-link endpoints are infra
    V6  a prod deployment has an infra_id
    V7  every flow has an inline auth_method; any external entry has an auth row

Usage:
    python -m archharness req-validate req.yaml
    python -m archharness req-validate req.yaml --json

Exit code: 0 = no errors (warnings allowed), 1 = errors found, 2 = unreadable input.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

import yaml

from ..schemas import SchemaError, validate_final_req_v2

# ── Node-kind containment matrix ──────────────────────────────────────────────

L1_KINDS = {"region"}
L2_KINDS = {
    "data_center", "iaas_vpc_vnet", "paas", "saas", "third_party",
    "office_network", "factory_network", "lab", "internet_network",
}
L3_KINDS = {"network_zone", "subnet"}
L4_KINDS = {
    "firewall", "security_gateway", "waf", "router", "switch", "vpn_gateway",
    "identity_provider", "soc_monitoring", "load_balancer", "bastion_host",
    "logging_service", "policy_service", "key_management",
}
# node_kinds that must never be modelled as an application component.
# `load_balancer` is deliberately excluded: an application-layer load balancer
# may be a component with component_role=load_balancer (rule R-CMP-2); only an
# infrastructure appliance must be an infra L4 node.
APPLIANCE_KINDS = L4_KINDS - {"load_balancer"}

PARENT_ALLOWED = {
    **{kind: set() for kind in L1_KINDS},                       # region is a root
    **{kind: L1_KINDS for kind in L2_KINDS},                    # L2 under region
    **{kind: L2_KINDS for kind in L3_KINDS},                    # zone/subnet under L2
    **{kind: L3_KINDS | L2_KINDS for kind in L4_KINDS},         # service node inside L2/L3
}

COLLECTION_PREFIX = {
    "infra": "INF", "systems": "APP", "components": "CMP", "stacks": "STK",
    "deployments": "DEP", "flows": "FLOW", "network_links": "LNK",
    "auth": "AUTH", "ecosystem_relations": None,
}


@dataclass
class Finding:
    rule_id: str
    severity: str          # error | warning
    subject: str
    message: str


def _ids(doc: dict, collection: str) -> set[str]:
    return {item.get("id") for item in doc["requirements"].get(collection, []) or []}


def _by_id(doc: dict, collection: str) -> dict[str, dict]:
    return {item.get("id"): item for item in doc["requirements"].get(collection, []) or []}


def validate_requirements(doc: object) -> list[Finding]:
    """Return all findings for a req/v2 document (schema + cross-field)."""
    findings: list[Finding] = []

    try:
        validate_final_req_v2(doc)
    except SchemaError as exc:
        findings.append(Finding("SCHEMA", "error", "$", str(exc)))
        return findings

    req = doc["requirements"]

    # ── V1 — id prefix matches collection ─────────────────────────────────────
    for collection, prefix in COLLECTION_PREFIX.items():
        if prefix is None:
            continue
        for item in req.get(collection, []) or []:
            item_id = item.get("id", "")
            if not item_id.startswith(f"{prefix}-"):
                findings.append(Finding(
                    "V1", "error", str(item_id),
                    f"{collection} id {item_id!r} does not use prefix {prefix}-"))

    # Duplicate ids
    for collection in COLLECTION_PREFIX:
        seen: set[str] = set()
        for item in req.get(collection, []) or []:
            item_id = item.get("id")
            if item_id in seen:
                findings.append(Finding("V1", "error", str(item_id),
                                        f"duplicate id in {collection}"))
            seen.add(item_id)

    infra_ids = _ids(doc, "infra")
    system_ids = _ids(doc, "systems")
    component_ids = _ids(doc, "components")
    infra_by_id = _by_id(doc, "infra")

    def _check_ref(rule: str, subject: str, value, allowed: set, label: str,
                   allow_internet: bool = False, required: bool = True) -> None:
        if value is None:
            if required:
                findings.append(Finding(rule, "error", subject, f"{label} is missing"))
            return
        if allow_internet and value == "internet":
            return
        if value not in allowed:
            findings.append(Finding(rule, "error", subject,
                                    f"{label} {value!r} does not resolve to an existing "
                                    f"{label.split()[0]}"))

    # ── V2 — referential integrity ────────────────────────────────────────────
    for infra in req.get("infra", []) or []:
        subject = str(infra.get("id"))
        if infra.get("parent_id"):
            _check_ref("V2", subject, infra["parent_id"], infra_ids, "parent_id")
        if infra.get("node_kind") in L1_KINDS and infra.get("parent_id"):
            findings.append(Finding("V3", subject, subject,
                                    "a region must be a root node without parent_id"))

    for component in req.get("components", []) or []:
        subject = str(component.get("id"))
        _check_ref("V2", subject, component.get("system_id"), system_ids, "system_id")
        if component.get("key_management"):
            _check_ref("V2", subject, component["key_management"], infra_ids, "key_management")

    for stack in req.get("stacks", []) or []:
        _check_ref("V2", str(stack.get("id")), stack.get("component_id"),
                   component_ids, "component_id")

    for deployment in req.get("deployments", []) or []:
        subject = str(deployment.get("id"))
        _check_ref("V2", subject, deployment.get("component_id"), component_ids, "component_id")
        _check_ref("V2", subject, deployment.get("infra_id"), infra_ids, "infra_id")
        # ── V6 — prod deployments must carry an infra_id ──────────────────────
        if deployment.get("environment") == "prod" and not deployment.get("infra_id"):
            findings.append(Finding("V6", "error", subject,
                                    "prod deployment is missing infra_id"))

    for flow in req.get("flows", []) or []:
        subject = str(flow.get("id"))
        # ── V5 — flow endpoints are components (or the internet sentinel) ─────
        _check_ref("V5", subject, flow.get("source_component_id"), component_ids,
                   "source_component_id", allow_internet=True)
        _check_ref("V5", subject, flow.get("target_component_id"), component_ids,
                   "target_component_id")
        for node_id in flow.get("via", []) or []:
            _check_ref("V2", subject, node_id, infra_ids, "via node")
        # ── V7 — every flow has an inline auth_method ─────────────────────────
        if not flow.get("auth_method"):
            findings.append(Finding("V7", "error", subject,
                                    "flow is missing an inline auth_method"))

    for link in req.get("network_links", []) or []:
        subject = str(link.get("id"))
        # ── V5 — network-link endpoints are infra nodes ───────────────────────
        _check_ref("V5", subject, link.get("source_infra_id"), infra_ids, "source_infra_id")
        _check_ref("V5", subject, link.get("target_infra_id"), infra_ids, "target_infra_id")

    for auth in req.get("auth", []) or []:
        subject = str(auth.get("id"))
        _check_ref("V2", subject, auth.get("applies_to"), component_ids | infra_ids,
                   "applies_to", allow_internet=True)
        server = auth.get("auth_server")
        if isinstance(server, str) and server.upper().startswith("INF-"):
            _check_ref("V2", subject, server, infra_ids, "auth_server")

    for relation in req.get("ecosystem_relations", []) or []:
        subject = str(relation.get("id"))
        _check_ref("V2", subject, relation.get("source_system_id"), system_ids,
                   "source_system_id")
        _check_ref("V2", subject, relation.get("target_system_id"), system_ids,
                   "target_system_id")

    # ── V3 — infra containment matrix ─────────────────────────────────────────
    for infra in req.get("infra", []) or []:
        subject = str(infra.get("id"))
        kind = infra.get("node_kind")
        parent_id = infra.get("parent_id")
        if not parent_id or kind not in PARENT_ALLOWED:
            continue
        parent = infra_by_id.get(parent_id)
        if not parent:
            continue
        parent_kind = parent.get("node_kind")
        if parent_kind in PARENT_ALLOWED.get(kind, set()):
            continue
        findings.append(Finding(
            "V3", "error", subject,
            f"{kind} node {subject} cannot be contained by {parent_kind} "
            f"node {parent_id}"))

    # ── V4 — infrastructure roles are not modelled as application artefacts ───
    # The component_role enum already excludes appliance kinds (schema-enforced);
    # the role check guards future enum drift, and key_management is checked for
    # the kind of node it actually points at.
    for component in req.get("components", []) or []:
        subject = str(component.get("id"))
        role = component.get("component_role")
        if role in APPLIANCE_KINDS:
            findings.append(Finding(
                "V4", "error", subject,
                f"component_role {role!r} is an infrastructure/security appliance "
                f"role; model it as an infra L4 node instead"))
        key_management = component.get("key_management")
        if key_management:
            node = infra_by_id.get(key_management)
            if node and node.get("node_kind") != "key_management":
                findings.append(Finding(
                    "V4", "error", subject,
                    f"key_management {key_management!r} points to a "
                    f"{node.get('node_kind')!r} node, not a key_management node"))

    # ── V7 — an external entry point needs an auth row ────────────────────────
    external_flows = [f for f in req.get("flows", []) or []
                      if f.get("source_component_id") == "internet"]
    if external_flows and not req.get("auth"):
        findings.append(Finding(
            "V7", "error", "auth",
            "flows enter from the internet but no user/entry authentication "
            "(auth) row is defined"))

    return findings


# ── CLI ───────────────────────────────────────────────────────────────────────

def _load(path: str) -> dict:
    text = Path(path).read_text(encoding="utf-8")
    if path.lower().endswith(".json"):
        return json.loads(text)
    return yaml.safe_load(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a req/v2 requirements document")
    parser.add_argument("path", help="req/v2 YAML or JSON document")
    parser.add_argument("--json", action="store_true", dest="as_json",
                        help="Emit findings as JSON")
    args = parser.parse_args(argv)

    try:
        doc = _load(args.path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"ERROR: cannot read {args.path}: {exc}", file=sys.stderr)
        return 2

    findings = validate_requirements(doc)

    if args.as_json:
        print(json.dumps({"findings": [asdict(f) for f in findings],
                          "errors": sum(1 for f in findings if f.severity == "error")},
                         indent=2))
    else:
        if not findings:
            print(f"{args.path}: OK — req/v2 valid (no cross-field findings)")
        for finding in findings:
            print(f"{args.path}: {finding.severity.upper()}: [{finding.rule_id}] "
                  f"{finding.subject}: {finding.message}")

    return 1 if any(f.severity == "error" for f in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
