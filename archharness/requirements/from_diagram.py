"""
from_diagram.py — Extract requirements from architecture diagram files.

Supports:
  .drawio / .xml   — draw.io XML: parse mxCell hierarchy
  .d2              — D2 diagram: parse container + edge syntax
  .yaml / .yml     — arch: YAML (our own format): direct mapping
  .png / .jpg / .webp — Architecture image: Claude Vision API extraction

Output is a req/v2 PartialReq: hosting/network nodes become `infra`, application
artefacts become `components` under one `systems` row, arrows become `flows`, and
network appliances (F5, WAF, ADFS, Key Vault) are classified as `infra` L4 nodes —
never as components.

Usage:
    python from_diagram.py -i diagram.drawio -o partial-req.yaml
    python from_diagram.py -i diagram.d2 -o partial-req.yaml
    python from_diagram.py -i arch.yaml -o partial-req.yaml
    python from_diagram.py -i screenshot.png -o partial-req.yaml   # needs Anthropic API key
"""

import argparse
import json
import os
import re
import base64
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

from .normalizer import (
    PartialReq, PartialSystem, PartialInfra, PartialComponent, PartialDeployment,
    PartialAuth, PartialFlow, PartialNetworkLink,
    Confidence, fv, partial_req_to_yaml, v2_json_to_partial,
)


# ── Label classification (shared by drawio / d2) ──────────────────────────────

_APPLIANCE_RULES = [
    (("firewall", "azfw", "pan-os", "fortigate"), "firewall"),
    (("waf", "web application firewall"), "waf"),
    (("load balancer", "loadbalancer", " f5", "f5 ", "bigip", "alb", "nlb", "elb"), "load_balancer"),
    (("adfs", "entra", "active directory", "identity provider", "idp", "ldap"), "identity_provider"),
    (("key vault", "keyvault", "kms", "secrets manager", "hsm"), "key_management"),
    (("bastion", "jump host", "jumpbox"), "bastion_host"),
    (("vpn gateway", "expressroute", "direct connect", "vpn"), "vpn_gateway"),
    (("soc", "siem", "sentinel"), "soc_monitoring"),
    (("router", "switch"), "router"),
]

_COMPONENT_RULES = [
    (("kafka", "rabbitmq", "queue", "message bus", "pubsub", "service bus"), "message_bus", "mq"),
    (("api gateway", "wso2", "apim", "apih", "kong", "api management"), "api_gateway", "ip"),
    (("postgres", "mysql", "oracle", "sql server", "rds", "aurora", "mongodb", "database", " db", "db "), "database", "db"),
    (("redis", "memcached", "cache"), "cache", "db"),
    (("s3", "blob storage", "object storage", "oss"), "object_storage", "db"),
    (("data lake", "lakehouse", "hdfs"), "data_lake", "db"),
    (("databricks", "data warehouse", "redshift", "snowflake", "synapse"), "data_warehouse", "db"),
    (("etl", "slt", "debezium", "cdc", "data integration"), "data_integration", "ip"),
    (("agent", "llm", "ai "), "ai_agent", "be"),
    (("bff",), "bff", "bff"),
    (("frontend", "web ui", " front", "portal ui", "nginx"), "web_frontend", "fe"),
]


def _classify_label(label: str) -> tuple[str, str, str | None]:
    """Classify a node label into (kind, role_or_nodekind, layer_or_none)."""
    text = f" {label.lower()} "
    for needles, node_kind in _APPLIANCE_RULES:
        if any(n in text for n in needles):
            return "infra", node_kind, None
    for needles, role, layer in _COMPONENT_RULES:
        if any(n in text for n in needles):
            return "component", role, layer
    return "component", "backend_service", "be"


def _clean_html(text: str) -> str:
    """Strip HTML tags and decode entities from draw.io cell values."""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = (text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
                .replace('&nbsp;', ' ').replace('&#39;', "'").replace('&quot;', '"'))
    return ' '.join(text.split()).strip()


def _clean_label(value: str) -> str:
    clean = re.sub(r'\s*\([^)]*\)', '', value).strip()
    clean = re.sub(r'\s*\[[^\]]*\]', '', clean).strip()
    return clean.lstrip("⚠ ").strip()


