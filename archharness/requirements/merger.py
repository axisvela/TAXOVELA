"""
merger.py — Merge multiple partial req YAML files into one final req/v2 req.yaml.

Strategy:
  1. Load all partial-req files (per-entity, name-based references)
  2. Merge each entity kind across sources:
     - named entities match by normalized name
     - deployments match by (component, environment)
     - flows match by (source, target)
     - network_links match by (undirected endpoint pair, method)
     - auth matches by (applies_to, subject)
  3. Resolve name references to typed IDs (INF/APP/CMP/DEP/FLOW/LNK/AUTH/STK)
  4. Run gap analysis against the CRITICAL fields list
  5. Output: merged req/v2 + gap-report.md

Usage:
    python -m archharness req --merge partial-1.yaml partial-2.yaml -o req.yaml
"""

import argparse
import re
import sys
from pathlib import Path
from datetime import datetime

import yaml

from .normalizer import (
    PartialReq, PartialInfra, PartialSystem, PartialComponent, PartialStack,
    PartialDeployment, PartialFlow, PartialNetworkLink, PartialAuth,
    PartialEcosystemRelation, FieldValue, Confidence, CONFIDENCE_RANK,
    merge_field, fv, _clean,
)
from ..schemas import validate_final_req_v2


# ── Enum coercion ─────────────────────────────────────────────────────────────

NODE_KINDS = {
    "region", "data_center", "iaas_vpc_vnet", "paas", "saas", "third_party",
    "office_network", "factory_network", "lab", "internet_network", "network_zone",
    "subnet", "firewall", "security_gateway", "waf", "router", "switch",
    "vpn_gateway", "identity_provider", "soc_monitoring", "load_balancer",
    "bastion_host", "logging_service", "policy_service", "key_management",
}
INFRA_TYPES = {"private_cloud", "public_cloud", "saas", "third_party", "office", "factory", "lab"}
NETWORK_TYPES = {"office_network", "factory_network", "lab_network", "prod_network", "dmz"}
ENVIRONMENTS = {"dev", "test", "staging", "prod", "dr"}

# Where secrets live. A model may label the store by the party that owns it
# (for example ``partner_keys``); the contract only knows these five, so an
# unrecognised label is reported and folded onto ``other``.
CREDENTIAL_ENVIRONMENTS = {"azure", "aws", "private_dc", "saas", "other"}
_CREDENTIAL_ENV_ALIASES = {
    "on_prem": "private_dc", "onprem": "private_dc", "datacenter": "private_dc",
    "data_center": "private_dc", "private_cloud": "private_dc",
    "public_cloud": "aws", "cloud": "other",
}
DEPLOYMENT_TYPES = {"private_cloud", "public_cloud", "public_cloud_paas", "saas", "third_party"}
LOCATION_TYPES = {"data_center", "public_cloud_region", "saas"}
RUNTIME_TYPES = {"vm", "container", "physical", "serverless"}
LAYERS = {"fe", "be", "api", "bff", "db", "mq", "ip", "lb", "bc", "other"}
COMPONENT_ROLES = {
    "application_service", "web_frontend", "backend_service", "bff", "ai_agent",
    "api_gateway", "load_balancer", "message_bus", "data_integration",
    "integration_service", "database", "cache", "file_storage", "object_storage",
    "metadata_store", "data_processing", "data_lake", "data_warehouse", "bi_report",
    "batch_processing", "streaming_processing", "large_scale_compute",
}
FLOW_AUTH_METHODS = {
    "OAuth2_ClientCredentials", "mTLS", "ClientCertificate", "SASL_SCRAM", "Basic",
    "ApiKey", "UserPassword", "Kerberos", "IAM_Role", "ManagedIdentity", "none",
}
FLOW_ENCRYPTIONS = {"TLS1.3", "TLS1.2", "mTLS", "IPSec", "none", "TBD"}
LINK_METHODS = {
    "mpls", "expressroute", "direct_connect", "vpc_peering", "vnet_peering",
    "vpn", "internet", "sdwan", "leased_line",
}
REDUNDANCIES = {"primary", "secondary", "backup"}
AUTH_SUBJECTS = {"user", "application"}
AUTH_PROTOCOLS = {"OIDC", "OAuth2_AuthCode", "SAML2", "CAS", "Kerberos", "Basic", "ApiKey"}
AUTHORIZATIONS = {"RBAC", "ABAC", "PBAC", "DAC"}
RELATION_TYPES = {"upstream", "downstream", "partner", "customer"}


def _norm(value: str) -> str:
    """Normalize a value for alias lookup: lowercase, separators -> underscore."""
    return re.sub(r"[\s\-/]+", "_", str(value).strip().lower())


def _alias(value, table: dict, allowed: set) -> str | None:
    """Map a raw value to an allowed enum value via a normalized alias table."""
    if value is None:
        return None
    key = _norm(value)
    if key in table:
        return table[key]
    if key in allowed:
        return key
    for candidate in allowed:
        if candidate.lower() == key:
            return candidate
    return None


