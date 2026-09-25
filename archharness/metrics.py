"""Governance metrics (``metrics/v1``): aggregate counts, never architecture payloads.

Measures the four things the roadmap asks for — workflow completion, validation
finding categories, routing/readability defects, and review turnaround — from
the artifacts a project already records. The roll-up deliberately contains no
entity names, ids, subjects, evidence, notes, or artifact paths: only counts,
fixed enums, and standard rule/dimension labels. That makes it safe to hand to
an external governance dashboard (for example AXISRobo-PAMP's review analytics)
without leaking an architecture.

The module is pure and offline. ``summarize`` takes already-parsed documents;
``discover_documents`` finds them under a project tree; ``render_markdown``
renders the human view.
"""

from __future__ import annotations

import json
import statistics
from datetime import datetime, timezone
from pathlib import Path

import yaml

from .schemas import validate

METRICS_SCHEMA = "metrics/v1"

SEVERITIES = ("critical", "high", "medium", "low")
DISPOSITIONS = ("must_fix", "should_fix", "consider")
WAYPOINT_BUCKETS = ("<=2", "3-5", ">=6")
READABILITY_WAYPOINTS = 6

PRIVACY_NOTE = (
    "Aggregate counts, fixed enums, and standard rule/dimension labels only. "
    "No entity names, ids, subjects, evidence, notes, or artifact paths are "
    "included, so the roll-up can be shared without exposing architecture."
)

# schema_version -> the bucket discover_documents classifies it into
_SCHEMA_BUCKETS = {
    "validation/v1": "validation",
    "enforcement/v1": "enforcement",
    "routing-diagnostics/v1": "routing",
    "artifact/v1": "manifests",
}


# ── Loading and discovery ─────────────────────────────────────────────────────

def _load(path: str | Path) -> dict | None:
    """Read one JSON/YAML document, or return None when it is unreadable.

    Metrics must never fail the pipeline because one stray file is malformed;
    an unreadable document is simply not counted.
    """
    p = Path(path)
    try:
        text = p.read_text(encoding="utf-8")
    except OSError:
        return None
    try:
        doc = yaml.safe_load(text) if p.suffix.lower() in (".yaml", ".yml") else json.loads(text)
    except (ValueError, yaml.YAMLError):
        return None
    return doc if isinstance(doc, dict) else None


def load_documents(paths, schema_id: str | None = None) -> list[dict]:
    """Load an explicit list of documents, skipping unreadable ones.

    When ``schema_id`` is given, only documents declaring that ``schema_version``
    are kept, so a mis-supplied file is ignored rather than miscounted.
    """
    documents = [doc for doc in (_load(path) for path in (paths or [])) if doc is not None]
    if schema_id is not None:
        documents = [doc for doc in documents if doc.get("schema_version") == schema_id]
    return documents


def discover_documents(roots) -> dict[str, list[dict]]:
    """Classify every governance document under ``roots`` by ``schema_version``.

    Returns a dict with ``validation``, ``enforcement``, ``routing``, and
    ``manifests`` lists. Files without a recognised contract are ignored, so a
    project that also holds gap reports or arbitrary JSON is unaffected.
    """
    found: dict[str, list[dict]] = {key: [] for key in
                                    ("validation", "enforcement", "routing", "manifests")}
    if isinstance(roots, (str, Path)):
        roots = [roots]
    for root in roots:
        directory = Path(root)
        if not directory.is_dir():
            continue
        for path in sorted(directory.rglob("*.json")):
            doc = _load(path)
            if doc is None:
                continue
            bucket = _SCHEMA_BUCKETS.get(doc.get("schema_version"))
            if bucket:
                found[bucket].append(doc)
    return found


# ── Aggregation helpers ───────────────────────────────────────────────────────

def _bump(table: dict, key) -> None:
    token = key if isinstance(key, str) and key else "unclassified"
    table[token] = table.get(token, 0) + 1


def _rule_family(issue: dict) -> str:
    """Group a finding by the leading token of its rule id (``E-GCP-001`` -> ``E``)."""
    rule = issue.get("rule_id") or issue.get("id")
    if not isinstance(rule, str) or not rule.strip():
        return "unclassified"
    return rule.split("-", 1)[0].strip().upper() or "unclassified"


