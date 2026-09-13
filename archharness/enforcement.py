"""Deterministic policy enforcement for validation results.

``evaluate_gate`` applies versioned enforcement bounds to a ``validation/v1``
document and returns an ``enforcement/v1`` decision. No LLM is involved:
identical inputs always produce identical decisions, making the result safe
to use as a CI gate (PASS/WARN exit 0, BLOCK exits 1).
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

import yaml

from . import __version__
from .schemas import SchemaError, validate, validate_validation_result

DECISIONS = ("PASS", "WARN", "BLOCK")


class PolicyError(ValueError):
    """Raised when the gate policy is missing or malformed."""


def sha256_bytes(data: bytes) -> str:
    """Return the hex SHA-256 of bytes."""
    return hashlib.sha256(data).hexdigest()


def load_policy(path: str | Path) -> tuple[dict, str]:
    """Load a gate policy file. Returns (bounds, hex digest of file bytes)."""
    policy_path = Path(path)
    try:
        raw = policy_path.read_bytes()
    except OSError as exc:
        raise PolicyError(f"cannot read policy file {policy_path}: {exc}") from exc
    try:
        doc = yaml.safe_load(raw) or {}
    except yaml.YAMLError as exc:
        raise PolicyError(f"invalid policy YAML {policy_path}: {exc}") from exc
    if not isinstance(doc, dict):
        raise PolicyError(f"policy root must be a mapping: {policy_path}")
    bounds = doc.get("enforcement_bounds")
    if not isinstance(bounds, dict):
        raise PolicyError(f"policy missing enforcement_bounds: {policy_path}")
    for key in ("block_threshold", "warn_threshold", "must_fix_zero_required"):
        if key not in bounds:
            raise PolicyError(f"policy enforcement_bounds missing {key!r}: {policy_path}")
    try:
        block = float(bounds["block_threshold"])
        warn = float(bounds["warn_threshold"])
        must_fix_zero = bool(bounds["must_fix_zero_required"])
    except (TypeError, ValueError) as exc:
        raise PolicyError(f"policy bounds have invalid types: {exc}") from exc
    if not block <= warn:
        raise PolicyError(
            f"policy requires block_threshold <= warn_threshold, got {block} > {warn}"
        )
    return {"block_threshold": block, "warn_threshold": warn,
            "must_fix_zero_required": must_fix_zero}, sha256_bytes(raw)


def load_validation(path: str | Path) -> dict:
    """Load and schema-validate a validation/v1 result file."""
    validation_path = Path(path)
    try:
        raw = validation_path.read_bytes()
    except OSError as exc:
        raise SchemaError(f"cannot read validation file {validation_path}: {exc}") from exc
    try:
        doc = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise SchemaError(f"invalid validation YAML {validation_path}: {exc}") from exc
    validate_validation_result(doc)
    return doc


def evaluate_gate(validation: dict, bounds: dict) -> dict:
    """Evaluate enforcement bounds against a validated result document."""
    validate_validation_result(validation)
    summary = validation["summary"]
    score = float(summary["total_score"])
    must_fix = int(summary["must_fix"])
    should_fix = int(summary.get("should_fix", 0))
    consider = int(summary.get("consider", 0))

    block_threshold = float(bounds["block_threshold"])
    warn_threshold = float(bounds["warn_threshold"])
    must_fix_zero = bool(bounds["must_fix_zero_required"])

    reasons: list[str] = []
    if must_fix_zero and must_fix > 0:
        decision = "BLOCK"
        reasons.append(f"must_fix={must_fix} > 0 (must_fix_zero_required)")
    elif score < block_threshold:
        decision = "BLOCK"
        reasons.append(f"total_score={score} < block_threshold={block_threshold}")
    elif score < warn_threshold:
        decision = "WARN"
        reasons.append(f"total_score={score} < warn_threshold={warn_threshold}")
    else:
        decision = "PASS"
        reasons.append(f"total_score={score} >= warn_threshold={warn_threshold} and must_fix={must_fix}")

    return {
        "schema_version": "enforcement/v1",
        "decision": decision,
        "validation": {
            "path": validation["source"].get("path"),
            "sha256": validation["source"]["sha256"],
            "ruleset_digest": validation["source"]["ruleset_digest"],
        },
        "policy": {
            "path": None,
            "digest": "",
            "block_threshold": block_threshold,
            "warn_threshold": warn_threshold,
            "must_fix_zero_required": must_fix_zero,
        },
        "evaluation": {
            "total_score": score,
            "must_fix": must_fix,
            "should_fix": should_fix,
            "consider": consider,
        },
        "reasons": reasons,
        "producer": f"archharness/{__version__}",
        "produced_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def evaluate_files(validation_path: str | Path, policy_path: str | Path) -> dict:
    """Load files, evaluate the gate, and bind policy provenance."""
    validation = load_validation(validation_path)
    bounds, digest = load_policy(policy_path)
    decision = evaluate_gate(validation, bounds)
    decision["policy"]["path"] = str(policy_path)
    decision["policy"]["digest"] = digest
    validate(decision, "enforcement/v1")
    return decision