def _primary_system(req: PartialReq, hint: str, src: str) -> str:
    """Ensure the partial has one system; return its name for component refs."""
    name = _clean_label(hint) if hint else ""
    if not name:
        name = "Unassigned System"
    if not any(s.name and s.name.value == name for s in req.systems):
        system = PartialSystem(id="system_1")
        system.name = fv(name, Confidence.MEDIUM, src)
        system.type = fv("existing", Confidence.LOW, src, "Inferred from diagram")
        req.systems.append(system)
    return name


def _runtime_type(runtime: str) -> str | None:
    """Classify a free-text runtime into the contract's runtime enum."""
    text = (runtime or "").lower()
    if any(token in text for token in ("k8s", "kubernetes", "container", "pod", "docker")):
        return "container"
    if any(token in text for token in ("serverless", "lambda", "function")):
        return "serverless"
    if any(token in text for token in ("vm", "virtual machine", "instance")):
        return "vm"
    if any(token in text for token in ("physical", "appliance", "bare metal", "host")):
        return "physical"
    return None


_EXTERNAL_SOURCES = {"internet", "user", "office-network"}

_LINK_METHOD_TOKENS = (
    ("mpls", "mpls"),
    ("expressroute", "expressroute"),
    ("express route", "expressroute"),
    ("direct connect", "direct_connect"),
    ("vnet peering", "vnet_peering"),
    ("vpc peering", "vpc_peering"),
    ("peering", "vnet_peering"),
    ("sd-wan", "sdwan"),
    ("sdwan", "sdwan"),
    ("ipsec", "vpn"),
    ("vpn", "vpn"),
    ("leased line", "leased_line"),
    ("private line", "leased_line"),
    ("internet", "internet"),
)

_AUTH_PROTOCOL_TOKENS = (
    ("saml", "SAML2"),
    ("openid connect", "OIDC"),
    ("oidc", "OIDC"),
    ("authorization code", "OAuth2_AuthCode"),
    ("client credentials", "OAuth2_ClientCredentials"),
    ("oauth2", "OAuth2_AuthCode"),
    ("oauth 2", "OAuth2_AuthCode"),
    ("kerberos", "Kerberos"),
    ("api key", "ApiKey"),
    ("apikey", "ApiKey"),
    ("active directory", "Kerberos"),
    ("password", "Basic"),
    ("basic", "Basic"),
)


def _keyword_token(text: str, table: tuple[tuple[str, str], ...]) -> str | None:
    """Return the enum token whose keyword appears first in a free-text field."""
    haystack = (text or "").lower()
    for token, value in table:
        if token in haystack:
            return value
    return None


def _deployment_type(region_type: str) -> tuple[str, str]:
    """Return the (deployment_type, location_type) pair for a region type."""
    if region_type == "private_dc":
        return "private_cloud", "data_center"
    if region_type in ("aws_vpc", "azure_vnet"):
        return "public_cloud", "public_cloud_region"
    if region_type == "saas":
        return "saas", "saas"
    return "third_party", "saas"


def _zone_infra(label: str, parent: str, src: str, zone_count: int) -> PartialInfra:
    zone = label.lower()
    if "dmz" in zone:
        network_type = "dmz"
    elif "office" in zone:
        network_type = "office_network"
    elif "factory" in zone or "plant" in zone:
        network_type = "factory_network"
    elif "lab" in zone:
        network_type = "lab_network"
    else:
        network_type = "prod_network"
    infra = PartialInfra(id=f"zone_{zone_count}")
    infra.name = fv(label, Confidence.HIGH, src)
    infra.node_kind = fv("network_zone", Confidence.MEDIUM, src)
    infra.network_type = fv(network_type, Confidence.MEDIUM, src)
    if parent:
        infra.parent = fv(parent, Confidence.MEDIUM, src)
    return infra


