"""
normalizer.py — Shared data model for partial requirements extraction (req/v2).

Every reader (diagram, document, API, vision) outputs a PartialReq object.
The merger combines multiple PartialReq objects into a final req/v2 req.yaml.

The partial model stores **entity names as references** (``system``, ``infra``,
``component`` …), because that is what extraction produces. The merger resolves
those names to typed IDs (``APP-nn``, ``INF-nn``, ``CMP-nn`` …) when it emits the
final contract.

Confidence levels:
  HIGH   — from a system of record (CMDB, structured file with clear schema)
  MEDIUM — from a document or structured diagram (draw.io, D2, YAML)
  LOW    — from vision OCR, unstructured text, inferred values
  MANUAL — explicitly confirmed by the user (overrides everything)
"""

from __future__ import annotations
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


# ── Partial entities (req/v2) ─────────────────────────────────────────────────
# References between entities are stored as names; the merger resolves them to
# typed IDs. Each entity keeps a local id for de-duplication only.

@dataclass
class PartialInfra:
    id: str = ""
    name: FieldValue = None
    node_kind: FieldValue = None        # region | data_center | iaas_vpc_vnet | … | firewall | identity_provider
    infra_type: FieldValue = None       # private_cloud | public_cloud | saas | third_party | office | factory | lab
    network_type: FieldValue = None     # office_network | factory_network | lab_network | prod_network | dmz
    parent: FieldValue = None           # name ref to another infra node
    country: FieldValue = None
    vendor: FieldValue = None
    infra_owner: FieldValue = None


@dataclass
class PartialSystem:
    id: str = ""
    name: FieldValue = None
    type: FieldValue = None             # new | existing | modified
    owner: FieldValue = None            # org_it | biz_owned | third_party
    vendor: FieldValue = None
    data_classification: FieldValue = None


@dataclass
class PartialComponent:
    id: str = ""
    system: FieldValue = None           # name ref to a system
    name: FieldValue = None
    kind: FieldValue = None             # service | component
    layer: FieldValue = None            # fe | be | api | bff | db | mq | ip | lb | bc
    component_role: FieldValue = None   # backend_service | web_frontend | database | …
    function_desc: FieldValue = None
    sensitivity: FieldValue = None
    encryption_at_rest: FieldValue = None
    key_management: FieldValue = None   # name ref to a key_management infra node


@dataclass
class PartialStack:
    id: str = ""
    component: FieldValue = None        # name ref to a component
    component_name: FieldValue = None   # technology name, e.g. "Spring Boot"
    component_package: FieldValue = None
    version: FieldValue = None
    category: FieldValue = None
    license: FieldValue = None
    eol_date: FieldValue = None
    standard_flag: FieldValue = None


@dataclass
class PartialDeployment:
    id: str = ""
    component: FieldValue = None        # name ref to a component
    environment: FieldValue = None      # dev | test | staging | prod | dr
    deployment_type: FieldValue = None  # private_cloud | public_cloud | public_cloud_paas | saas | third_party
    location_type: FieldValue = None    # data_center | public_cloud_region | saas
    infra: FieldValue = None            # name ref to an infra node
    runtime_type: FieldValue = None     # vm | container | physical | serverless
    runtime_detail: FieldValue = None
    instance_count: FieldValue = None


@dataclass
class PartialFlow:
    id: str = ""
    source: FieldValue = None           # name ref to a component, or "internet"
    target: FieldValue = None           # name ref to a component
    protocol: FieldValue = None
    port: FieldValue = None
    auth_method: FieldValue = None      # inline enum (service-to-service)
    encryption: FieldValue = None       # TLS1.3 | TLS1.2 | mTLS | IPSec | none | TBD
    cross_border: FieldValue = None
    cross_border_basis: FieldValue = None
    via: FieldValue = None              # name refs to infra L4 nodes, ordered
    notes: FieldValue = None


@dataclass
class PartialNetworkLink:
    id: str = ""
    source_infra: FieldValue = None     # name ref to an infra node
    target_infra: FieldValue = None     # name ref to an infra node
    method: FieldValue = None           # mpls | expressroute | direct_connect | vpc_peering | vpn | internet | …
    bandwidth: FieldValue = None
    encrypted: FieldValue = None
    encryption_method: FieldValue = None
    managed_by: FieldValue = None
    redundancy: FieldValue = None       # primary | secondary | backup
    notes: FieldValue = None