_NODE_KIND_ALIASES = {
    "dc": "data_center", "datacenter": "data_center", "datacentre": "data_center",
    "region": "region", "cloud": "public_cloud", "vpc": "iaas_vpc_vnet",
    "vnet": "iaas_vpc_vnet", "subnet": "subnet", "zone": "network_zone",
    "security_zone": "network_zone", "internet": "internet_network",
    "office": "office_network", "office_lan": "office_network",
    "factory": "factory_network", "plant": "factory_network",
    "lab": "lab", "firewall": "firewall", "fw": "firewall", "waf": "waf",
    "router": "router", "switch": "switch", "gateway": "vpn_gateway",
    "vpn": "vpn_gateway", "vpn_gateway": "vpn_gateway",
    "adfs": "identity_provider", "entra": "identity_provider", "entra_id": "identity_provider",
    "idp": "identity_provider", "idp_provider": "identity_provider",
    "lb": "load_balancer", "f5": "load_balancer", "loadbalancer": "load_balancer",
    "bastion": "bastion_host", "jump_host": "bastion_host",
    "keyvault": "key_management", "key_vault": "key_management", "kms": "key_management",
    "soc": "soc_monitoring", "siem": "soc_monitoring", "logging": "logging_service",
    "policy": "policy_service", "paas": "paas", "saas": "saas",
    "thirdparty": "third_party", "third_party": "third_party",
    "security_gateway": "security_gateway", "api_gateway": "security_gateway",
}
_INFRA_TYPE_ALIASES = {
    "aws": "public_cloud", "azure": "public_cloud", "gcp": "public_cloud",
    "aliyun": "public_cloud", "cloud": "public_cloud", "onprem": "private_cloud",
    "on_prem": "private_cloud", "on_premise": "private_cloud", "dc": "private_cloud",
    "datacenter": "private_cloud", "private": "private_cloud", "self_hosted": "private_cloud",
    "vendor": "third_party", "partner": "third_party", "office": "office",
    "plant": "factory", "manufacturing": "factory",
}
_NETWORK_TYPE_ALIASES = {
    "dmz": "dmz", "prod": "prod_network", "production": "prod_network",
    "internal": "prod_network", "intranet": "prod_network", "app": "prod_network",
    "office": "office_network", "lan": "office_network", "corp": "office_network",
    "plant": "factory_network", "ot": "factory_network", "lab": "lab_network",
}
_ENV_ALIASES = {
    "production": "prod", "prd": "prod", "live": "prod", "development": "dev",
    "development_env": "dev", "uat": "test", "sit": "test", "qa": "test",
    "staging": "staging", "stage": "staging", "preprod": "staging",
    "disaster_recovery": "dr", "backup": "dr",
}
_DEPLOYMENT_TYPE_ALIASES = {
    "aws": "public_cloud", "azure": "public_cloud", "gcp": "public_cloud",
    "cloud": "public_cloud", "iaas": "public_cloud", "paas": "public_cloud_paas",
    "onprem": "private_cloud", "on_prem": "private_cloud", "private": "private_cloud",
    "dc": "private_cloud", "datacenter": "private_cloud", "physical": "private_cloud",
    "vendor": "third_party", "partner": "third_party", "external": "third_party",
}
_RUNTIME_ALIASES = {
    "k8s": "container", "kubernetes": "container", "docker": "container",
    "pod": "container", "ecs": "container", "aks": "container", "eks": "container",
    "gke": "container", "openshift": "container",
    "ec2": "vm", "instance": "vm", "server": "vm", "virtual_machine": "vm",
    "virtualmachine": "vm", "iaas_vm": "vm",
    "bare_metal": "physical", "baremetal": "physical", "hardware": "physical",
    "host": "physical", "appliance": "physical",
    "lambda": "serverless", "functions": "serverless", "function": "serverless",
    "faas": "serverless", "managed": "serverless",
}
_LAYER_ALIASES = {
    "frontend": "fe", "front_end": "fe", "ui": "fe", "web": "fe",
    "backend": "be", "back_end": "be", "business": "be",
    "api": "api", "bff": "bff", "database": "db", "data": "db",
    "queue": "mq", "message_queue": "mq", "messaging": "mq", "bus": "mq",
    "integration": "ip", "integration_platform": "ip", "middleware": "ip",
    "load_balancer": "lb", "batch": "bc", "compute": "other",
}
_ROLE_ALIASES = {
    "frontend": "web_frontend", "web": "web_frontend", "ui": "web_frontend",
    "backend": "backend_service", "service": "backend_service", "api": "backend_service",
    "app": "application_service", "application": "application_service",
    "gateway": "api_gateway", "apigateway": "api_gateway",
    "queue": "message_bus", "kafka": "message_bus", "bus": "message_bus",
    "db": "database", "rdbms": "database", "sql": "database",
    "storage": "object_storage", "object_store": "object_storage",
    "integration": "integration_service", "etl": "data_integration",
    "cache": "cache", "redis": "cache", "agent": "ai_agent",
    "data_warehouse": "data_warehouse", "warehouse": "data_warehouse",
    "data_lake": "data_lake", "lakehouse": "data_lake",
}
_FLOW_AUTH_ALIASES = {
    "oauth2": "OAuth2_ClientCredentials", "oauth2_0": "OAuth2_ClientCredentials",
    "oauth2_client_credentials": "OAuth2_ClientCredentials",
    "client_credentials": "OAuth2_ClientCredentials",
    "mtls": "mTLS", "tls": "mTLS", "client_certificate": "ClientCertificate",
    "certificate": "ClientCertificate", "sasl_scram": "SASL_SCRAM",
    "sasl": "SASL_SCRAM", "scram": "SASL_SCRAM", "basic": "Basic",
    "basic_auth": "Basic", "apikey": "ApiKey", "api_key": "ApiKey",
    "user_password": "UserPassword", "password": "UserPassword", "pwd": "UserPassword",
    "kerberos": "Kerberos", "sap_logon_ticket": "Kerberos",
    "iam_role": "IAM_Role", "managed_identity": "ManagedIdentity",
    "none": "none", "no_auth": "none", "na": "none",
}
_FLOW_ENCRYPTION_ALIASES = {
    "tls1_3": "TLS1.3", "tls_1_3": "TLS1.3", "tls13": "TLS1.3",
    "tls1_2": "TLS1.2", "tls_1_2": "TLS1.2", "tls12": "TLS1.2",
    "mtls": "mTLS", "ipsec": "IPSec", "none": "none", "tbd": "TBD",
}
_LINK_METHOD_ALIASES = {
    "express_route": "expressroute", "er": "expressroute", "directconnect": "direct_connect",
    "direct_connect": "direct_connect", "dx": "direct_connect",
    "vpc_peering": "vpc_peering", "vnet_peering": "vnet_peering",
    "peering": "vnet_peering", "vpn": "vpn", "ipsec": "vpn", "site_to_site": "vpn",
    "internet": "internet", "public_internet": "internet", "mpls": "mpls",
    "sdwan": "sdwan", "sd_wan": "sdwan", "leased_line": "leased_line",
    "lease_line": "leased_line", "dedicated_line": "leased_line",
}
_AUTH_PROTOCOL_ALIASES = {
    "saml": "SAML2", "saml2_0": "SAML2", "oidc": "OIDC",
    "openid_connect": "OIDC", "oauth2": "OAuth2_AuthCode",
    "oauth2_authorization_code": "OAuth2_AuthCode", "oauth2_authcode": "OAuth2_AuthCode",
    "authorization_code": "OAuth2_AuthCode", "cas": "CAS", "kerberos": "Kerberos",
    "basic": "Basic", "apikey": "ApiKey", "api_key": "ApiKey",
}
_AUTHORIZATION_ALIASES = {"rbac": "RBAC", "abac": "ABAC", "pbac": "PBAC", "dac": "DAC"}


