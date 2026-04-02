"""
normalizer.py — Shared data model for partial requirements extraction.

Every reader (diagram, document, API, vision) outputs a PartialReq object.
The merger combines multiple PartialReq objects into a final req.yaml.

Confidence levels:
  HIGH   — from a system of record (CMDB, structured file with clear schema)
  MEDIUM — from a document or structured diagram (draw.io, D2, YAML)
  LOW    — from vision OCR, unstructured text, inferred values
  MANUAL — explicitly confirmed by the user (overrides everything)
"""

from __future__ import annotations
import json
import yaml
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional


class Confidence(str, Enum):
    MANUAL = "manual"    # user confirmed
    HIGH   = "high"      # system of record
    MEDIUM = "medium"    # structured file / diagram
    LOW    = "low"       # vision / unstructured text
    UNKNOWN = "unknown"  # no source


CONFIDENCE_RANK = {
    Confidence.MANUAL:  5,
    Confidence.HIGH:    4,
    Confidence.MEDIUM:  3,
    Confidence.LOW:     2,
    Confidence.UNKNOWN: 1,
}


@dataclass
class FieldValue:
    """A single extracted field with provenance."""
    value: object
    confidence: Confidence = Confidence.UNKNOWN
    source: str = ""          # e.g. "CMDB:ServiceNow", "diagram:drawio", "vision:claude"
    note: str = ""


@dataclass
class PartialApplication:
    id: str
    name: FieldValue = None
    type: FieldValue = None             # new | existing | modified
    owner: FieldValue = None            # org_it | biz_owned | third_party
    vendor: FieldValue = None
    dc_or_region: FieldValue = None     # e.g. "Hohhot DC [CN]"
    country: FieldValue = None
    platform: FieldValue = None         # private_dc | aws | azure | saas
    zone_subnet: FieldValue = None
    infra_owner: FieldValue = None      # InfraSec | BizIT | ThirdParty


@dataclass
class PartialComponent:
    id: str
    app_id: str = ""
    name: FieldValue = None
    comp_type: FieldValue = None        # FE | BE | DB | MQ | IP | LB | SEC
    language: FieldValue = None
    framework: FieldValue = None
    runtime: FieldValue = None
    sensitivity: FieldValue = None


@dataclass
class PartialInteraction:
    id: str
    from_component: str = ""
    to_component: str = ""
    protocol: FieldValue = None
    port: FieldValue = None
    auth_method: FieldValue = None
    notes: FieldValue = None


@dataclass
class PartialUserAuth:
    entry_point: str = ""
    user_roles: FieldValue = None
    auth_server: FieldValue = None
    auth_protocol: FieldValue = None
    authorization: FieldValue = None
    auth_platform: FieldValue = None


@dataclass
class PartialReq:
    """Output of a single reader. May be incomplete."""
    source_tool: str = ""       # which reader produced this
    source_file: str = ""       # file path or API endpoint

    project_name: FieldValue = None
    project_id: FieldValue = None
    project_scope: FieldValue = None    # standalone | e2e
    department: FieldValue = None

    applications: list[PartialApplication] = field(default_factory=list)
    components: list[PartialComponent]    = field(default_factory=list)
    interactions: list[PartialInteraction] = field(default_factory=list)
    user_auth: list[PartialUserAuth]       = field(default_factory=list)
    credentials: list[dict]               = field(default_factory=list)
    data_encryption: list[dict]           = field(default_factory=list)
    network_connections: list[dict]       = field(default_factory=list)
    constraints: list[str]               = field(default_factory=list)
    open_items: list[dict]               = field(default_factory=list)

    # Gaps identified by this reader
    gaps: list[str] = field(default_factory=list)
    # Fields where this reader has no data (honest about coverage)
    no_coverage: list[str] = field(default_factory=list)


# ── Serialization helpers ─────────────────────────────────────────────────────

def fv(value, confidence: Confidence, source: str, note: str = "") -> FieldValue:
    """Shorthand for FieldValue construction."""
    return FieldValue(value=value, confidence=confidence, source=source, note=note)


def to_dict(obj) -> dict:
    """Recursively convert dataclass + FieldValue to plain dict."""
    if isinstance(obj, FieldValue):
        return {"value": obj.value, "confidence": obj.confidence.value,
                "source": obj.source, "note": obj.note}
    if isinstance(obj, Enum):
        return obj.value
    if hasattr(obj, "__dataclass_fields__"):
        return {k: to_dict(v) for k, v in asdict(obj).items()}
    if isinstance(obj, list):
        return [to_dict(i) for i in obj]
    if isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}
    return obj


def partial_req_to_yaml(req: PartialReq) -> str:
    """Serialise a PartialReq to YAML string."""
    return yaml.dump(to_dict(req), allow_unicode=True, sort_keys=False, default_flow_style=False)


def merge_field(fields: list[Optional[FieldValue]]) -> Optional[FieldValue]:
    """
    Merge multiple FieldValues for the same logical field.
    Returns the highest-confidence non-None value.
    Marks CONFLICT if two HIGH-or-above sources disagree.
    """
    candidates = [f for f in fields if f is not None and f.value is not None]
    if not candidates:
        return None
    # Sort by confidence descending
    ranked = sorted(candidates, key=lambda f: CONFIDENCE_RANK.get(f.confidence, 0), reverse=True)
    best = ranked[0]

    # Check for conflict: any other HIGH+ source with a different value?
    top_rank = CONFIDENCE_RANK.get(best.confidence, 0)
    conflicts = [
        f for f in ranked[1:]
        if CONFIDENCE_RANK.get(f.confidence, 0) >= 3   # MEDIUM or above
        and str(f.value).strip().lower() != str(best.value).strip().lower()
    ]
    if conflicts:
        conflict_note = f"CONFLICT: {best.source}={best.value!r} vs " + \
                        ", ".join(f"{c.source}={c.value!r}" for c in conflicts)
        return FieldValue(
            value=best.value,
            confidence=Confidence.LOW,
            source=best.source,
            note=conflict_note,
        )
    return best
