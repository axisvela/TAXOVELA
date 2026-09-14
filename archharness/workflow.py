"""Executable workflow state machine for the ArchHarness pipeline.

The pipeline order is declared in ``standards/workflow.yaml``. This module
makes it mechanical: a stage may start only when every artifact in its
``requires`` list is recorded (manifest or decision), and stages downstream
of the enforce gate additionally require a recorded PASS or WARN decision.
A BLOCK decision halts the pipeline until re-validation.

State lives in ``<working>/workflow-state.json`` (or the current directory
when no project context applies)::

    {
      "artifacts": {
        "req.yaml": {"kind": "manifest", "data": {...artifact/v1...}},
        "enforce_result.json": {"kind": "decision", "data": {...enforcement/v1...}}
      },
      "stages_completed": ["requirements", "design"]
    }
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from .artifacts import verify_manifest
from .schemas import SchemaError, validate_enforcement_result, validate_manifest

STATE_FILENAME = "workflow-state.json"

# Stages that must not run unless the enforce gate recorded PASS or WARN.
# workflow.yaml declares this for security/review via on_pass/on_warn; the
# documented pipeline order (security + review -> optimize -> report)
# extends the same rule to optimize and report.
GATED_STAGES = ("security", "review", "optimize", "report")


class WorkflowError(ValueError):
    """Raised for unknown stages, bad state, or unverifiable artifacts."""


def workflow_spec_path() -> Path:
    """Locate standards/workflow.yaml (checkout or installed package data)."""
    from .paths import require_archharness_root

    return require_archharness_root() / "standards" / "workflow.yaml"


def load_spec() -> dict:
    """Load and minimally validate the pipeline specification."""
    path = workflow_spec_path()
    try:
        spec = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except OSError as exc:
        raise WorkflowError(f"cannot read workflow spec {path}: {exc}") from exc
    if not isinstance(spec, dict) or not isinstance(spec.get("pipeline"), list):
        raise WorkflowError(f"invalid workflow spec: {path}")
    return spec


def stage_ids(spec: dict) -> list[str]:
    """Return stage ids in pipeline order."""
    return [stage["id"] for stage in spec["pipeline"]]


def find_stage(spec: dict, stage_id: str) -> dict:
    """Return the stage mapping or raise WorkflowError."""
    for stage in spec["pipeline"]:
        if stage.get("id") == stage_id:
            return stage
    raise WorkflowError(f"unknown stage: {stage_id!r} (known: {', '.join(stage_ids(spec))})")


def _resource_satisfies(name: str) -> bool:
    """Check whether a required name is a shipped resource, not a project artifact."""
    from .paths import find_archharness_root

    root = find_archharness_root()
    if root is None:
        return False
    return (root / "standards" / name).is_file() or (root / name).is_file()


def load_state(path: str | Path) -> dict:
    """Load workflow state; a missing file means an empty pipeline."""
    state_path = Path(path)
    if not state_path.is_file():
        return {"artifacts": {}, "stages_completed": []}
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise WorkflowError(f"cannot read workflow state {state_path}: {exc}") from exc
    if not isinstance(state, dict):
        raise WorkflowError(f"invalid workflow state: {state_path}")
    state.setdefault("artifacts", {})
    state.setdefault("stages_completed", [])
    return state


def save_state(path: str | Path, state: dict) -> None:
    """Persist workflow state atomically (creates parent directories)."""
    from .files import atomic_write_text

    atomic_write_text(path, json.dumps(state, indent=2))


def enforce_decision(state: dict) -> str | None:
    """Return the recorded enforce decision, if any."""
    entry = state.get("artifacts", {}).get("enforce_result.json")
    if not isinstance(entry, dict) or entry.get("kind") != "decision":
        return None
    decision = entry.get("data", {}).get("decision")
    return decision if decision in ("PASS", "WARN", "BLOCK") else None


def can_start(stage_id: str, state: dict, spec: dict | None = None) -> tuple[bool, list[str], str | None]:
    """Check whether a stage may start.

    Returns (ok, missing, blocked_reason). ``missing`` lists required
    artifacts with neither a manifest nor a decision recorded (shipped
    resources such as arch-gate-policy.yaml resolve automatically).
    ``blocked_reason`` is set when the enforce gate halts the stage.
    """
    spec = spec or load_spec()
    stage = find_stage(spec, stage_id)
    recorded = state.get("artifacts", {})
    missing = [name for name in stage.get("requires", []) or []
               if name not in recorded and not _resource_satisfies(name)]
    if missing:
        return False, missing, None
    if stage_id in GATED_STAGES:
        decision = enforce_decision(state)
        if decision is None:
            return False, [], "no enforce decision recorded (run `archharness enforce` first)"
        if decision == "BLOCK":
            return False, [], "enforce decision is BLOCK (fix findings and re-validate first)"
    return True, [], None


def record_artifact(state: dict, name: str, doc: dict, base_dir: str | Path | None = None) -> dict:
    """Record a manifest (artifact/v1) or decision (enforcement/v1) under ``name``.

    Manifests are hash-verified against ``base_dir`` when given. Returns the
    updated state.
    """
    if not isinstance(doc, dict):
        raise WorkflowError(f"artifact document for {name!r} must be a mapping")
    version = doc.get("schema_version")
    if version == "artifact/v1":
        try:
            validate_manifest(doc)
        except SchemaError as exc:
            raise WorkflowError(f"invalid manifest for {name!r}: {exc}") from exc
        if base_dir is not None and not verify_manifest(doc, base_dir):
            raise WorkflowError(f"manifest for {name!r} does not match file on disk")
        entry = {"kind": "manifest", "data": doc}
    elif version == "enforcement/v1":
        try:
            validate_enforcement_result(doc)
        except SchemaError as exc:
            raise WorkflowError(f"invalid enforcement decision for {name!r}: {exc}") from exc
        entry = {"kind": "decision", "data": doc}
    else:
        raise WorkflowError(
            f"cannot record {name!r}: unsupported schema_version {version!r} "
            "(expected artifact/v1 or enforcement/v1)"
        )
    state.setdefault("artifacts", {})[name] = entry
    return state


def complete_stage(stage_id: str, state: dict, spec: dict | None = None) -> dict:
    """Mark a stage complete after verifying it may start. Returns state."""
    spec = spec or load_spec()
    find_stage(spec, stage_id)  # raises on unknown stage
    ok, missing, blocked = can_start(stage_id, state, spec)
    if not ok:
        detail = f"missing: {', '.join(missing)}" if missing else blocked
        raise WorkflowError(f"stage {stage_id!r} may not complete ({detail})")
    completed = state.setdefault("stages_completed", [])
    if stage_id not in completed:
        completed.append(stage_id)
    return state


def status_rows(state: dict, spec: dict | None = None) -> list[dict]:
    """Return per-stage readiness rows for display."""
    spec = spec or load_spec()
    rows = []
    for stage_id in stage_ids(spec):
        ok, missing, blocked = can_start(stage_id, state, spec)
        rows.append({
            "stage": stage_id,
            "completed": stage_id in state.get("stages_completed", []),
            "ready": ok,
            "missing": missing,
            "blocked": blocked,
        })
    return rows