# ── Name matching ─────────────────────────────────────────────────────────────

def _normalize_name(name: str) -> str:
    """Normalize a name for fuzzy matching."""
    if not name:
        return ""
    s = re.sub(r'[^a-z0-9]', '', str(name).lower())
    for suffix in ("service", "svc", "api", "app", "db", "database"):
        if s.endswith(suffix) and len(s) > len(suffix):
            s = s[:-len(suffix)]
    return s


def _key_of(entity, aspect: str) -> str:
    """Return the merge key for an entity, or '' when it cannot be keyed."""
    def val(field_name):
        f = getattr(entity, field_name, None)
        return str(f.value) if isinstance(f, FieldValue) and f.value is not None else ""

    if aspect == "name":
        return _normalize_name(val("name"))
    if aspect == "deployment":
        return f"{_normalize_name(val('component'))}|{val('environment').lower()}"
    if aspect == "flow":
        return f"{_normalize_name(val('source'))}->{_normalize_name(val('target'))}"
    if aspect == "link":
        ends = sorted([_normalize_name(val("source_infra")), _normalize_name(val("target_infra"))])
        return f"{ends[0]}--{ends[1]}|{val('method').lower()}"
    if aspect == "auth":
        # One entry point can be served by several identity providers (an
        # internal STS and an external IdP); the server is part of the identity
        # of the declaration, not a field to reconcile.
        return (f"{_normalize_name(val('applies_to'))}|{val('subject').lower()}"
                f"|{_normalize_name(val('auth_server'))}")
    if aspect == "stack":
        return f"{_normalize_name(val('component'))}|{val('component_name').lower()}|{val('version')}"
    if aspect == "ecosystem":
        return f"{_normalize_name(val('source_system'))}->{_normalize_name(val('target_system'))}"
    return ""


_ENTITY_SPECS = [
    ("infra", "name"), ("systems", "name"), ("components", "name"),
    ("stacks", "stack"), ("deployments", "deployment"), ("flows", "flow"),
    ("network_links", "link"), ("auth", "auth"), ("ecosystem_relations", "ecosystem"),
]


def _merge_one(versions: list):
    """Merge same-key entity versions field-by-field by confidence."""
    template = versions[0]
    merged = type(template)(id=template.id)
    for field_name in template.__dataclass_fields__:
        if field_name == "id":
            continue
        setattr(merged, field_name, merge_field(
            [getattr(v, field_name, None) for v in versions]))
    return merged