def _location_infra(label: str, src: str, count: int) -> PartialInfra:
    """Build a top-level infra node (region / data centre / cloud) from a label."""
    lowered = label.lower()
    infra = PartialInfra(id=f"loc_{count}")
    infra.name = fv(label, Confidence.HIGH, src)

    if any(x in lowered for x in ("aws", "amazon", "vpc", "azure", "vnet", "gcp", "google")):
        infra.node_kind = fv("iaas_vpc_vnet", Confidence.LOW, src)
        infra.infra_type = fv("public_cloud", Confidence.MEDIUM, src)
    elif "internet" in lowered:
        infra.node_kind = fv("internet_network", Confidence.HIGH, src)
    elif "office" in lowered:
        infra.node_kind = fv("office_network", Confidence.MEDIUM, src)
        infra.infra_type = fv("office", Confidence.MEDIUM, src)
    else:
        infra.node_kind = fv("data_center", Confidence.MEDIUM, src)
        infra.infra_type = fv("private_cloud", Confidence.MEDIUM, src)

    loc = re.search(r'\[([A-Z]{2,})\]', label)
    if loc:
        infra.country = fv(loc.group(1), Confidence.HIGH, src)
    owner_match = re.search(r'\(([^)]+)\)', label)
    if owner_match:
        infra.infra_owner = fv(owner_match.group(1), Confidence.MEDIUM, src)
    return infra


def _edge_to_flow(src_value: str, tgt_value: str, label: str, src: str,
                  index: int) -> PartialFlow:
    """Parse an edge label like ``HTTPS/OAuth2.0`` into a flow."""
    protocol, auth = "", ""
    if label:
        if "/" in label:
            protocol, _, auth = label.partition("/")
        else:
            protocol = label
    flow = PartialFlow(id=f"flow_{index}")
    flow.source = fv(_clean_label(src_value) or src_value, Confidence.HIGH, src)
    flow.target = fv(_clean_label(tgt_value) or tgt_value, Confidence.HIGH, src)
    if protocol.strip():
        flow.protocol = fv(protocol.strip(), Confidence.MEDIUM, src)
    if auth.strip():
        flow.auth_method = fv(auth.strip(), Confidence.LOW, src,
                              "Extracted from edge label — verify")
    return flow


# ── draw.io XML parser ────────────────────────────────────────────────────────

def parse_drawio(content: str, source_file: str) -> PartialReq:
    req = PartialReq(source_tool="arch-req-from-diagram", source_file=source_file)
    SRC = f"diagram:drawio:{Path(source_file).name}"

    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        req.gaps.append(f"XML parse error: {e}")
        return req

    cells = {}
    for cell in root.iter("mxCell"):
        cid = cell.get("id", "")
        if cid in ("0", "1"):
            continue
        cells[cid] = {
            "id": cid,
            "value": _clean_html(cell.get("value", "")),
            "style": cell.get("style", ""),
            "parent": cell.get("parent", "1"),
            "source": cell.get("source", ""),
            "target": cell.get("target", ""),
            "edge": cell.get("edge", "0") == "1",
            "vertex": cell.get("vertex", "0") == "1",
        }

    system_name = _primary_system(req, Path(source_file).stem, SRC)
    infra_names: set[str] = set()
    comp_count = 0
    zone_count = 0
    edge_count = 0

    for cid, c in sorted(cells.items()):
        if not c["vertex"] or c["edge"] or not c["value"]:
            continue
        style = c["style"].lower()
        value = c["value"]

        is_container = ("ext" in style and "double" in style) or "container=1" in style

        if is_container and "dashed" not in style:
            # Top-level deployment container (DC / cloud / region)
            name = _clean_label(value)
            if name and name not in infra_names:
                infra_names.add(name)
                req.infra.append(_location_infra(value, SRC, len(req.infra) + 1))
            continue

        if (is_container and "dashed" in style) or ("ext" in style and "dashed" in style):
            zone_count += 1
            req.infra.append(_zone_infra(value, "", SRC, zone_count))
            continue

        kind, role, layer = _classify_label(value)
        if kind == "infra":
            if value not in infra_names:
                infra_names.add(value)
                infra = PartialInfra(id=f"appliance_{len(req.infra) + 1}")
                infra.name = fv(value, Confidence.HIGH, SRC)
                infra.node_kind = fv(role, Confidence.MEDIUM, SRC)
                req.infra.append(infra)
            continue

        comp_count += 1
        comp = PartialComponent(id=f"comp_{comp_count}")
        comp.system = fv(system_name, Confidence.MEDIUM, SRC)
        comp.name = fv(value, Confidence.HIGH, SRC)
        comp.kind = fv("component", Confidence.LOW, SRC)
        comp.component_role = fv(role, Confidence.MEDIUM, SRC)
        if layer:
            comp.layer = fv(layer, Confidence.LOW, SRC)
        req.components.append(comp)

    for cid, c in sorted(cells.items()):
        if not c["edge"]:
            continue
        edge_count += 1
        src_cell = cells.get(c["source"], {})
        tgt_cell = cells.get(c["target"], {})
        req.flows.append(_edge_to_flow(
            src_cell.get("value", c["source"]), tgt_cell.get("value", c["target"]),
            c["value"], SRC, edge_count,
        ))

    req.no_coverage.extend(["auth", "credentials", "project_name", "department"])
    req.gaps.append(f"draw.io: {len([i for i in req.infra])} infra nodes, "
                    f"{zone_count} zones, {comp_count} components, {edge_count} edges")
    if edge_count:
        req.gaps.append("Auth mechanisms on edges may be incomplete — verify each flow")
    return req


