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
    PartialReq, PartialSystem, PartialInfra, PartialComponent, PartialFlow,
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

    for region in arch.get("deployment", []):
        rid = region.get("id", "")
        location = region.get("location", rid)
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

        zkey = "network_zones" if region_type == "private_dc" else "subnets"
        for zone in region.get(zkey, []):
            zone_name = _clean_label(zone.get("name", zone.get("id", "")))
            if zone_name:
                req.infra.append(_zone_infra(zone_name, _clean_label(location), SRC,
                                             len(req.infra) + 1))
            for comp in zone.get("components", []):
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
                req.components.append(pc)

    for i, iact in enumerate(arch.get("interactions", [])):
        flow = PartialFlow(id=f"flow_{i + 1}")
        flow.source = fv(iact.get("from", ""), Confidence.HIGH, SRC)
        flow.target = fv(iact.get("to", ""), Confidence.HIGH, SRC)
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
    if sec.get("user_auth_internal"):
        ua = sec["user_auth_internal"]
        entry = ua.get("entry_point") or system_name
        from .normalizer import PartialAuth
        auth = PartialAuth(id="auth_1")
        auth.subject = fv("user", Confidence.HIGH, SRC)
        auth.applies_to = fv(entry, Confidence.MEDIUM, SRC)
        if ua.get("server"):
            auth.auth_server = fv(ua["server"], Confidence.HIGH, SRC)
        if ua.get("protocol"):
            auth.protocol = fv(ua["protocol"], Confidence.HIGH, SRC)
        if ua.get("authorization"):
            auth.authorization = fv(ua["authorization"], Confidence.HIGH, SRC)
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