def _merge_entities(all_reqs: list[PartialReq]) -> dict[str, list]:
    merged: dict[str, list] = {}
    for attr, aspect in _ENTITY_SPECS:
        groups: dict[str, list] = {}
        order: list[str] = []
        for req in all_reqs:
            for entity in getattr(req, attr):
                key = _key_of(entity, aspect)
                if not key:
                    continue
                if key not in groups:
                    groups[key] = []
                    order.append(key)
                groups[key].append(entity)
        merged[attr] = [_merge_one(groups[k]) for k in order]
    return merged


# ── Reference resolution ──────────────────────────────────────────────────────

def _value_of(field_value) -> object:
    if isinstance(field_value, FieldValue):
        return field_value.value
    return field_value


def _ref_id(field_value, mapping: dict, allow_internet: bool = False) -> str | None:
    value = _value_of(field_value)
    if value is None:
        return None
    if allow_internet and str(value).strip().lower() == "internet":
        return "internet"
    return mapping.get(_normalize_name(str(value)))


def _ref_list(field_value, mapping: dict) -> list[str]:
    value = _value_of(field_value)
    if not isinstance(value, (list, tuple)):
        return []
    out = []
    for item in value:
        resolved = mapping.get(_normalize_name(str(item)))
        if resolved:
            out.append(resolved)
    return out


def _bool_of(value) -> bool | None:
    value = _value_of(value)
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    token = _norm(value)
    if token in {"true", "yes", "y", "1", "encrypted"}:
        return True
    if token in {"false", "no", "n", "0", "plain", "unencrypted"}:
        return False
    return None


def _int_of(value) -> int | None:
    value = _value_of(value)
    if value is None:
        return None
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


# ── Final output serialization ────────────────────────────────────────────────

def _plain(field_value):
    return _value_of(field_value)


def _enum(field_value, table: dict, allowed: set) -> str | None:
    return _alias(_value_of(field_value), table, allowed)


def _credential_rows(credentials, unresolved: list[str]) -> list[dict]:
    """Normalise credential rows to the contract's environment enum.

    A reader may name the key store by owner (``partner_keys``); the req/v2
    schema accepts only azure / aws / private_dc / saas / other, so an
    unmapped label folds onto ``other`` and is reported as a gap instead of
    failing the merge.
    """
    rows: list[dict] = []
    for credential in credentials or []:
        if not isinstance(credential, dict):
            continue
        label = _plain(credential.get("environment"))
        environment = _alias(label, _CREDENTIAL_ENV_ALIASES, CREDENTIAL_ENVIRONMENTS)
        if environment is None:
            unresolved.append(
                f"credential environment '{label or '?'}' is not in the model — "
                "recorded as 'other'")
            environment = "other"
        rows.append({**credential, "environment": environment})
    return rows