# ── D2 parser ─────────────────────────────────────────────────────────────────

_D2_KEYWORDS = {
    'direction', 'style', 'shape', 'fill', 'stroke', 'stroke-dash',
    'stroke-width', 'double-border', 'font-color', 'bold', 'italic',
    'underline', 'text-transform', 'opacity', 'border-radius', 'shadow',
    'multiple', 'animated', 'link', 'tooltip', 'icon', 'width', 'height',
    'top', 'left', 'near', 'constraint',
}


def parse_d2(content: str, source_file: str) -> PartialReq:
    req = PartialReq(source_tool="arch-req-from-diagram", source_file=source_file)
    SRC = f"diagram:d2:{Path(source_file).name}"
    system_name = _primary_system(req, Path(source_file).stem, SRC)

    depth = 0
    count = 0
    for raw_line in content.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            depth += stripped.count('{') - stripped.count('}')
            continue
        if stripped == '}':
            depth = max(0, depth - 1)
            continue

        edge_match = re.match(r'^([\w._-]+)\s*->\s*([\w._-]+)\s*(?::\s*"?([^"]*)"?)?', stripped)
        if edge_match:
            count += 1
            label = (edge_match.group(3) or "").strip()
            req.flows.append(_edge_to_flow(
                edge_match.group(1).split(".")[-1],
                edge_match.group(2).split(".")[-1],
                label.replace("\\n", "/"), SRC, count,
            ))
            depth += stripped.count('{') - stripped.count('}')
            continue

        node_match = re.match(r'^([\w._-]+)\s*:\s*"?([^"{}\\]*)"?\s*\{?', stripped)
        if node_match:
            path = node_match.group(1)
            label = (node_match.group(2) or "").strip().replace("\\n", " ")
            key = path.split(".")[0].lower()
            if key in _D2_KEYWORDS or not label:
                depth += stripped.count('{') - stripped.count('}')
                continue

            if depth == 0:
                req.infra.append(_location_infra(label, SRC, len(req.infra) + 1))
            elif depth == 1:
                req.infra.append(_zone_infra(label, "", SRC, len(req.infra) + 1))
            else:
                kind, role, layer = _classify_label(label)
                if kind == "infra":
                    infra = PartialInfra(id=f"appliance_{len(req.infra) + 1}")
                    infra.name = fv(label, Confidence.HIGH, SRC)
                    infra.node_kind = fv(role, Confidence.MEDIUM, SRC)
                    req.infra.append(infra)
                else:
                    comp = PartialComponent(id=f"comp_{len(req.components) + 1}")
                    comp.system = fv(system_name, Confidence.MEDIUM, SRC)
                    comp.name = fv(_clean_label(label) or label, Confidence.HIGH, SRC)
                    comp.kind = fv("component", Confidence.LOW, SRC)
                    comp.component_role = fv(role, Confidence.MEDIUM, SRC)
                    if layer:
                        comp.layer = fv(layer, Confidence.LOW, SRC)
                    req.components.append(comp)

        depth += stripped.count('{') - stripped.count('}')
        depth = max(0, depth)

    req.no_coverage.extend(["auth", "credentials", "project_name"])
    return req


