"""
merger.py — Merge multiple partial req.yaml files into one final req.yaml.

Strategy:
  1. Load all partial-req files
  2. For each logical entity (application, component, interaction):
     - Match across files by name similarity
     - Pick the highest-confidence value for each field
     - Flag conflicts (two HIGH+ sources disagree)
  3. Run gap analysis against the CRITICAL fields list
  4. Output: merged-req.yaml + gap-report.md

Usage:
    python merger.py partial-1.yaml partial-2.yaml partial-3.yaml -o merged-req.yaml --report gap-report.md
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from normalizer import (
    PartialReq, PartialApplication, PartialComponent, PartialInteraction,
    PartialUserAuth, FieldValue, Confidence, CONFIDENCE_RANK, merge_field,
    partial_req_to_yaml, fv
)


# ── Fields that MUST have values (CRITICAL gaps) ──────────────────────────────

CRITICAL_FIELDS = {
    "application": ["dc_or_region", "country", "platform"],
    "component":   ["comp_type"],
    "interaction": ["from_component", "to_component", "protocol", "auth_method"],
    "user_auth":   ["auth_server", "auth_protocol"],
    "project":     ["project_name"],
}

NON_CRITICAL_FIELDS = {
    "component":   ["language", "framework", "runtime", "sensitivity"],
    "interaction": ["port"],
    "application": ["zone_subnet", "infra_owner"],
}


# ── Name matching ─────────────────────────────────────────────────────────────

def _normalize_name(name: str) -> str:
    """Normalize a component name for fuzzy matching."""
    if not name:
        return ""
    import re
    s = re.sub(r'[^a-z0-9]', '', name.lower())
    # Remove common suffixes
    for suffix in ("service", "svc", "api", "app", "db", "database"):
        if s.endswith(suffix) and len(s) > len(suffix):
            s = s[:-len(suffix)]
    return s


def _match_by_name(items: list, name: str, threshold: float = 0.7) -> object:
    """Find the item in a list whose name most closely matches 'name'."""
    target = _normalize_name(name)
    if not target:
        return None

    best_score = 0.0
    best_item = None

    for item in items:
        item_name = ""
        fv_name = getattr(item, "name", None)
        if isinstance(fv_name, FieldValue) and fv_name.value:
            item_name = str(fv_name.value)
        elif isinstance(fv_name, str):
            item_name = fv_name

        candidate = _normalize_name(item_name)
        if not candidate:
            continue

        # Simple overlap score
        overlap = len(set(target) & set(candidate))
        score = (2 * overlap) / (len(target) + len(candidate)) if target and candidate else 0
        # Boost exact match
        if target == candidate:
            score = 1.0
        # Boost if one contains the other
        elif target in candidate or candidate in target:
            score = 0.85

        if score > best_score:
            best_score = score
            best_item = item

    return best_item if best_score >= threshold else None


# ── Field-level merge ─────────────────────────────────────────────────────────

def _merge_fv_list(field_values: list) -> FieldValue:
    """Merge a list of FieldValues (some may be None)."""
    candidates = [fv for fv in field_values if fv is not None]
    return merge_field(candidates)


def _merge_applications(all_reqs: list[PartialReq]) -> list[PartialApplication]:
    """Merge applications across all partial reqs by name matching."""
    merged: list[PartialApplication] = []
    seen_names = set()

    for req in all_reqs:
        for app in req.applications:
            name_val = app.name.value if isinstance(app.name, FieldValue) else (app.name or "")
            norm = _normalize_name(str(name_val))
            if norm and norm not in seen_names:
                seen_names.add(norm)
                # Find all versions of this app across all reqs
                versions = []
                for r in all_reqs:
                    match = _match_by_name(r.applications, str(name_val))
                    if match:
                        versions.append(match)

                merged_app = PartialApplication(id=app.id)
                merged_app.name = _merge_fv_list([v.name for v in versions])
                merged_app.type = _merge_fv_list([v.type for v in versions])
                merged_app.owner = _merge_fv_list([v.owner for v in versions])
                merged_app.dc_or_region = _merge_fv_list([v.dc_or_region for v in versions])
                merged_app.country = _merge_fv_list([v.country for v in versions])
                merged_app.platform = _merge_fv_list([v.platform for v in versions])
                merged_app.zone_subnet = _merge_fv_list([v.zone_subnet for v in versions])
                merged_app.infra_owner = _merge_fv_list([v.infra_owner for v in versions])
                merged.append(merged_app)

    return merged


def _merge_components(all_reqs: list[PartialReq]) -> list[PartialComponent]:
    merged: list[PartialComponent] = []
    seen = set()

    for req in all_reqs:
        for comp in req.components:
            name_val = comp.name.value if isinstance(comp.name, FieldValue) else (comp.name or "")
            norm = _normalize_name(str(name_val))
            if norm and norm not in seen:
                seen.add(norm)
                versions = []
                for r in all_reqs:
                    match = _match_by_name(r.components, str(name_val))
                    if match:
                        versions.append(match)

                mc = PartialComponent(id=comp.id, app_id=comp.app_id)
                mc.name = _merge_fv_list([v.name for v in versions])
                mc.comp_type = _merge_fv_list([v.comp_type for v in versions])
                mc.language = _merge_fv_list([v.language for v in versions])
                mc.framework = _merge_fv_list([v.framework for v in versions])
                mc.runtime = _merge_fv_list([v.runtime for v in versions])
                mc.sensitivity = _merge_fv_list([v.sensitivity for v in versions])
                merged.append(mc)

    return merged


def _merge_interactions(all_reqs: list[PartialReq]) -> list[PartialInteraction]:
    """Merge interactions — dedup by (from, to) pair."""
    merged: list[PartialInteraction] = []
    seen_pairs = set()

    for req in all_reqs:
        for iact in req.interactions:
            from_val = iact.from_component.value if isinstance(iact.from_component, FieldValue) else ""
            to_val   = iact.to_component.value   if isinstance(iact.to_component, FieldValue) else ""
            pair_key = (_normalize_name(str(from_val)), _normalize_name(str(to_val)))

            if pair_key not in seen_pairs and pair_key != ("", ""):
                seen_pairs.add(pair_key)
                # Collect all versions of this interaction
                versions = [i for r in all_reqs for i in r.interactions
                           if _normalize_name(str(
                               i.from_component.value if isinstance(i.from_component, FieldValue) else ""
                           )) == pair_key[0] and
                           _normalize_name(str(
                               i.to_component.value if isinstance(i.to_component, FieldValue) else ""
                           )) == pair_key[1]]

                mi = PartialInteraction(id=iact.id)
                mi.from_component = _merge_fv_list([v.from_component for v in versions])
                mi.to_component   = _merge_fv_list([v.to_component for v in versions])
                mi.protocol       = _merge_fv_list([v.protocol for v in versions])
                mi.port           = _merge_fv_list([v.port for v in versions])
                mi.auth_method    = _merge_fv_list([v.auth_method for v in versions])
                merged.append(mi)

    return merged


# ── Gap analysis ──────────────────────────────────────────────────────────────

def analyze_gaps(merged_apps: list, merged_comps: list,
                 merged_interactions: list, user_auth: list,
                 project_name: FieldValue) -> dict:
    """Identify critical and non-critical gaps in the merged requirements."""
    critical = []
    non_critical = []
    conflicts = []

    # Project-level
    if not project_name or not project_name.value:
        critical.append("Project name is missing")

    # Applications
    for app in merged_apps:
        n = app.name.value if isinstance(app.name, FieldValue) else "?"
        for f in CRITICAL_FIELDS["application"]:
            fv_val = getattr(app, f, None)
            if fv_val is None or (isinstance(fv_val, FieldValue) and not fv_val.value):
                critical.append(f"Application '{n}': {f} is missing")
            elif isinstance(fv_val, FieldValue) and "CONFLICT" in (fv_val.note or ""):
                conflicts.append(f"Application '{n}': {f} has conflict — {fv_val.note}")

    # Components
    for comp in merged_comps:
        n = comp.name.value if isinstance(comp.name, FieldValue) else "?"
        for f in CRITICAL_FIELDS["component"]:
            fv_val = getattr(comp, f, None)
            if fv_val is None or (isinstance(fv_val, FieldValue) and not fv_val.value):
                critical.append(f"Component '{n}': {f} is missing")
        for f in NON_CRITICAL_FIELDS["component"]:
            fv_val = getattr(comp, f, None)
            if fv_val is None or (isinstance(fv_val, FieldValue) and not fv_val.value):
                non_critical.append(f"Component '{n}': {f} not specified")

    # Interactions
    for iact in merged_interactions:
        fr = iact.from_component.value if isinstance(iact.from_component, FieldValue) else "?"
        to = iact.to_component.value   if isinstance(iact.to_component, FieldValue) else "?"
        label = f"{fr} → {to}"

        if not iact.auth_method or (isinstance(iact.auth_method, FieldValue) and
                                     not iact.auth_method.value):
            critical.append(f"Interaction '{label}': auth_method is missing")

        if not iact.protocol or (isinstance(iact.protocol, FieldValue) and
                                   not iact.protocol.value):
            critical.append(f"Interaction '{label}': protocol is missing")

    # User auth
    if not user_auth:
        critical.append("User authentication not defined for any entry point")

    return {
        "critical": critical,
        "non_critical": non_critical,
        "conflicts": conflicts,
    }


# ── Gap report ────────────────────────────────────────────────────────────────

def generate_gap_report(gaps: dict, sources: list[str]) -> str:
    lines = [
        f"# Requirements Gap Report",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"",
        f"## Sources merged",
    ]
    for s in sources:
        lines.append(f"  - {s}")

    lines += ["", f"## Critical gaps ({len(gaps['critical'])}) — must resolve before arch-design"]
    if gaps["critical"]:
        for g in gaps["critical"]:
            lines.append(f"  - ❌ {g}")
    else:
        lines.append("  ✓ No critical gaps")

    lines += ["", f"## Conflicts ({len(gaps['conflicts'])}) — same field, different values"]
    if gaps["conflicts"]:
        for g in gaps["conflicts"]:
            lines.append(f"  - ⚠ {g}")
    else:
        lines.append("  ✓ No conflicts detected")

    lines += ["", f"## Non-critical gaps ({len(gaps['non_critical'])}) — can be TBD"]
    if gaps["non_critical"]:
        for g in gaps["non_critical"][:20]:   # cap at 20
            lines.append(f"  - ○ {g}")
        if len(gaps["non_critical"]) > 20:
            lines.append(f"  ... and {len(gaps['non_critical']) - 20} more")
    else:
        lines.append("  ✓ All recommended fields present")

    lines += ["",
              "## Next steps",
              "1. Resolve all ❌ CRITICAL gaps (required for arch-design)",
              "2. Confirm or correct ⚠ CONFLICTS with the application owner",
              "3. Run /arch-requirements interview to fill remaining gaps",
              "4. Once gap-report shows no ❌, run /arch-design with merged-req.yaml"]

    return "\n".join(lines)


# ── Final output serialization ────────────────────────────────────────────────

def _fv_to_plain(fv_val) -> object:
    """Convert FieldValue to plain value for final req.yaml output."""
    if isinstance(fv_val, FieldValue):
        if fv_val.note and "CONFLICT" in fv_val.note:
            return f"⚠CONFLICT: {fv_val.value}  # {fv_val.note}"
        return fv_val.value
    return fv_val


def to_final_req_yaml(merged_apps, merged_comps, merged_interactions,
                      user_auth, credentials, data_encryption,
                      constraints, open_items,
                      project_name, project_id, project_scope, department) -> str:
    """Produce the final req.yaml in the standard requirements format."""

    def app_to_dict(app: PartialApplication) -> dict:
        return {
            "id": app.id,
            "name": _fv_to_plain(app.name),
            "type": _fv_to_plain(app.type) or "existing",
            "owner": _fv_to_plain(app.owner) or "org_it",
            "dc_or_region": _fv_to_plain(app.dc_or_region),
            "country": _fv_to_plain(app.country),
            "platform": _fv_to_plain(app.platform),
            "zone_subnet": _fv_to_plain(app.zone_subnet),
            "infra_owner": _fv_to_plain(app.infra_owner),
        }

    def comp_to_dict(comp: PartialComponent) -> dict:
        return {
            "id": comp.id,
            "app_id": comp.app_id,
            "name": _fv_to_plain(comp.name),
            "type": _fv_to_plain(comp.comp_type) or "BE",
            "language": _fv_to_plain(comp.language),
            "framework": _fv_to_plain(comp.framework),
            "runtime": _fv_to_plain(comp.runtime),
            "sensitivity": _fv_to_plain(comp.sensitivity),
        }

    def int_to_dict(iact: PartialInteraction) -> dict:
        return {
            "id": iact.id,
            "from_component": _fv_to_plain(iact.from_component),
            "to_component": _fv_to_plain(iact.to_component),
            "protocol": _fv_to_plain(iact.protocol),
            "port": _fv_to_plain(iact.port),
            "auth_method": _fv_to_plain(iact.auth_method) or "⚠MISSING",
        }

    def ua_to_dict(ua: PartialUserAuth) -> dict:
        return {
            "entry_point": ua.entry_point,
            "user_roles": _fv_to_plain(ua.user_roles),
            "auth_server": _fv_to_plain(ua.auth_server),
            "auth_protocol": _fv_to_plain(ua.auth_protocol),
            "authorization": _fv_to_plain(ua.authorization),
        }

    doc = {
        "requirements": {
            "project": {
                "name": _fv_to_plain(project_name),
                "id": _fv_to_plain(project_id),
                "scope": _fv_to_plain(project_scope),
                "department": _fv_to_plain(department),
            },
            "applications":       [app_to_dict(a) for a in merged_apps],
            "components":         [comp_to_dict(c) for c in merged_comps],
            "interactions":       [int_to_dict(i) for i in merged_interactions],
            "user_auth":          [ua_to_dict(u) for u in user_auth],
            "credentials":        credentials,
            "data_encryption":    data_encryption,
            "constraints":        constraints,
            "open_items":         open_items,
        }
    }
    return yaml.dump(doc, allow_unicode=True, sort_keys=False, default_flow_style=False)


# ── Main merge function ───────────────────────────────────────────────────────

def merge_partial_reqs(partial_files: list[str]) -> tuple[str, str, dict]:
    """
    Load and merge multiple partial req YAML files.
    Returns: (merged_req_yaml, gap_report_md, gaps_dict)
    """
    all_reqs: list[PartialReq] = []

    for f in partial_files:
        with open(f, encoding="utf-8") as fp:
            raw = yaml.safe_load(fp)
        # Deserialize back into PartialReq (simplified — just use as dict)
        # In production this would fully reconstruct the dataclass
        # Here we store raw dicts and treat them in merge step
        req = PartialReq.__new__(PartialReq)
        req.__dict__.update({
            "source_tool": raw.get("source_tool", ""),
            "source_file": raw.get("source_file", f),
            "project_name": raw.get("project_name"),
            "project_id": raw.get("project_id"),
            "project_scope": raw.get("project_scope"),
            "department": raw.get("department"),
            "applications": [],
            "components": [],
            "interactions": [],
            "user_auth": [],
            "credentials": raw.get("credentials", []),
            "data_encryption": raw.get("data_encryption", []),
            "network_connections": raw.get("network_connections", []),
            "constraints": raw.get("constraints", []),
            "open_items": raw.get("open_items", []),
            "gaps": raw.get("gaps", []),
            "no_coverage": raw.get("no_coverage", []),
        })

        def _to_fv(d) -> FieldValue:
            if d is None: return None
            if isinstance(d, dict) and "value" in d:
                return FieldValue(
                    value=d["value"],
                    confidence=Confidence(d.get("confidence", "unknown")),
                    source=d.get("source", ""),
                    note=d.get("note", "")
                )
            return fv(d, Confidence.UNKNOWN, "")

        for a in raw.get("applications", []):
            app = PartialApplication(id=a.get("id", ""))
            for field in ("name", "type", "owner", "vendor", "dc_or_region",
                          "country", "platform", "zone_subnet", "infra_owner"):
                setattr(app, field, _to_fv(a.get(field)))
            req.applications.append(app)

        for c in raw.get("components", []):
            comp = PartialComponent(id=c.get("id", ""), app_id=c.get("app_id", ""))
            for field in ("name", "comp_type", "language", "framework", "runtime", "sensitivity"):
                setattr(comp, field, _to_fv(c.get(field)))
            req.components.append(comp)

        for i in raw.get("interactions", []):
            iact = PartialInteraction(id=i.get("id", ""))
            for field in ("from_component", "to_component", "protocol", "port", "auth_method"):
                setattr(iact, field, _to_fv(i.get(field)))
            req.interactions.append(iact)

        all_reqs.append(req)

    merged_apps   = _merge_applications(all_reqs)
    merged_comps  = _merge_components(all_reqs)
    merged_ints   = _merge_interactions(all_reqs)

    all_user_auth = [ua for r in all_reqs for ua in r.user_auth]
    all_creds     = [c for r in all_reqs for c in r.credentials]
    all_enc       = [e for r in all_reqs for e in r.data_encryption]
    all_constraints = list(dict.fromkeys(c for r in all_reqs for c in r.constraints))
    all_open      = [o for r in all_reqs for o in r.open_items if isinstance(o, dict) and "id" in o]

    def _ensure_fv(v) -> FieldValue:
        if v is None:
            return None
        if isinstance(v, FieldValue):
            return v
        if isinstance(v, dict) and "value" in v:
            return _to_fv(v)
        return fv(v, Confidence.UNKNOWN, "")

    project_name  = merge_field([_ensure_fv(r.project_name) for r in all_reqs])
    project_id    = merge_field([_ensure_fv(r.project_id) for r in all_reqs])
    project_scope = merge_field([_ensure_fv(r.project_scope) for r in all_reqs])
    department    = merge_field([_ensure_fv(r.department) for r in all_reqs])

    gaps = analyze_gaps(merged_apps, merged_comps, merged_ints,
                        all_user_auth, project_name)

    merged_yaml = to_final_req_yaml(
        merged_apps, merged_comps, merged_ints, all_user_auth,
        all_creds, all_enc, all_constraints, all_open,
        project_name, project_id, project_scope, department
    )

    sources = [r.source_file or r.source_tool for r in all_reqs]
    gap_report = generate_gap_report(gaps, sources)

    return merged_yaml, gap_report, gaps


def main():
    parser = argparse.ArgumentParser(description="Merge partial requirement YAML files")
    parser.add_argument("files", nargs="+", help="Partial req YAML files to merge")
    parser.add_argument("-o", "--output", default="merged-req.yaml", help="Output merged req YAML")
    parser.add_argument("--report", default="gap-report.md", help="Gap report output file")
    args = parser.parse_args()

    merged_yaml, gap_report, gaps = merge_partial_reqs(args.files)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(merged_yaml)
    print(f"✓ Merged requirements: {args.output}")

    with open(args.report, "w", encoding="utf-8") as f:
        f.write(gap_report)
    print(f"✓ Gap report: {args.report}")

    n_critical = len(gaps["critical"])
    n_conflict = len(gaps["conflicts"])
    print(f"  Critical gaps: {n_critical}  |  Conflicts: {n_conflict}")
    if n_critical == 0:
        print("  ✓ Ready for arch-design")
    else:
        print(f"  ✗ Resolve {n_critical} critical gaps before running arch-design")


if __name__ == "__main__":
    main()