def _build_final(merged: dict, project: dict, credentials, constraints,
                 open_items) -> tuple[dict, list[str]]:
    """Resolve references, assign typed IDs and build the req/v2 document."""
    unresolved: list[str] = []

    credentials = _credential_rows(credentials, unresolved)

    infra_map: dict[str, str] = {}
    system_map: dict[str, str] = {}
    component_map: dict[str, str] = {}

    # Pass 1 — IDs for the named entities (stable, first-seen order).
    valid_infra = []
    for entity in merged["infra"]:
        name = _plain(entity.name)
        node_kind = _enum(entity.node_kind, _NODE_KIND_ALIASES, NODE_KINDS)
        if not name or not node_kind:
            unresolved.append(f"infra '{name or '?'}': node_kind missing or invalid — row dropped")
            continue
        valid_infra.append((entity, node_kind))
    for index, (entity, _) in enumerate(valid_infra, start=1):
        infra_map[_normalize_name(_plain(entity.name))] = f"INF-{index:02d}"

    valid_systems = []
    for entity in merged["systems"]:
        name = _plain(entity.name)
        if not name:
            unresolved.append("system with no name — row dropped")
            continue
        valid_systems.append(entity)
    for index, entity in enumerate(valid_systems, start=1):
        system_map[_normalize_name(_plain(entity.name))] = f"APP-{index:02d}"

    valid_components = []
    for entity in merged["components"]:
        name = _plain(entity.name)
        if not name:
            unresolved.append("component with no name — row dropped")
            continue
        valid_components.append(entity)
    for index, entity in enumerate(valid_components, start=1):
        component_map[_normalize_name(_plain(entity.name))] = f"CMP-{index:02d}"

    # Pass 2 — emit entities with resolved references.
    infra_out = []
    for entity, node_kind in valid_infra:
        infra_out.append(_drop_none({
            "id": infra_map[_normalize_name(_plain(entity.name))],
            "name": _plain(entity.name),
            "node_kind": node_kind,
            "infra_type": _enum(entity.infra_type, _INFRA_TYPE_ALIASES, INFRA_TYPES),
            "network_type": _enum(entity.network_type, _NETWORK_TYPE_ALIASES, NETWORK_TYPES),
            "parent_id": _ref_id(entity.parent, infra_map),
            "country": _plain(entity.country),
            "vendor": _plain(entity.vendor),
            "infra_owner": _plain(entity.infra_owner),
        }))

    systems_out = []
    for entity in valid_systems:
        systems_out.append(_drop_none({
            "id": system_map[_normalize_name(_plain(entity.name))],
            "name": _plain(entity.name),
            "type": (_plain(entity.type) or "existing").lower()
                    if str(_plain(entity.type) or "existing").lower() in {"new", "existing", "modified"} else "existing",
            "owner": _enum(entity.owner, {}, {"org_it", "biz_owned", "third_party"}),
            "vendor": _plain(entity.vendor),
            "data_classification": _plain(entity.data_classification),
        }))

    components_out = []
    for entity in valid_components:
        system_id = _ref_id(entity.system, system_map)
        if not system_id:
            unresolved.append(f"component '{_plain(entity.name)}': owning system "
                              f"'{_plain(entity.system)}' unresolved — row dropped")
            continue
        components_out.append(_drop_none({
            "id": component_map[_normalize_name(_plain(entity.name))],
            "system_id": system_id,
            "name": _plain(entity.name),
            "kind": (_plain(entity.kind) or "component").lower()
                    if str(_plain(entity.kind) or "component").lower() in {"service", "component"} else "component",
            "layer": _enum(entity.layer, _LAYER_ALIASES, LAYERS),
            "component_role": _enum(entity.component_role, _ROLE_ALIASES, COMPONENT_ROLES),
            "function_desc": _plain(entity.function_desc),
            "sensitivity": _plain(entity.sensitivity),
            "encryption_at_rest": _plain(entity.encryption_at_rest),
            "key_management": _ref_id(entity.key_management, infra_map),
        }))

    stacks_out = []
    for index, entity in enumerate(merged["stacks"], start=1):
        component_id = _ref_id(entity.component, component_map)
        tech = _plain(entity.component_name) or _plain(entity.component)
        if not component_id or not tech:
            unresolved.append(f"stack '{tech or '?'}': component unresolved — row dropped")
            continue
        stacks_out.append(_drop_none({
            "id": f"STK-{index:02d}",
            "component_id": component_id,
            "component": tech,
            "component_package": _plain(entity.component_package),
            "version": _plain(entity.version) or "TBD",
            "category": _plain(entity.category),
            "eol_date": _plain(entity.eol_date),
            "license": _plain(entity.license),
            "standard_flag": _bool_of(entity.standard_flag),
        }))

    deployments_out = []
    for index, entity in enumerate(merged["deployments"], start=1):
        component_id = _ref_id(entity.component, component_map)
        if not component_id:
            unresolved.append(f"deployment of '{_plain(entity.component)}': component "
                              f"unresolved — row dropped")
            continue
        environment = _alias(_plain(entity.environment), _ENV_ALIASES, ENVIRONMENTS) or "prod"
        deployment_type = _alias(_plain(entity.deployment_type),
                                 _DEPLOYMENT_TYPE_ALIASES, DEPLOYMENT_TYPES) or "private_cloud"
        location_type = _alias(_plain(entity.location_type), {}, LOCATION_TYPES)
        if not location_type:
            location_type = {"public_cloud": "public_cloud_region",
                             "public_cloud_paas": "public_cloud_region",
                             "saas": "saas", "third_party": "saas"}.get(deployment_type, "data_center")
        runtime_type = _alias(_plain(entity.runtime_type), _RUNTIME_ALIASES, RUNTIME_TYPES) or "container"
        infra_id = None
        if _plain(entity.infra) is not None:
            infra_id = _ref_id(entity.infra, infra_map)
            if not infra_id:
                unresolved.append(f"deployment of '{_plain(entity.component)}': infra "
                                  f"'{_plain(entity.infra)}' unresolved")
        deployments_out.append(_drop_none({
            "id": f"DEP-{index:02d}",
            "component_id": component_id,
            "environment": environment,
            "deployment_type": deployment_type,
            "location_type": location_type,
            "infra_id": infra_id,
            "runtime_type": runtime_type,
            "runtime_detail": _plain(entity.runtime_detail),
            "instance_count": _int_of(entity.instance_count),
        }))

    flows_out = []
    for index, entity in enumerate(merged["flows"], start=1):
        source_id = _ref_id(entity.source, component_map, allow_internet=True)
        target_id = _ref_id(entity.target, component_map)
        protocol = _plain(entity.protocol)
        if not source_id or not target_id or not protocol:
            unresolved.append(f"flow '{_plain(entity.source)}' -> '{_plain(entity.target)}': "
                              f"endpoint or protocol unresolved — row dropped")
            continue
        flows_out.append(_drop_none({
            "id": f"FLOW-{index:02d}",
            "source_component_id": source_id,
            "target_component_id": target_id,
            "protocol": protocol,
            "port": _plain(entity.port),
            "auth_method": _alias(_plain(entity.auth_method), _FLOW_AUTH_ALIASES,
                                  FLOW_AUTH_METHODS) or "none",
            "encryption": _enum(entity.encryption, _FLOW_ENCRYPTION_ALIASES, FLOW_ENCRYPTIONS),
            "cross_border": _bool_of(entity.cross_border),
            "cross_border_basis": _plain(entity.cross_border_basis),
            "via": _ref_list(entity.via, infra_map) or None,
            "notes": _plain(entity.notes),
        }))

    links_out = []
    for index, entity in enumerate(merged["network_links"], start=1):
        source_id = _ref_id(entity.source_infra, infra_map)
        target_id = _ref_id(entity.target_infra, infra_map)
        method = _alias(_plain(entity.method), _LINK_METHOD_ALIASES, LINK_METHODS)
        if not source_id or not target_id or not method:
            unresolved.append(f"network_link '{_plain(entity.source_infra)}' <-> "
                              f"'{_plain(entity.target_infra)}': endpoint or method unresolved — row dropped")
            continue
        links_out.append(_drop_none({
            "id": f"LNK-{index:02d}",
            "source_infra_id": source_id,
            "target_infra_id": target_id,
            "method": method,
            "bandwidth": _plain(entity.bandwidth),
            "encrypted": _bool_of(entity.encrypted),
            "encryption_method": _plain(entity.encryption_method),
            "managed_by": _plain(entity.managed_by),
            "redundancy": _enum(entity.redundancy, {}, REDUNDANCIES),
            "notes": _plain(entity.notes),
        }))

    auth_out = []
    for index, entity in enumerate(merged["auth"], start=1):
        protocol = _alias(_plain(entity.protocol), _AUTH_PROTOCOL_ALIASES, AUTH_PROTOCOLS)
        applies_to = _ref_id(entity.applies_to, {**component_map, **infra_map},
                             allow_internet=True)
        if not protocol or not applies_to:
            unresolved.append(f"auth '{_plain(entity.applies_to)}': entry point or protocol "
                              f"unresolved — row dropped")
            continue
        auth_server = _ref_id(entity.auth_server, {**infra_map, **component_map})
        if _plain(entity.auth_server) and not auth_server:
            unresolved.append(f"auth '{_plain(entity.applies_to)}': server "
                              f"'{_plain(entity.auth_server)}' unresolved")
        auth_out.append(_drop_none({
            "id": f"AUTH-{index:02d}",
            "subject": _alias(_plain(entity.subject), {}, AUTH_SUBJECTS) or "user",
            "applies_to": applies_to,
            "auth_server": auth_server,
            "protocol": protocol,
            "authorization": _enum(entity.authorization, _AUTHORIZATION_ALIASES, AUTHORIZATIONS),
            "authorization_platform": _plain(entity.authorization_platform),
            "user_roles": _value_of(entity.user_roles),
            "mfa": _bool_of(entity.mfa),
            "notes": _plain(entity.notes),
        }))

    eco_out = []
    for index, entity in enumerate(merged["ecosystem_relations"], start=1):
        source_id = _ref_id(entity.source_system, system_map)
        target_id = _ref_id(entity.target_system, system_map)
        if not source_id or not target_id:
            unresolved.append(f"ecosystem_relation '{_plain(entity.source_system)}' -> "
                              f"'{_plain(entity.target_system)}': system unresolved — row dropped")
            continue
        eco_out.append(_drop_none({
            "id": f"ECO-{index:02d}",
            "source_system_id": source_id,
            "target_system_id": target_id,
            "relation_type": _enum(entity.relation_type, {}, RELATION_TYPES),
            "notes": _plain(entity.notes),
        }))

    doc = {
        "schema_version": "req/v2",
        "requirements": {
            # project.name is required by the contract; keep the key even when null.
            "project": {k: v for k, v in project.items()},
            "infra": infra_out,
            "systems": systems_out,
            "components": components_out,
            "deployments": deployments_out,
            "flows": flows_out,
            "network_links": links_out,
            "auth": auth_out,
            "stacks": stacks_out,
            "ecosystem_relations": eco_out,
            "credentials": credentials,
            "constraints": constraints,
            "open_items": open_items,
        },
    }
    return doc, unresolved