# ── arch YAML parser ──────────────────────────────────────────────────────────

def parse_arch_yaml(data: dict, source_file: str) -> PartialReq:
    """Direct mapping from our arch: YAML format to the req/v2 model."""
    req = PartialReq(source_tool="arch-req-from-diagram", source_file=source_file)
    SRC = f"diagram:yaml:{Path(source_file).name}"
    arch = data.get("arch", data)

    if arch.get("name"):
        req.project_name = fv(arch["name"], Confidence.HIGH, SRC)
    if arch.get("id"):
        req.project_id = fv(arch["id"], Confidence.HIGH, SRC)

    system_name = _primary_system(req, arch.get("name") or Path(source_file).stem, SRC)
    # Interactions address nodes by diagram id; the model references entities by
    # name, so endpoints are translated through the label each component was
    # emitted with (virtual nodes such as ``internet`` pass through unchanged).
    label_by_id: dict[str, str] = {}
    # The merger keys entities by name, so repeated labels would displace one
    # another: zones repeat across DCs ("Intranet", "DB Zone"), and two partner
    # boundaries can share one location string. A repeated label is qualified
    # with its region id. Parent references use the same emitted name, so a
    # zone resolves to the DC row rather than to a cleaned variant of it.
    regions = list(arch.get("deployment", []))

    def zkey_of(region: dict) -> str:
        return "network_zones" if region.get("type", "private_dc") == "private_dc" else "subnets"

    region_labels = [str(region.get("location", region.get("id", ""))) for region in regions]
    region_names = {}
    for region in regions:
        rid = region.get("id", "")
        label = str(region.get("location", rid))
        if not rid:
            rid = f"loc_{len(region_names) + 1}"
        if region_labels.count(label) > 1:
            label = f"{label} ({rid})"
        region_names[region.get("id", rid)] = label

    zone_labels = [
        _clean_label(zone.get("name", zone.get("id", "")))
        for region in regions for zone in region.get(zkey_of(region), [])
    ]
    ambiguous_zones = {label for label in zone_labels if zone_labels.count(label) > 1}

    def zone_label(zone: dict, region: dict) -> str:
        label = _clean_label(zone.get("name", zone.get("id", "")))
        rid = region.get("id", "")
        if label and label in ambiguous_zones and rid:
            return f"{label} ({rid})"
        return label

    # Container ids map to the infra names they were emitted with, so an
    # interaction between two containers becomes a network link rather than a
    # flow with a component-only reference.
    container_names: dict[str, str] = {}

    for region in regions:
        rid = region.get("id", "")
        location = region_names.get(rid, region.get("location", rid))
        infra = PartialInfra(id=rid or f"loc_{len(req.infra) + 1}")
        infra.name = fv(location, Confidence.HIGH, SRC)
        region_type = region.get("type", "private_dc")
        if region_type == "private_dc":
            infra.node_kind = fv("data_center", Confidence.HIGH, SRC)
            infra.infra_type = fv("private_cloud", Confidence.HIGH, SRC)
        else:
            infra.node_kind = fv("iaas_vpc_vnet", Confidence.HIGH, SRC)
            infra.infra_type = fv("public_cloud", Confidence.HIGH, SRC)
        if region.get("owner"):
            infra.infra_owner = fv(region["owner"], Confidence.HIGH, SRC)
        loc = re.search(r'\[([A-Z]{2,})\]', location)
        if loc:
            infra.country = fv(loc.group(1), Confidence.HIGH, SRC)
        req.infra.append(infra)
        container_names[rid] = location

        deployment_type, location_type = _deployment_type(region_type)
        for zone in region.get(zkey_of(region), []):
            zone_name = zone_label(zone, region)
            if zone_name:
                req.infra.append(_zone_infra(zone_name, location, SRC, len(req.infra) + 1))
                container_names[zone.get("id", "")] = zone_name
            for comp in zone.get("components", []):
                deployment = PartialDeployment(id=f"deployment_{len(req.deployments) + 1}")
                deployment.component = fv(comp.get("name", ""), Confidence.HIGH, SRC)
                deployment.environment = fv(region.get("role") or "prod", Confidence.MEDIUM, SRC)
                deployment.deployment_type = fv(deployment_type, Confidence.HIGH, SRC)
                deployment.location_type = fv(location_type, Confidence.HIGH, SRC)
                if zone_name:
                    deployment.infra = fv(zone_name, Confidence.MEDIUM, SRC)
                runtime = comp.get("runtime")
                if runtime:
                    deployment.runtime_detail = fv(runtime, Confidence.HIGH, SRC)
                    canonical = _runtime_type(runtime)
                    if canonical:
                        deployment.runtime_type = fv(canonical, Confidence.MEDIUM, SRC)
                req.deployments.append(deployment)

                pc = PartialComponent(id=comp.get("id", ""))
                pc.system = fv(system_name, Confidence.HIGH, SRC)
                pc.name = fv(comp.get("name", ""), Confidence.HIGH, SRC)
                pc.kind = fv(comp.get("kind", "component"), Confidence.MEDIUM, SRC)
                if comp.get("component_role"):
                    pc.component_role = fv(comp["component_role"], Confidence.MEDIUM, SRC)
                if comp.get("layer"):
                    pc.layer = fv(comp["layer"], Confidence.MEDIUM, SRC)
                if comp.get("sensitivity"):
                    pc.sensitivity = fv(comp["sensitivity"], Confidence.HIGH, SRC)
                if comp.get("encryption_at_rest"):
                    pc.encryption_at_rest = fv(comp["encryption_at_rest"], Confidence.HIGH, SRC)
                label_by_id[comp.get("id", "")] = comp.get("name", "")
                req.components.append(pc)

    # Authentication applies to the application tier that terminates ingress,
    # not to the network appliance in front of it, so the ingress chain is
    # walked past firewalls, load balancers, and security nodes.
    appliance_types = {"NW", "LB", "SEC"}
    reachable: dict[str, list[str]] = {}
    for iact in arch.get("interactions", []):
        reachable.setdefault(iact.get("from", ""), []).append(iact.get("to", ""))

    def _is_appliance(component_id: str) -> bool:
        for component in (
            comp
            for region in regions for zone in region.get(zkey_of(region), [])
            for comp in zone.get("components", []) or []
        ):
            if component.get("id") == component_id:
                return component.get("type") in appliance_types
        return False

    entry_points: list[str] = []
    pending = [target for source in _EXTERNAL_SOURCES for target in reachable.get(source, [])]
    seen: set[str] = set()
    while pending and not entry_points:
        next_hop: list[str] = []
        for node in pending:
            if node in seen:
                continue
            seen.add(node)
            if node in label_by_id and not _is_appliance(node):
                entry_points.append(label_by_id[node])
            else:
                next_hop.extend(reachable.get(node, []))
        pending = next_hop

    for i, iact in enumerate(arch.get("interactions", [])):
        source = iact.get("from", "")
        target = iact.get("to", "")
        if source in container_names and target in container_names:
            # Both ends are hosting/network nodes: this is a WAN or peering
            # link, not a component flow.
            protocol = str(iact.get("protocol") or "")
            link = PartialNetworkLink(id=f"link_{len(req.network_links) + 1}")
            link.source_infra = fv(container_names[source], Confidence.MEDIUM, SRC)
            link.target_infra = fv(container_names[target], Confidence.MEDIUM, SRC)
            method = _keyword_token(protocol, _LINK_METHOD_TOKENS)
            if method:
                link.method = fv(method, Confidence.MEDIUM, SRC)
            if protocol:
                link.encryption_method = fv(protocol, Confidence.LOW, SRC)
            req.network_links.append(link)
            continue

        flow = PartialFlow(id=f"flow_{i + 1}")
        # req/v2 has one external-flow sentinel, ``internet``. A rendered user
        # actor or office network represents the same pre-auth boundary rather
        # than a component row, so preserve the flow by normalising it here.
        flow_source = "internet" if source in _EXTERNAL_SOURCES else label_by_id.get(source, source)
        flow.source = fv(flow_source, Confidence.HIGH, SRC)
        flow.target = fv(label_by_id.get(target, target), Confidence.HIGH, SRC)
        if iact.get("protocol"):
            flow.protocol = fv(iact["protocol"], Confidence.HIGH, SRC)
        auth = iact.get("auth", "")
        if auth and auth not in ("—", "-", ""):
            flow.auth_method = fv(auth, Confidence.HIGH, SRC)
        if iact.get("via"):
            flow.via = fv(iact["via"], Confidence.HIGH, SRC)
        req.flows.append(flow)

    sec = arch.get("security", {})
    for env, solution in (sec.get("key_management") or {}).items():
        req.credentials.append({"environment": env, "solution": solution,
                                "_source": SRC, "_confidence": "high"})
    for index, key in enumerate(("user_auth_internal", "user_auth_external"), start=1):
        declaration = sec.get(key)
        if not declaration:
            continue
        auth = PartialAuth(id=f"auth_{index}")
        auth.subject = fv("user", Confidence.HIGH, SRC)
        # Authentication applies to the ingress component; without one in the
        # diagram the row cannot be anchored and is left for the interview.
        entry = declaration.get("entry_point") or (entry_points[0] if entry_points else None)
        if entry:
            auth.applies_to = fv(entry, Confidence.MEDIUM, SRC)
        if declaration.get("server"):
            auth.auth_server = fv(declaration["server"], Confidence.HIGH, SRC)
        protocol = _keyword_token(str(declaration.get("protocol") or ""), _AUTH_PROTOCOL_TOKENS)
        if protocol:
            auth.protocol = fv(protocol, Confidence.MEDIUM, SRC)
        if declaration.get("authorization"):
            auth.authorization = fv(declaration["authorization"], Confidence.HIGH, SRC)
        req.auth.append(auth)

    req.no_coverage.extend(["department", "project_scope"])
    return req