@dataclass
class PartialAuth:
    id: str = ""
    subject: FieldValue = None          # user | application
    applies_to: FieldValue = None       # name ref to an entry point (component/infra/internet)
    auth_server: FieldValue = None      # name ref to an identity_provider infra node
    protocol: FieldValue = None         # OIDC | OAuth2_AuthCode | SAML2 | CAS | Kerberos | Basic | ApiKey
    authorization: FieldValue = None    # RBAC | ABAC | PBAC | DAC
    authorization_platform: FieldValue = None
    user_roles: FieldValue = None
    mfa: FieldValue = None
    notes: FieldValue = None


@dataclass
class PartialEcosystemRelation:
    id: str = ""
    source_system: FieldValue = None    # name ref to a system
    target_system: FieldValue = None    # name ref to a system
    relation_type: FieldValue = None    # upstream | downstream | partner | customer
    notes: FieldValue = None


@dataclass
class PartialReq:
    """Output of a single reader. May be incomplete."""
    source_tool: str = ""       # which reader produced this
    source_file: str = ""       # file path or API endpoint

    project_name: FieldValue = None
    project_id: FieldValue = None
    project_scope: FieldValue = None    # standalone | modification | e2e
    department: FieldValue = None
    data_classification: FieldValue = None

    infra: list[PartialInfra] = field(default_factory=list)
    systems: list[PartialSystem] = field(default_factory=list)
    components: list[PartialComponent] = field(default_factory=list)
    stacks: list[PartialStack] = field(default_factory=list)
    deployments: list[PartialDeployment] = field(default_factory=list)
    flows: list[PartialFlow] = field(default_factory=list)
    network_links: list[PartialNetworkLink] = field(default_factory=list)
    auth: list[PartialAuth] = field(default_factory=list)
    ecosystem_relations: list[PartialEcosystemRelation] = field(default_factory=list)

    credentials: list[dict] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    open_items: list[dict] = field(default_factory=list)

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
    candidates = [f for f in fields if f is not None and getattr(f, "value", None) is not None]
    if not candidates:
        return None
    ranked = sorted(candidates, key=lambda f: CONFIDENCE_RANK.get(f.confidence, 0), reverse=True)
    best = ranked[0]

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


# ── Shared reader mapping (extraction JSON -> PartialReq) ─────────────────────
#
# All LLM/structured readers emit the same JSON shape and call this mapper, so
# the extraction contract lives in exactly one place.

_VOID = {"", None, "unknown", "n/a", "none", "-", "null", "tbd"}


def _clean(value):
    """Return the value unless it is an empty/placeholder token."""
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.lower() in _VOID:
            return None
        return stripped
    if isinstance(value, (list, tuple)) and not value:
        return None
    return value


def _set(obj, field_name: str, raw: dict, key: str, conf: Confidence, src: str,
         note: str = "") -> None:
    value = _clean(raw.get(key))
    if value is not None:
        setattr(obj, field_name, fv(value, conf, src, note))


# field maps: (dataclass field name, JSON key)
_INFRA_FIELDS = [
    ("name", "name"), ("node_kind", "node_kind"), ("infra_type", "infra_type"),
    ("network_type", "network_type"), ("parent", "parent"), ("country", "country"),
    ("vendor", "vendor"), ("infra_owner", "infra_owner"),
]
_SYSTEM_FIELDS = [
    ("name", "name"), ("type", "type"), ("owner", "owner"), ("vendor", "vendor"),
    ("data_classification", "data_classification"),
]
_COMPONENT_FIELDS = [
    ("system", "system"), ("name", "name"), ("kind", "kind"), ("layer", "layer"),
    ("component_role", "component_role"), ("function_desc", "function_desc"),
    ("sensitivity", "sensitivity"), ("encryption_at_rest", "encryption_at_rest"),
    ("key_management", "key_management"),
]
_STACK_FIELDS = [
    ("component", "component"), ("component_name", "component_name"),
    ("component_package", "component_package"), ("version", "version"),
    ("category", "category"), ("license", "license"), ("eol_date", "eol_date"),
    ("standard_flag", "standard_flag"),
]
_DEPLOYMENT_FIELDS = [
    ("component", "component"), ("environment", "environment"),
    ("deployment_type", "deployment_type"), ("location_type", "location_type"),
    ("infra", "infra"), ("runtime_type", "runtime_type"),
    ("runtime_detail", "runtime_detail"), ("instance_count", "instance_count"),
]
_FLOW_FIELDS = [
    ("source", "from"), ("target", "to"), ("protocol", "protocol"), ("port", "port"),
    ("auth_method", "auth_method"), ("encryption", "encryption"),
    ("cross_border", "cross_border"), ("cross_border_basis", "cross_border_basis"),
    ("via", "via"), ("notes", "notes"),
]
_NETWORK_LINK_FIELDS = [
    ("source_infra", "from"), ("target_infra", "to"), ("method", "method"),
    ("bandwidth", "bandwidth"), ("encrypted", "encrypted"),
    ("encryption_method", "encryption_method"), ("managed_by", "managed_by"),
    ("redundancy", "redundancy"), ("notes", "notes"),
]
_AUTH_FIELDS = [
    ("subject", "subject"), ("applies_to", "applies_to"), ("auth_server", "auth_server"),
    ("protocol", "protocol"), ("authorization", "authorization"),
    ("authorization_platform", "authorization_platform"), ("user_roles", "user_roles"),
    ("mfa", "mfa"), ("notes", "notes"),
]
_ECOSYSTEM_FIELDS = [
    ("source_system", "from"), ("target_system", "to"),
    ("relation_type", "relation_type"), ("notes", "notes"),
]


