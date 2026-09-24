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

#: The profile that ``enforcement_bounds`` itself represents.
DEFAULT_PROFILE = "baseline"


class PolicyError(ValueError):
    """Raised when the gate policy is missing or malformed."""


def sha256_bytes(data: bytes) -> str:
    """Return the hex SHA-256 of bytes."""
    return hashlib.sha256(data).hexdigest()


def _normalise_bounds(bounds: object, label: str) -> dict:
    """Validate one set of enforcement bounds and normalise its types."""
    if not isinstance(bounds, dict):
        raise PolicyError(f"{label} must be a mapping")
    for key in ("block_threshold", "warn_threshold", "must_fix_zero_required"):
        if key not in bounds:
            raise PolicyError(f"{label} missing {key!r}")
    try:
        block = float(bounds["block_threshold"])
        warn = float(bounds["warn_threshold"])
        must_fix_zero = bool(bounds["must_fix_zero_required"])
    except (TypeError, ValueError) as exc:
        raise PolicyError(f"{label} has invalid types: {exc}") from exc
    if not block <= warn:
        raise PolicyError(
            f"{label} requires block_threshold <= warn_threshold, got {block} > {warn}"
        )
    return {"block_threshold": block, "warn_threshold": warn,
            "must_fix_zero_required": must_fix_zero}


def resolve_bounds(doc: dict, profile: str | None = None) -> tuple[dict, str]:
    """Resolve the bounds for a named profile against the baseline.

    ``enforcement_bounds`` is the baseline. A profile may tighten it freely; a
    looser profile has to say so with ``allow_looser: true`` and a rationale, so
    a gate can never be quietly relaxed.
    """
    baseline = _normalise_bounds(doc.get("enforcement_bounds"), "enforcement_bounds")
    profiles = doc.get("profiles") or {}
    name = profile or doc.get("default_profile") or DEFAULT_PROFILE
    if name == DEFAULT_PROFILE:
        return baseline, DEFAULT_PROFILE
    if name not in profiles:
        available = ", ".join([DEFAULT_PROFILE, *sorted(profiles)])
        raise PolicyError(f"unknown policy profile {name!r} (available: {available})")
    entry = profiles[name]
    selected = _normalise_bounds(entry, f"profiles.{name}")
    looser = (
        selected["block_threshold"] < baseline["block_threshold"]
        or selected["warn_threshold"] < baseline["warn_threshold"]
        or (baseline["must_fix_zero_required"] and not selected["must_fix_zero_required"])
    )
    if looser and not (isinstance(entry, dict) and entry.get("allow_looser")):
        raise PolicyError(
            f"profile {name!r} is looser than the baseline; declare "
            "allow_looser: true and a rationale"
        )
    return selected, name


def load_policy(path: str | Path, profile: str | None = None) -> tuple[dict, str, str]:
    """Load a gate policy file. Returns (bounds, digest, resolved profile name)."""
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
    bounds, name = resolve_bounds(doc, profile)
    return bounds, sha256_bytes(raw), name


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


def evaluate_files(validation_path: str | Path, policy_path: str | Path,
                   profile: str | None = None) -> dict:
    """Load files, evaluate the gate, and bind policy provenance."""
    validation = load_validation(validation_path)
    bounds, digest, resolved = load_policy(policy_path, profile)
    decision = evaluate_gate(validation, bounds)
    # The decision records which profile gated the artifact, so a later reader
    # can tell a production gate from a proof-of-concept one.
    decision["policy"]["profile"] = resolved
    decision["policy"]["path"] = str(policy_path)
    decision["policy"]["digest"] = digest
    validate(decision, "enforcement/v1")
    return decision