# ── PNG Vision (Claude API) ───────────────────────────────────────────────────

VISION_PROMPT = """You are an enterprise architecture analyst. Analyse this architecture diagram image and extract every architecture fact into the JSON shape below.

Modelling rules:
- `infra` holds hosting/network nodes: regions, data centres, VPC/VNets, zones, subnets, and network/security appliances (firewall, WAF, load balancer, identity provider, bastion, key management). node_kind is the topology role; infra_type is the hosting category; network_type is the network/security domain. Use "parent" to name the containing node.
- Firewalls, WAFs, load-balancer appliances, identity providers (ADFS/Entra) and key vaults are infra nodes, NOT components.
- `components` are application artefacts only (web frontend, backend services, BFF, API gateway, message bus, database, cache, storage, integration service). Use "system" to name the owning application, and set component_role accordingly.
- `flows` are directed arrows between components (caller -> provider); use "internet" as the source for external ingress; put appliances the path traverses in "via".
- `network_links` are undirected links between infra nodes (MPLS, ExpressRoute, VPN, VNet peering).
- `auth` is user/entry authentication only.
- Every reference between entities is a NAME, not an ID. Do not invent IDs.

Output ONLY valid JSON in this structure:
{
  "project": { "name": null, "id": null, "scope": "standalone|modification|e2e",
               "department": null, "data_classification": null },
  "infra": [ { "name": null, "node_kind": null, "infra_type": null, "network_type": null,
               "parent": null, "country": null, "vendor": null } ],
  "systems": [ { "name": null, "type": "new|existing|modified", "owner": null, "vendor": null } ],
  "components": [ { "system": null, "name": null, "kind": "service|component", "layer": null,
                    "component_role": null, "sensitivity": null } ],
  "deployments": [ { "component": null, "environment": "prod", "deployment_type": null,
                     "location_type": null, "infra": null, "runtime_type": null } ],
  "flows": [ { "from": null, "to": null, "protocol": null, "port": null,
               "auth_method": null, "encryption": null, "via": [], "notes": null } ],
  "network_links": [ { "from": null, "to": null, "method": null, "encrypted": null } ],
  "auth": [ { "subject": "user", "applies_to": null, "auth_server": null,
              "protocol": null, "authorization": null, "user_roles": [], "mfa": null } ],
  "gaps_noted": ["things uncertain or hard to read in the image"]
}
"""


