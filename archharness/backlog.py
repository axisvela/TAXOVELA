#!/usr/bin/env python3
"""backlog.py — turn a validation result into an ordered remediation backlog.

Every finding is joined to the model element it cites (see ``validate_check``),
so the backlog is grouped by the thing that has to change rather than by the
order a reviewer happened to write the findings in. The join is reported too: a
finding that cites an unknown element or none at all is kept, but marked, so
nobody remediates an unverifiable claim by accident.

Usage
    archharness backlog -v output/validation/validate_result.json \\
        -r output/requirements/req.yaml [-b output/designs/blueprint.yaml] [--json]

Output schema: ``backlog/v1``
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .diagrams import topology
from .validate_check import FIELD_CODE, TYPED_CODE, check_findings

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
DISPOSITION_ORDER = {"must_fix": 0, "should_fix": 1, "consider": 2}
UNANCHORED = "unanchored"


def _load(path: Path) -> dict:
    import yaml

    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    return document if isinstance(document, dict) else {}


def element_index(requirements: dict | None, blueprint: dict | None) -> dict[str, dict]:
    """Map every model id to the context a remediation needs."""
    index: dict[str, dict] = {}
    if isinstance(requirements, dict):
        req = requirements.get("requirements") or {}
        for collection in ("infra", "systems", "components", "deployments",
                           "flows", "network_links", "auth"):
            for row in req.get(collection) or []:
                if not isinstance(row, dict) or not row.get("id"):
                    continue
                index[str(row["id"])] = {
                    "kind": collection.rstrip("s"),
                    "name": str(row.get("name") or row["id"]),
                    "system_id": row.get("system_id"),
                    "infra_id": row.get("infra_id"),
                }
    if isinstance(blueprint, dict):
        for region in topology.deployment_of(blueprint):
            if not isinstance(region, dict):
                continue
            for zone in topology.region_zones(region):
                if not isinstance(zone, dict):
                    continue
                for node in zone.get("components", []) or []:
                    if not isinstance(node, dict) or not node.get("id"):
                        continue
                    index.setdefault(str(node["id"]), {
                        "kind": "blueprint-node",
                        "name": str(node.get("name") or node["id"]),
                        "zone": str(zone.get("id") or ""),
                        "region": str(region.get("id") or ""),
                    })
    return index


def build_backlog(validation: dict, requirements: dict | None = None,
                  blueprint: dict | None = None) -> dict:
    """Return a ``backlog/v1`` document for one validation result."""
    index = element_index(requirements, blueprint)
    checks = {finding["evidence"].get("issue_id"): finding
              for finding in check_findings(validation, requirements, blueprint)}

    items: list[dict] = []
    for issue in validation.get("issues") or []:
        if not isinstance(issue, dict):
            continue
        issue_id = str(issue.get("id") or "?")
        text = f"{issue.get('subject') or ''} {issue.get('evidence') or ''}"
        cited = sorted({match.group(0) for match in TYPED_CODE.finditer(text)})
        anchors = [code for code in cited if code in index]
        unknown = [code for code in cited if code not in index]
        # A field qualifier narrows the item to the column that has to change.
        fields = [f"{match.group(1)}-{int(match.group(2)):02d}.{match.group(3)}"
                  for match in FIELD_CODE.finditer(text)]

        if anchors:
            group, target = anchors[0], dict(index[anchors[0]])
            field_name = next((f.split(".", 1)[1] for f in fields
                               if f.startswith(f"{group}.")), None)
            if field_name:
                target["field"] = field_name
                group = f"{group}.{field_name}"
        else:
            group, target = UNANCHORED, {"kind": UNANCHORED, "name": issue.get("subject") or ""}

        item = {
            "id": f"BL-{len(items) + 1:03d}",
            "issue_id": issue_id,
            "rule_id": issue.get("rule_id"),
            "severity": issue.get("severity"),
            "disposition": issue.get("disposition"),
            "dimension": issue.get("dimension"),
            "subject": issue.get("subject"),
            "evidence": issue.get("evidence"),
            "confidence": issue.get("confidence"),
            "anchor": {**target, "id": anchors[0] if anchors else None},
        }
        if unknown:
            item["unverified_codes"] = unknown
        if unknown and not anchors:
            item["join_warning"] = "cites code(s) the model does not declare"
        elif not anchors:
            item["join_warning"] = "no model element cited"
        elif issue_id in checks and checks[issue_id]["rule"] == "V-03":
            item["join_warning"] = "cites the retired SYS-nn id space"
        items.append(item)

    items.sort(key=lambda item: (
        SEVERITY_ORDER.get(str(item.get("severity")), 9),
        DISPOSITION_ORDER.get(str(item.get("disposition")), 9),
        str(item.get("anchor", {}).get("id") or ""),
        str(item["issue_id"]),
    ))
    for position, item in enumerate(items, start=1):
        item["priority"] = position

    groups: dict[str, list[str]] = {}
    for item in items:
        key = str(item["anchor"].get("id") or UNANCHORED)
        groups.setdefault(key, []).append(item["id"])

    return {
        "schema_version": "backlog/v1",
        "source": validation.get("source"),
        "summary": {
            "items": len(items),
            "must_fix": sum(1 for item in items
                            if item["disposition"] == "must_fix"),
            "unanchored": sum(1 for item in items if item["anchor"]["kind"] == UNANCHORED),
            "unverified": sum(1 for item in items if item.get("unverified_codes")),
        },
        "groups": groups,
        "items": items,
    }


def render_markdown(backlog: dict) -> str:
    """Render a backlog as a reviewable markdown list."""
    lines = ["# Remediation backlog", ""]
    summary = backlog["summary"]
    lines.append(f"{summary['items']} item(s): {summary['must_fix']} must-fix, "
                 f"{summary['unanchored']} unanchored, {summary['unverified']} citing an unknown element.")
    lines.append("")
    for item in backlog["items"]:
        anchor = item["anchor"]
        label = f"{anchor.get('id')} ({anchor.get('name')})" if anchor.get("id") else UNANCHORED
        lines.append(f"## {item['priority']}. [{item['disposition']}/{item['severity']}] {label}")
        lines.append("")
        lines.append(f"- finding: {item['issue_id']} ({item['rule_id'] or 'no rule id'})")
        lines.append(f"- subject: {item['subject']}")
        lines.append(f"- evidence: {item['evidence']}")
        if item.get("join_warning"):
            lines.append(f"- ⚠ join: {item['join_warning']}")
        if item.get("unverified_codes"):
            lines.append(f"- ⚠ unknown elements: {', '.join(item['unverified_codes'])}")
        lines.append("")
    return "\n".join(lines)


def anchor_label(anchor: dict) -> str:
    name = anchor.get("name") or ""
    identifier = anchor.get("id") or UNANCHORED
    return f"{identifier} ({name})" if name else str(identifier)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a remediation backlog from a validation result")
    parser.add_argument("--validation", "-v", required=True, help="validation/v1 result file")
    parser.add_argument("--requirements", "-r", default=None, help="req/v2 requirements YAML")
    parser.add_argument("--blueprint", "-b", default=None, help="Architecture blueprint YAML")
    parser.add_argument("-o", "--output", default=None, help="Write the backlog here (JSON, or Markdown for .md)")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Print the backlog as JSON")
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

    backlog = build_backlog(validation, requirements, blueprint)
    if args.output:
        from .files import atomic_write_text

        text = (render_markdown(backlog) if args.output.endswith(".md")
                else json.dumps(backlog, indent=2))
        try:
            atomic_write_text(args.output, text)
        except OSError as exc:
            print(f"ERROR: cannot write {args.output}: {exc}", file=sys.stderr)
            return 2
        print(f"✓ backlog written: {args.output}")
    elif args.as_json:
        print(json.dumps(backlog, indent=2))
    else:
        summary = backlog["summary"]
        print(f"{summary['items']} item(s): {summary['must_fix']} must-fix, "
              f"{summary['unanchored']} unanchored")
        for item in backlog["items"][:20]:
            print(f"  {item['priority']:>3}. {anchor_label(item['anchor'])} "
                  f"[{item['disposition']}/{item['severity']}] {item['issue_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