def _number(value) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _validation_metrics(reports: list[dict]) -> dict:
    by_severity = {name: 0 for name in SEVERITIES}
    by_disposition = {name: 0 for name in DISPOSITIONS}
    by_dimension: dict[str, int] = {}
    by_rule_family: dict[str, int] = {}
    findings = 0
    scores: list[float] = []

    for report in reports:
        for issue in report.get("issues") or []:
            if not isinstance(issue, dict):
                continue
            findings += 1
            _bump(by_severity, issue.get("severity"))
            _bump(by_disposition, issue.get("disposition"))
            _bump(by_dimension, issue.get("dimension") or "unclassified")
            _bump(by_rule_family, _rule_family(issue))
        summary = report.get("summary")
        if isinstance(summary, dict):
            score = _number(summary.get("total_score"))
            if score is not None:
                scores.append(score)

    return {
        "reports": len(reports),
        "findings_total": findings,
        "by_severity": by_severity,
        "by_disposition": by_disposition,
        "by_dimension": by_dimension,
        "by_rule_family": by_rule_family,
        "scores": {
            "samples": len(scores),
            "mean_total_score": round(statistics.fmean(scores), 4) if scores else None,
            "min_total_score": min(scores) if scores else None,
            "max_total_score": max(scores) if scores else None,
            "must_fix": by_disposition.get("must_fix", 0),
        },
    }


def _routing_metrics(reports: list[dict]) -> dict:
    by_strategy: dict[str, int] = {}
    buckets = {name: 0 for name in WAYPOINT_BUCKETS}
    edges = 0
    fallbacks = 0
    defects = 0
    total_ns = 0.0

    for report in reports:
        routes = report.get("routes")
        if not isinstance(routes, list):
            continue
        for route in routes:
            if not isinstance(route, dict):
                continue
            edges += 1
            if route.get("fallback"):
                fallbacks += 1
                defects += 1
            _bump(by_strategy, route.get("strategy"))
            waypoints = route.get("waypoint_count")
            if isinstance(waypoints, int) and not isinstance(waypoints, bool):
                if waypoints <= 2:
                    buckets["<=2"] += 1
                elif waypoints <= 5:
                    buckets["3-5"] += 1
                else:
                    buckets[">=6"] += 1
                if waypoints >= READABILITY_WAYPOINTS:
                    defects += 1
            duration = _number(route.get("duration_ns"))
            if duration is not None:
                total_ns += duration

    return {
        "reports": len(reports),
        "edges_total": edges,
        "fallback_edges": fallbacks,
        "fallback_ratio": round(fallbacks / edges, 4) if edges else 0.0,
        "by_strategy": by_strategy,
        "waypoint_buckets": buckets,
        "readability_defects": defects,
        "total_planning_ms": round(total_ns / 1_000_000, 3),
    }


# ── Turnaround ────────────────────────────────────────────────────────────────

def _parse_ts(value) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _record_earliest(times: dict[str, datetime], stage: str, moment: datetime) -> None:
    current = times.get(stage)
    if current is None or moment < current:
        times[stage] = moment


def _produced_stage_map(spec: dict | None) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for stage in (spec or {}).get("pipeline", []) or []:
        for name in stage.get("produces", []) or []:
            mapping.setdefault(name, stage.get("id"))
    return mapping


def _stage_times(state, spec, validations, enforcements, manifests) -> dict[str, datetime]:
    times: dict[str, datetime] = {}
    produced = _produced_stage_map(spec)

    artifacts = (state or {}).get("artifacts") or {}
    for name, entry in artifacts.items():
        if not isinstance(entry, dict) or entry.get("kind") != "manifest":
            continue
        stage = produced.get(name)
        moment = _parse_ts((entry.get("data") or {}).get("produced_at"))
        if stage and moment:
            _record_earliest(times, stage, moment)

    for manifest in manifests or []:
        stage = produced.get(Path(str(manifest.get("path", ""))).name) or \
            produced.get(str(manifest.get("id", "")))
        moment = _parse_ts(manifest.get("produced_at"))
        if stage and moment:
            _record_earliest(times, stage, moment)

    for report in validations:
        moment = _parse_ts((report.get("source") or {}).get("validated_at"))
        if moment:
            _record_earliest(times, "validate", moment)
    for decision in enforcements:
        moment = _parse_ts(decision.get("produced_at"))
        if moment:
            _record_earliest(times, "enforce", moment)
    return times


def _turnaround_metrics(state, spec, validations, enforcements, manifests) -> dict:
    times = _stage_times(state, spec, validations, enforcements, manifests)
    order = [stage.get("id") for stage in (spec or {}).get("pipeline", []) or []]
    samples: dict[str, list[float]] = {}
    for earlier, later in zip(order, order[1:]):
        start, end = times.get(earlier), times.get(later)
        if start and end and end >= start:
            samples.setdefault(f"{earlier}->{later}", []).append((end - start).total_seconds())
    return {
        "transitions": {
            key: {"samples": len(values), "median_seconds": round(statistics.median(values), 3)}
            for key, values in samples.items()
        }
    }


# ── Workflow ──────────────────────────────────────────────────────────────────