def _drop_none(mapping: dict) -> dict:
    return {k: v for k, v in mapping.items() if v is not None}


# ── Gap analysis ──────────────────────────────────────────────────────────────

def analyze_gaps(doc: dict, unresolved: list[str]) -> dict:
    """Identify critical / non-critical gaps and conflicts in the merged doc."""
    req = doc["requirements"]
    critical: list[str] = list(unresolved)
    non_critical: list[str] = []
    conflicts: list[str] = []

    if not req["project"].get("name"):
        critical.append("Project name is missing")

    for infra in req["infra"]:
        if not infra.get("country"):
            non_critical.append(f"Infra '{infra.get('name')}': country not specified")

    for system in req["systems"]:
        if not system.get("owner"):
            non_critical.append(f"System '{system.get('name')}': owner not specified")

    for comp in req["components"]:
        if not comp.get("component_role"):
            non_critical.append(f"Component '{comp.get('name')}': component_role not assigned")
        if not comp.get("sensitivity"):
            non_critical.append(f"Component '{comp.get('name')}': sensitivity not specified")

    for dep in req["deployments"]:
        if dep.get("environment") == "prod" and not dep.get("infra_id"):
            critical.append(f"Deployment '{dep.get('id')}' ({dep.get('component_id')}): "
                            f"infra_id missing for prod")

    for flow in req["flows"]:
        if not flow.get("auth_method") or flow.get("auth_method") == "none":
            non_critical.append(f"Flow '{flow.get('id')}' ({flow.get('source_component_id')} -> "
                                f"{flow.get('target_component_id')}): auth_method is none/absent")
        if not flow.get("port"):
            non_critical.append(f"Flow '{flow.get('id')}': port not specified")

    if not req["auth"] and not req["flows"]:
        critical.append("No authentication defined for any entry point")

    for item in req["open_items"]:
        if isinstance(item, dict) and "CONFLICT" in str(item):
            conflicts.append(str(item))

    return {"critical": critical, "non_critical": non_critical, "conflicts": conflicts}