def parse_png_via_vision(image_path: str, source_file: str) -> PartialReq:
    """Call the Claude Vision API to extract architecture from an image."""
    req = PartialReq(source_tool="arch-req-from-diagram", source_file=source_file)
    SRC = f"diagram:vision:{Path(source_file).name}"

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        req.gaps.append("ANTHROPIC_API_KEY not set — cannot use vision extraction")
        return req

    with open(image_path, "rb") as f:
        img_data = base64.standard_b64encode(f.read()).decode("utf-8")

    suffix = Path(image_path).suffix.lower()
    media_type_map = {".png": "image/png", ".jpg": "image/jpeg",
                      ".jpeg": "image/jpeg", ".webp": "image/webp"}
    media_type = media_type_map.get(suffix, "image/png")

    import urllib.request
    payload = json.dumps({
        "model": "claude-opus-4-6",
        "max_tokens": 8192,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image", "source": {
                    "type": "base64", "media_type": media_type, "data": img_data
                }},
                {"type": "text", "text": VISION_PROMPT}
            ]
        }]
    }).encode("utf-8")

    http_req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(http_req, timeout=90) as resp:
            response = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        req.gaps.append(f"Vision API error: {e}")
        return req

    text_content = ""
    for block in response.get("content", []):
        if block.get("type") == "text":
            text_content = block["text"]
            break

    json_match = re.search(r'\{[\s\S]+\}', text_content)
    if not json_match:
        req.gaps.append("Vision API returned non-JSON response")
        return req

    try:
        extracted = json.loads(json_match.group())
    except json.JSONDecodeError as e:
        req.gaps.append(f"Vision API JSON parse error: {e}")
        return req

    req = v2_json_to_partial(extracted, source_tool="arch-req-from-diagram",
                             source_file=source_file, confidence=Confidence.LOW,
                             source_label=SRC)
    req.no_coverage.extend(["credentials", "language", "framework", "department"])
    req.gaps.append("Vision extraction confidence is LOW — all values require human verification")
    return req


