#!/usr/bin/env python3
"""schema_check.py — classify a schema change before it breaks a consumer.

Contracts in this repository are versioned by identity: ``req/v2`` is a promise,
and a breaking change ships as ``req/v3`` rather than mutating ``req/v2`` under
consumers who pinned it. This command compares a schema against a baseline and
classifies each difference, so that promise is checked rather than remembered.

    breaking   a property or enum value disappeared, a property changed type, or
               a new property became required. Consumers that pinned the id
               cannot absorb this — publish a new id.
    additive   a new optional property, a widened enum, or a new definition.
               Existing consumers keep working.
    cosmetic   format, description, or ordering only.

Usage
    archharness schema-check --baseline HEAD
    archharness schema-check --baseline origin/main [--json]
    archharness schema-check --baseline previous/schemas [--strict]

Exit codes: 0 = no breaking change, 1 = a breaking change under the same id,
2 = bad invocation.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

BREAKING = "breaking"
ADDITIVE = "additive"
COSMETIC = "cosmetic"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def entities(schema: dict) -> dict[str, dict]:
    """Return ``name → {properties, required, enums, types}`` for a schema.

    Definitions and top-level properties are treated alike; an array of objects
    (``issues``) is described by the properties of its item.
    """
    found: dict[str, dict] = {}

    def describe(name: str, node: dict) -> None:
        if not isinstance(node, dict):
            return
        target = node
        if node.get("type") == "array" and isinstance(node.get("items"), dict):
            target = node["items"]
        properties = target.get("properties") or {}
        if not properties:
            return
        found[name] = {
            "properties": set(properties),
            "required": set(target.get("required") or []),
            "enums": {key: tuple(value.get("enum") or [])
                      for key, value in properties.items()
                      if isinstance(value, dict) and value.get("enum")},
            "types": {key: value.get("type")
                      for key, value in properties.items() if isinstance(value, dict)},
        }

    for name, node in (schema.get("$defs") or {}).items():
        describe(name, node)
    for name, node in (schema.get("properties") or {}).items():
        describe(name, node)
    return found


def compare_schemas(baseline: dict, candidate: dict, name: str) -> list[dict]:
    """Return the classified differences between two revisions of one schema."""
    findings: list[dict] = []
    before, after = entities(baseline), entities(candidate)

    for entity in sorted(set(before) | set(after)):
        old, new = before.get(entity), after.get(entity)
        if old and not new:
            findings.append({"kind": BREAKING, "entity": entity,
                             "detail": f"definition removed from {name}"})
            continue
        if new and not old:
            findings.append({"kind": ADDITIVE, "entity": entity,
                             "detail": f"definition added to {name}"})
            continue

        for prop in sorted(old["properties"] - new["properties"]):
            findings.append({"kind": BREAKING, "entity": entity, "property": prop,
                             "detail": f"{entity}.{prop} was removed"})
        for prop in sorted(new["properties"] - old["properties"]):
            kind = BREAKING if prop in new["required"] else ADDITIVE
            findings.append({"kind": kind, "entity": entity, "property": prop,
                             "detail": f"{entity}.{prop} was added"
                                       + (" as required" if kind == BREAKING else "")})
        for prop in sorted(new["required"] - old["required"]):
            findings.append({"kind": BREAKING, "entity": entity, "property": prop,
                             "detail": f"{entity}.{prop} became required"})
        for prop in sorted(old["required"] - new["required"]):
            findings.append({"kind": COSMETIC, "entity": entity, "property": prop,
                             "detail": f"{entity}.{prop} is no longer required"})

        for prop, old_values in old["enums"].items():
            if prop not in new["enums"]:
                continue     # handled as a removal or a type change above
            new_values = new["enums"][prop]
            missing = [value for value in old_values if value not in new_values]
            added = [value for value in new_values if value not in old_values]
            if missing:
                findings.append({"kind": BREAKING, "entity": entity, "property": prop,
                                 "detail": f"{entity}.{prop} dropped "
                                           f"{', '.join(repr(v) for v in missing)}"})
            if added:
                findings.append({"kind": ADDITIVE, "entity": entity, "property": prop,
                                 "detail": f"{entity}.{prop} accepts "
                                           f"{', '.join(repr(v) for v in added)}"})

        for prop, old_type in old["types"].items():
            new_type = new["types"].get(prop)
            if prop in new["properties"] and new_type != old_type and prop not in new["enums"]:
                findings.append({"kind": BREAKING, "entity": entity, "property": prop,
                                 "detail": f"{entity}.{prop} changed type "
                                           f"{old_type!r} → {new_type!r}"})
    return findings


def _baseline_schema(baseline: str, path: Path) -> dict | None:
    """Read the baseline revision of ``path`` from a directory or a git ref."""
    candidate_path = Path(baseline)
    if candidate_path.exists():
        if candidate_path.is_dir():
            candidate_path = candidate_path / path.name
        return _load(candidate_path) if candidate_path.is_file() else None
    # ``git show`` addresses blobs relative to the repository root, while the
    # schema path is absolute, so translate it first.
    # Schema files carry UTF-8 text, so decode explicitly rather than relying on
    # the console encoding (which is not UTF-8 on every platform).
    top = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                         capture_output=True, text=True, encoding="utf-8")
    if top.returncode != 0:
        return None
    try:
        relative = path.resolve().relative_to(Path(top.stdout.strip()).resolve())
    except ValueError:
        return None
    result = subprocess.run(["git", "show", f"{baseline}:{relative.as_posix()}"],
                            capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        return None
    return json.loads(result.stdout)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Classify schema changes against a baseline")
    parser.add_argument("--baseline", default="HEAD",
                        help="Baseline directory or git ref (default: HEAD)")
    parser.add_argument("--schema", action="append", default=None,
                        help="Schema id(s) to check (default: every schema in schemas/)")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--strict", action="store_true",
                        help="Also fail on additive changes")
    args = parser.parse_args(argv)

    from .paths import require_archharness_root

    try:
        schemas_dir = require_archharness_root() / "schemas"
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if not schemas_dir.is_dir():
        print(f"ERROR: no schemas directory at {schemas_dir}", file=sys.stderr)
        return 2

    def _resolve(name: str) -> Path:
        """Accept a schema id, a file stem, or a file name."""
        for candidate in (name, f"{name}.json", f"{name}.schema.json"):
            path = schemas_dir / candidate
            if path.is_file():
                return path
        return schemas_dir / name

    selected = (sorted(schemas_dir.glob("*.json")) if not args.schema
                else [_resolve(name) for name in args.schema])
    reports: list[dict] = []
    for path in selected:
        if not path.is_file():
            print(f"ERROR: schema not found: {path}", file=sys.stderr)
            return 2
        try:
            baseline = _baseline_schema(args.baseline, path)
        except (OSError, ValueError) as exc:
            print(f"ERROR: cannot read baseline {args.baseline} for {path.name}: {exc}",
                  file=sys.stderr)
            return 2
        if baseline is None:
            reports.append({"schema": path.name, "status": "new", "findings": []})
            continue
        findings = compare_schemas(baseline, _load(path), path.name)
        reports.append({
            "schema": path.name,
            "status": "changed" if findings else "unchanged",
            "findings": findings,
        })

    breaking = [(report["schema"], finding)
                for report in reports for finding in report["findings"]
                if finding["kind"] == BREAKING]
    additive = [(report["schema"], finding)
                for report in reports for finding in report["findings"]
                if finding["kind"] == ADDITIVE]

    if args.as_json:
        print(json.dumps({"schema_version": "schema-check/v1",
                          "baseline": args.baseline,
                          "breaking": len(breaking),
                          "additive": len(additive),
                          "reports": reports}, indent=2))
    else:
        for report in reports:
            if report["status"] == "new":
                print(f"new        {report['schema']}")
            elif report["status"] == "unchanged":
                print(f"unchanged  {report['schema']}")
            else:
                print(f"changed    {report['schema']}")
            for finding in report["findings"]:
                print(f"  {finding['kind']:<9} {finding['detail']}")
        if breaking:
            print(f"\n{len(breaking)} breaking change(s): publish a new schema id "
                  "instead of changing this one.")
        elif additive and args.strict:
            print(f"\n{len(additive)} additive change(s) rejected by --strict.")
        else:
            print("\nno breaking schema change.")

    if breaking or (args.strict and additive):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