# ── Gap report ────────────────────────────────────────────────────────────────

def generate_gap_report(gaps: dict, sources: list[str]) -> str:
    lines = [
        "# Requirements Gap Report",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Sources merged",
    ]
    for s in sources:
        lines.append(f"  - {s}")

    lines += ["", f"## Critical gaps ({len(gaps['critical'])}) — must resolve before arch-design"]
    if gaps["critical"]:
        for g in gaps["critical"]:
            lines.append(f"  - [CRITICAL] {g}")
    else:
        lines.append("  OK: no critical gaps")

    lines += ["", f"## Conflicts ({len(gaps['conflicts'])}) — same field, different values"]
    if gaps["conflicts"]:
        for g in gaps["conflicts"]:
            lines.append(f"  - [CONFLICT] {g}")
    else:
        lines.append("  OK: no conflicts detected")

    lines += ["", f"## Non-critical gaps ({len(gaps['non_critical'])}) — can be TBD"]
    if gaps["non_critical"]:
        for g in gaps["non_critical"][:20]:
            lines.append(f"  - {g}")
        if len(gaps["non_critical"]) > 20:
            lines.append(f"  ... and {len(gaps['non_critical']) - 20} more")
    else:
        lines.append("  OK: all recommended fields present")

    lines += ["",
              "## Next steps",
              "1. Resolve all CRITICAL gaps (required for arch-design)",
              "2. Confirm or correct CONFLICTs with the application owner",
              "3. Run /arch-requirements interview to fill remaining gaps",
              "4. Once the gap report shows no CRITICAL items, run /arch-design"]

    return "\n".join(lines)


# ── Partial input deserialization ─────────────────────────────────────────────

_ENTITY_FIELDS = {
    "infra": (PartialInfra, ["name", "node_kind", "infra_type", "network_type",
                             "parent", "country", "vendor", "infra_owner"]),
    "systems": (PartialSystem, ["name", "type", "owner", "vendor", "data_classification"]),
    "components": (PartialComponent, ["system", "name", "kind", "layer", "component_role",
                                      "function_desc", "sensitivity", "encryption_at_rest",
                                      "key_management"]),
    "stacks": (PartialStack, ["component", "component_name", "component_package", "version",
                              "category", "license", "eol_date", "standard_flag"]),
    "deployments": (PartialDeployment, ["component", "environment", "deployment_type",
                                        "location_type", "infra", "runtime_type",
                                        "runtime_detail", "instance_count"]),
    "flows": (PartialFlow, ["source", "target", "protocol", "port", "auth_method",
                            "encryption", "cross_border", "cross_border_basis", "via", "notes"]),
    "network_links": (PartialNetworkLink, ["source_infra", "target_infra", "method", "bandwidth",
                                           "encrypted", "encryption_method", "managed_by",
                                           "redundancy", "notes"]),
    "auth": (PartialAuth, ["subject", "applies_to", "auth_server", "protocol", "authorization",
                           "authorization_platform", "user_roles", "mfa", "notes"]),
    "ecosystem_relations": (PartialEcosystemRelation, ["source_system", "target_system",
                                                       "relation_type", "notes"]),
}


def _to_field_value(raw_value) -> FieldValue | None:
    if raw_value is None:
        return None
    if isinstance(raw_value, FieldValue):
        return raw_value
    if isinstance(raw_value, dict) and "value" in raw_value:
        confidence_value = raw_value.get("confidence", Confidence.UNKNOWN.value)
        try:
            confidence = Confidence(confidence_value)
        except ValueError:
            confidence = Confidence.UNKNOWN
        return FieldValue(
            value=raw_value["value"],
            confidence=confidence,
            source=raw_value.get("source", ""),
            note=raw_value.get("note", ""),
        )
    return fv(raw_value, Confidence.UNKNOWN, "")


def _partial_req_from_dict(raw: dict, source_path: str) -> PartialReq:
    """Reconstruct a PartialReq (req/v2 entity shape) from serialized YAML."""
    req = PartialReq(
        source_tool=raw.get("source_tool", ""),
        source_file=raw.get("source_file", source_path),
        project_name=_to_field_value(raw.get("project_name")),
        project_id=_to_field_value(raw.get("project_id")),
        project_scope=_to_field_value(raw.get("project_scope")),
        department=_to_field_value(raw.get("department")),
        data_classification=_to_field_value(raw.get("data_classification")),
        credentials=raw.get("credentials", []) or [],
        constraints=raw.get("constraints", []) or [],
        open_items=raw.get("open_items", []) or [],
        gaps=raw.get("gaps", []) or [],
        no_coverage=raw.get("no_coverage", []) or [],
    )

    for attr, (dataclass_type, fields) in _ENTITY_FIELDS.items():
        for index, raw_entity in enumerate(raw.get(attr, []) or []):
            if not isinstance(raw_entity, dict):
                continue
            entity = dataclass_type(id=raw_entity.get("id", f"{attr}_{index + 1}"))
            for field_name in fields:
                setattr(entity, field_name, _to_field_value(raw_entity.get(field_name)))
            getattr(req, attr).append(entity)

    return req