# ── Main entry point ──────────────────────────────────────────────────────────

def parse_diagram(input_path: str) -> PartialReq:
    """Dispatch to the correct parser based on file extension."""
    path = Path(input_path)
    ext = path.suffix.lower()

    if ext in (".drawio", ".xml"):
        with open(input_path, encoding="utf-8") as f:
            return parse_drawio(f.read(), input_path)

    elif ext == ".d2":
        with open(input_path, encoding="utf-8") as f:
            return parse_d2(f.read(), input_path)

    elif ext in (".yaml", ".yml"):
        with open(input_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return parse_arch_yaml(data, input_path)

    elif ext in (".png", ".jpg", ".jpeg", ".webp"):
        return parse_png_via_vision(input_path, input_path)

    else:
        req = PartialReq(source_tool="arch-req-from-diagram", source_file=input_path)
        req.gaps.append(f"Unsupported file extension: {ext}")
        return req


def main():
    parser = argparse.ArgumentParser(description="Extract requirements from architecture diagram")
    parser.add_argument("-i", "--input", required=True, help="Input file (.drawio/.d2/.yaml/.png)")
    parser.add_argument("-o", "--output", default=None, help="Output partial-req YAML file")
    args = parser.parse_args()

    req = parse_diagram(args.input)
    out = partial_req_to_yaml(req)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"✓ Partial requirements written: {args.output}")
        print(f"  Infra nodes: {len(req.infra)}  |  Components: {len(req.components)}"
              f"  |  Flows: {len(req.flows)}")
        if req.gaps:
            print("  Gaps/notes:")
            for g in req.gaps:
                print(f"    • {g}")
    else:
        print(out)


if __name__ == "__main__":
    main()