def _workflow_metrics(state, spec, base_dir) -> dict:
    from .workflow import can_start, check_state_integrity

    order = [stage.get("id") for stage in (spec or {}).get("pipeline", []) or []]
    state = state or {}
    recorded = state.get("artifacts") or {}
    completed_set = set(state.get("stages_completed") or [])

    ready = 0
    if order:
        for stage_id in order:
            try:
                if can_start(stage_id, state, spec)[0]:
                    ready += 1
            except Exception:  # noqa: BLE001 - a broken spec must not abort metrics
                continue

    enforce = None
    entry = recorded.get("enforce_result.json")
    if isinstance(entry, dict) and entry.get("kind") == "decision":
        decision = (entry.get("data") or {}).get("decision")
        if decision in ("PASS", "WARN", "BLOCK"):
            enforce = decision

    integrity = 0
    if base_dir is not None and state:
        integrity = len(check_state_integrity(state, base_dir))

    total = len(order)
    done = sum(1 for stage_id in order if stage_id in completed_set)
    return {
        "stages_total": total,
        "stages_completed": done,
        "completion_ratio": round(done / total, 4) if total else 0.0,
        "stages_ready": ready,
        "artifacts_recorded": len(recorded),
        "integrity_failures": integrity,
        "enforce_decision": enforce,
    }


# ── Public API ────────────────────────────────────────────────────────────────

def summarize(*, validations=(), enforcements=(), routings=(), manifests=(),
              state=None, spec=None, base_dir=None, generated_at=None) -> dict:
    """Build a validated ``metrics/v1`` roll-up from already-parsed documents.

    ``generated_at`` is injectable so callers (and tests) can be deterministic.
    """
    validations = [doc for doc in validations if isinstance(doc, dict)]
    enforcements = [doc for doc in enforcements if isinstance(doc, dict)]
    routings = [doc for doc in routings if isinstance(doc, dict)]
    manifests = [doc for doc in manifests if isinstance(doc, dict)]

    recorded_manifests = sum(
        1 for entry in ((state or {}).get("artifacts") or {}).values()
        if isinstance(entry, dict) and entry.get("kind") == "manifest"
    )
    moment = generated_at or datetime.now(timezone.utc)

    document = {
        "schema_version": METRICS_SCHEMA,
        "generated_at": moment.isoformat(timespec="seconds"),
        "scope": {
            "projects": 1 if base_dir is not None else 0,
            "validation_reports": len(validations),
            "enforcement_decisions": len(enforcements),
            "routing_reports": len(routings),
            "manifests": recorded_manifests + len(manifests),
        },
        "workflow": _workflow_metrics(state, spec, base_dir),
        "validation": _validation_metrics(validations),
        "routing": _routing_metrics(routings),
        "turnaround": _turnaround_metrics(state, spec, validations, enforcements, manifests),
        "privacy": {"payload_fields": "excluded", "note": PRIVACY_NOTE},
    }
    validate(document, METRICS_SCHEMA)
    return document


def render_markdown(document: dict) -> str:
    """Render a metrics roll-up as a concise human-readable report."""
    workflow = document.get("workflow", {})
    validation = document.get("validation", {})
    routing = document.get("routing", {})
    scores = validation.get("scores", {})
    lines = [
        "# Governance metrics",
        "",
        f"- generated: {document.get('generated_at', '')}",
        f"- scope: {document.get('scope', {})}",
        "",
        "## Workflow",
        f"- stages: {workflow.get('stages_completed')}/{workflow.get('stages_total')}"
        f" ({workflow.get('completion_ratio')})",
        f"- ready to start: {workflow.get('stages_ready')};"
        f" enforce: {workflow.get('enforce_decision')}",
        f"- recorded artifacts: {workflow.get('artifacts_recorded')};"
        f" integrity failures: {workflow.get('integrity_failures')}",
        "",
        "## Validation",
        f"- reports: {validation.get('reports')}; findings: {validation.get('findings_total')}",
        f"- by severity: {validation.get('by_severity', {})}",
        f"- by disposition: {validation.get('by_disposition', {})}",
        f"- by rule family: {validation.get('by_rule_family', {})}",
        f"- score mean/min/max: {scores.get('mean_total_score')}"
        f" / {scores.get('min_total_score')} / {scores.get('max_total_score')}",
        "",
        "## Routing",
        f"- edges: {routing.get('edges_total')}; fallbacks: {routing.get('fallback_edges')}"
        f" ({routing.get('fallback_ratio')})",
        f"- by strategy: {routing.get('by_strategy', {})}",
        f"- waypoints: {routing.get('waypoint_buckets', {})};"
        f" readability defects: {routing.get('readability_defects')}",
        "",
        "## Turnaround",
    ]
    transitions = document.get("turnaround", {}).get("transitions", {})
    if transitions:
        for key, value in transitions.items():
            lines.append(f"- {key}: median {value.get('median_seconds')}s"
                         f" (n={value.get('samples')})")
    else:
        lines.append("- no stage timestamps recorded yet")
    lines += ["", "## Privacy", f"- {document.get('privacy', {}).get('note', '')}", ""]
    return "\n".join(lines)