def _public_entry(entry: dict) -> dict:
    """Drop merge-internal provenance keys from a free-form entry.

    Readers tag credentials and open items with ``_source`` / ``_confidence``
    so a merge can explain where a row came from. Those keys are not part of
    the req/v2 contract, and ``credential`` rejects additional properties.
    """
    return {key: value for key, value in entry.items() if not key.startswith("_")}


def _deduplicate(items: list) -> list:
    """Deduplicate YAML-compatible values while retaining first-seen order."""
    deduplicated = []
    seen = set()
    for item in items:
        key = yaml.safe_dump(item, allow_unicode=True, sort_keys=True)
        if key not in seen:
            seen.add(key)
            deduplicated.append(item)
    return deduplicated


# ── Main merge function ───────────────────────────────────────────────────────

def merge_partial_reqs(partial_files: list[str]) -> tuple[str, str, dict]:
    """
    Load and merge multiple partial req YAML files.
    Returns: (merged_req_yaml, gap_report_md, gaps_dict)
    """
    all_reqs: list[PartialReq] = []
    for f in partial_files:
        with open(f, encoding="utf-8") as fp:
            raw = yaml.safe_load(fp) or {}
        if not isinstance(raw, dict):
            raise ValueError(f"Partial requirements root must be a mapping: {f}")
        all_reqs.append(_partial_req_from_dict(raw, f))

    merged = _merge_entities(all_reqs)

    def _ensure_fv(v) -> FieldValue:
        if v is None:
            return None
        if isinstance(v, FieldValue):
            return v
        if isinstance(v, dict) and "value" in v:
            return _to_field_value(v)
        return fv(v, Confidence.UNKNOWN, "")

    project = {
        "name": _plain(merge_field([_ensure_fv(r.project_name) for r in all_reqs])),
        "id": _plain(merge_field([_ensure_fv(r.project_id) for r in all_reqs])),
        "scope": _plain(merge_field([_ensure_fv(r.project_scope) for r in all_reqs])),
        "department": _plain(merge_field([_ensure_fv(r.department) for r in all_reqs])),
        "data_classification": _plain(merge_field(
            [_ensure_fv(r.data_classification) for r in all_reqs])),
    }

    all_creds = _deduplicate([_public_entry(c) for r in all_reqs for c in r.credentials])
    all_constraints = list(dict.fromkeys(c for r in all_reqs for c in r.constraints))
    all_open = _deduplicate([_public_entry(o) for r in all_reqs for o in r.open_items])

    doc, unresolved = _build_final(merged, project, all_creds, all_constraints, all_open)
    validate_final_req_v2(doc)

    gaps = analyze_gaps(doc, unresolved)
    merged_yaml = yaml.dump(doc, allow_unicode=True, sort_keys=False, default_flow_style=False)

    sources = [r.source_file or r.source_tool for r in all_reqs]
    gap_report = generate_gap_report(gaps, sources)

    return merged_yaml, gap_report, gaps


def main(argv: list[str] | None = None) -> int:
    """Merge partial files. Returns an exit code (no sys.exit)."""
    parser = argparse.ArgumentParser(description="Merge partial requirement YAML files")
    parser.add_argument("files", nargs="+", help="Partial req YAML files to merge")
    parser.add_argument("-o", "--output", default="merged-req.yaml", help="Output merged req YAML")
    parser.add_argument("--report", default="gap-report.md", help="Gap report output file")
    parser.add_argument("--manifest", default=None, help="Write an artifact/v1 provenance manifest (JSON)")
    args = parser.parse_args(argv)

    merged_yaml, gap_report, gaps = merge_partial_reqs(args.files)

    from ..files import atomic_write_text

    try:
        atomic_write_text(args.output, merged_yaml)
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"✓ Merged requirements: {args.output}")

    if args.manifest:
        import json
        from archharness import __version__ as _cli_version
        from archharness.artifacts import make_manifest
        manifest = make_manifest(
            artifact_id=f"req-{Path(args.output).stem}",
            artifact_type="requirements",
            schema="req/v2",
            path=args.output,
            producer=f"archharness/{_cli_version}",
            input_artifacts=[Path(f).name for f in args.files],
        )
        try:
            atomic_write_text(args.manifest, json.dumps(manifest, indent=2))
        except OSError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        print(f"✓ Artifact manifest: {args.manifest}")

    try:
        atomic_write_text(args.report, gap_report)
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"✓ Gap report: {args.report}")

    n_critical = len(gaps["critical"])
    n_conflict = len(gaps["conflicts"])
    print(f"  Critical gaps: {n_critical}  |  Conflicts: {n_conflict}")
    if n_critical == 0:
        print("  ✓ Ready for arch-design")
    else:
        print(f"  ✗ Resolve {n_critical} critical gaps before running arch-design")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