def _map_list(raw_items, dataclass_type, id_prefix: str, fields, conf, src):
    out = []
    for index, raw in enumerate(raw_items or []):
        if not isinstance(raw, dict):
            continue
        entity = dataclass_type(id=f"{id_prefix}_{index + 1}")
        for field_name, key in fields:
            _set(entity, field_name, raw, key, conf, src)
        out.append(entity)
    return out


def v2_json_to_partial(extracted, source_tool: str, source_file: str,
                       confidence: Confidence = Confidence.MEDIUM,
                       source_label: str | None = None) -> PartialReq:
    """Map an extraction JSON document (req/v2 entity shape) to a PartialReq.

    Readers pass the same JSON keys the extraction prompts ask for. References
    between entities are plain names; the merger resolves them to typed IDs.
    """
    req = PartialReq(source_tool=source_tool, source_file=source_file)
    if not isinstance(extracted, dict):
        req.gaps.append("Extraction returned no usable object")
        return req
    if "error" in extracted:
        req.gaps.append(f"Extraction error: {extracted['error']}")
        return req

    src = source_label or f"{source_tool}:{source_file}"
    proj = extracted.get("project") or {}
    _set(req, "project_name", proj, "name", confidence, src)
    _set(req, "project_id", proj, "id", confidence, src)
    _set(req, "project_scope", proj, "scope", confidence, src)
    _set(req, "department", proj, "department", confidence, src)
    _set(req, "data_classification", proj, "data_classification", confidence, src)

    req.infra = _map_list(extracted.get("infra"), PartialInfra, "infra", _INFRA_FIELDS, confidence, src)
    req.systems = _map_list(extracted.get("systems"), PartialSystem, "system", _SYSTEM_FIELDS, confidence, src)
    req.components = _map_list(extracted.get("components"), PartialComponent, "component", _COMPONENT_FIELDS, confidence, src)
    req.stacks = _map_list(extracted.get("stacks"), PartialStack, "stack", _STACK_FIELDS, confidence, src)
    req.deployments = _map_list(extracted.get("deployments"), PartialDeployment, "deployment", _DEPLOYMENT_FIELDS, confidence, src)
    req.flows = _map_list(extracted.get("flows"), PartialFlow, "flow", _FLOW_FIELDS, confidence, src)
    req.network_links = _map_list(extracted.get("network_links"), PartialNetworkLink, "link", _NETWORK_LINK_FIELDS, confidence, src)
    req.auth = _map_list(extracted.get("auth"), PartialAuth, "auth", _AUTH_FIELDS, confidence, src)
    req.ecosystem_relations = _map_list(
        extracted.get("ecosystem_relations"), PartialEcosystemRelation, "eco",
        _ECOSYSTEM_FIELDS, confidence, src,
    )

    for cred in extracted.get("credentials") or []:
        if isinstance(cred, dict) and _clean(cred.get("solution")):
            req.credentials.append({**cred, "_source": src,
                                    "_confidence": confidence.value})
    req.constraints = [c for c in (extracted.get("constraints") or []) if _clean(c)]
    for item in extracted.get("open_items") or []:
        if isinstance(item, dict):
            req.open_items.append({**item, "_source": src})

    for gap in extracted.get("gaps_noted") or []:
        if _clean(gap):
            req.gaps.append(f"Noted gap: {gap}")

    return req
