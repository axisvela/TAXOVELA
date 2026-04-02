"""
from_diagram.py — Extract requirements from architecture diagram files.

Supports:
  .drawio / .xml   — draw.io XML: parse mxCell hierarchy
  .d2              — D2 diagram: parse container + edge syntax
  .yaml / .yml     — arch: YAML (our own format): direct mapping
  .png / .jpg / .webp — Architecture image: Claude Vision API extraction

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
import sys
import base64
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from normalizer import (
    PartialReq, PartialApplication, PartialComponent, PartialInteraction,
    FieldValue, Confidence, fv, partial_req_to_yaml
)


# ── draw.io XML parser ────────────────────────────────────────────────────────

def _clean_html(text: str) -> str:
    """Strip HTML tags and decode entities from draw.io cell values."""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>') \
               .replace('&nbsp;', ' ').replace('&#39;', "'").replace('&quot;', '"')
    return ' '.join(text.split()).strip()


def _classify_drawio_shape(style: str) -> str:
    """Map draw.io style string to component type."""
    s = style.lower()
    if "hexagon" in s:            return "LB"
    if "parallelogram" in s:      return "IP"
    if "ellipse" in s or "oval" in s or "double" in s and "ellipse" in s: return "SEC"
    if "mxgraph.flowchart.database" in s or "cylinder" in s: return "DB"
    if "mxgraph.basic.wave" in s: return "DS"   # data lake
    if "mxgraph.flowchart.stored_data" in s: return "DS"
    if "cloud_rect" in s:         return "SaaS"
    if "umlactor" in s:           return "Actor"
    if "aws4" in s or "azure" in s or "gcp" in s: return "NW"
    if "ext" in s and "double" in s: return "_DC_CONTAINER"
    if "shape=ext" in s:          return "_ZONE_CONTAINER"
    if "group" in s:              return "_GROUP"
    if "rounded=1" in s:          return "FE"
    if "rounded=0" in s and "dashed=1" not in s: return "BE"
    if "dashed=1" in s:           return "BE"
    return "BE"


def _is_container(style: str, value: str) -> bool:
    s = style.lower()
    return ("ext" in s and "double" in s) or "container=1" in s or \
           ("aws4.group" in s) or ("azure" in s and "container=1" in s)


def _is_zone(style: str) -> bool:
    s = style.lower()
    return ("ext" in s and "dashed=1" in s) or \
           ("shape=ext" in s and "dashed" in s) or \
           ("fillcolor" in s and "dashed" in s)


def parse_drawio(content: str, source_file: str) -> PartialReq:
    req = PartialReq(source_tool="arch-req-from-diagram", source_file=source_file)
    SRC = f"diagram:drawio:{Path(source_file).name}"

    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        req.gaps.append(f"XML parse error: {e}")
        return req

    # Collect all mxCell elements
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

    # Build parent → children map
    children: dict[str, list[str]] = {}
    for cid, c in cells.items():
        p = c["parent"]
        children.setdefault(p, []).append(cid)

    # Identify DC containers (top-level large double-border rects)
    dc_count = 0
    zone_count = 0
    comp_count = 0
    edge_count = 0

    for cid, c in cells.items():
        if not c["vertex"] or c["edge"]:
            continue
        style = c["style"]
        value = c["value"]
        ctype = _classify_drawio_shape(style)

        if ctype == "_DC_CONTAINER" and value:
            dc_count += 1
            # Try to extract location and owner from label
            # e.g. "Hohhot DC, Inner Mongolia [CN] (InfraSec)"
            loc_match = re.search(r'\[([A-Z]{2,})\]', value)
            country = loc_match.group(1) if loc_match else ""
            owner_match = re.search(r'\(([^)]+)\)', value)
            owner = owner_match.group(1) if owner_match else ""
            dc_name = re.sub(r'\s*\[[^\]]*\]\s*', '', value).strip()
            dc_name = re.sub(r'\s*\([^)]*\)\s*', '', dc_name).strip()

            app = PartialApplication(id=f"dc_{dc_count}")
            app.name = fv(dc_name, Confidence.HIGH, SRC)
            if country:
                app.country = fv(country, Confidence.HIGH, SRC)
            if owner:
                app.infra_owner = fv(owner, Confidence.HIGH, SRC)
            # Infer platform
            if any(x in value.lower() for x in ("aws", "vpc", "amazon")):
                app.platform = fv("aws", Confidence.MEDIUM, SRC)
            elif any(x in value.lower() for x in ("azure", "vnet", "microsoft")):
                app.platform = fv("azure", Confidence.MEDIUM, SRC)
            else:
                app.platform = fv("private_dc", Confidence.MEDIUM, SRC)
            app.dc_or_region = fv(dc_name, Confidence.HIGH, SRC)
            req.applications.append(app)

        elif ctype == "_ZONE_CONTAINER" and value:
            zone_count += 1
            # Zones tell us zone/subnet names
            zone_name = value.lower()
            # Store as open item (zones are attributes of their parent DC)
            req.open_items.append({
                "type": "zone_found",
                "value": value,
                "cell_id": cid,
                "parent": c["parent"],
            })

        elif value and ctype not in ("_GROUP", "Actor", "_DC_CONTAINER", "_ZONE_CONTAINER", "NW"):
            comp_count += 1
            comp = PartialComponent(id=f"comp_{comp_count}", app_id="unknown")
            comp.name = fv(value, Confidence.HIGH, SRC)
            comp.comp_type = fv(ctype, Confidence.MEDIUM, SRC)
            # Try to detect runtime from label
            for rt in ["K8s", "Internal K8s", "ECS", "Lambda", "VM", "AKS"]:
                if rt.lower() in value.lower():
                    comp.runtime = fv(rt, Confidence.LOW, SRC)
                    break
            req.components.append(comp)

    # Extract edges (interactions)
    for cid, c in cells.items():
        if not c["edge"]:
            continue
        edge_count += 1
        src_cell = cells.get(c["source"], {})
        tgt_cell = cells.get(c["target"], {})
        label = c["value"]

        # Parse protocol/auth from label (e.g. "HTTPS/OAuth2.0")
        protocol = ""
        auth = ""
        if "/" in label:
            parts = label.split("/", 1)
            protocol = parts[0].strip()
            auth = parts[1].strip() if len(parts) > 1 else ""
        elif label:
            protocol = label

        interaction = PartialInteraction(id=f"int_{edge_count}")
        interaction.from_component = fv(
            src_cell.get("value", c["source"]), Confidence.HIGH, SRC
        )
        interaction.to_component = fv(
            tgt_cell.get("value", c["target"]), Confidence.HIGH, SRC
        )
        if protocol:
            interaction.protocol = fv(protocol, Confidence.MEDIUM, SRC)
        if auth:
            interaction.auth_method = fv(auth, Confidence.MEDIUM, SRC)
        req.interactions.append(interaction)

    req.no_coverage.extend(["user_auth", "credentials", "data_encryption",
                              "project_name", "department"])
    req.gaps.append(f"draw.io: found {dc_count} DC containers, {zone_count} zones, "
                    f"{comp_count} components, {edge_count} edges")
    if edge_count > 0:
        req.gaps.append("Auth mechanisms on edges may be incomplete — verify each interaction")

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

    comp_count = 0
    int_count = 0
    indent_depth = 0  # track block nesting depth via braces

    for raw_line in content.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            # Update depth counter for closing braces in blank/comment lines
            indent_depth += stripped.count('{') - stripped.count('}')
            continue

        # Closing brace only
        if stripped == '}':
            indent_depth = max(0, indent_depth - 1)
            continue

        # Edge detection at top level: path.path -> path.path : "label"
        edge_match = re.match(r'^([\w._-]+)\s*->\s*([\w._-]+)\s*(?::\s*"?([^"]*)"?)?', stripped)
        if edge_match:
            int_count += 1
            src_path = edge_match.group(1)
            tgt_path = edge_match.group(2)
            label = (edge_match.group(3) or "").strip()

            protocol, auth = "", ""
            if "\\n" in label:
                parts = label.split("\\n", 1)
                protocol = parts[0].strip("()")
                auth = parts[1].strip("()")
            elif "/" in label:
                parts = label.split("/", 1)
                protocol = parts[0]
                auth = parts[1].strip("()")
            else:
                protocol = label

            interaction = PartialInteraction(id=f"int_{int_count}")
            # Use last segment of dot-path as the component name key
            interaction.from_component = fv(src_path.split(".")[-1], Confidence.HIGH, SRC)
            interaction.to_component   = fv(tgt_path.split(".")[-1], Confidence.HIGH, SRC)
            if protocol:
                interaction.protocol = fv(protocol, Confidence.MEDIUM, SRC)
            if auth:
                interaction.auth_method = fv(auth, Confidence.LOW, SRC,
                                             "Extracted from D2 edge label — verify")
            req.interactions.append(interaction)
            indent_depth += stripped.count('{') - stripped.count('}')
            continue

        # Node / container: identifier: "label" {
        node_match = re.match(r'^([\w._-]+)\s*:\s*"?([^"{}\\]*)"?\s*\{?', stripped)
        if node_match:
            path = node_match.group(1)
            label = (node_match.group(2) or "").strip().replace("\\n", " ")
            key = path.split(".")[0].lower()

            # Skip D2 built-in keywords and style properties
            if key in _D2_KEYWORDS or not label:
                indent_depth += stripped.count('{') - stripped.count('}')
                continue

            comp_count += 1
            depth = indent_depth  # current nesting depth when this line appears

            if depth == 0:
                # Top-level: DC / Cloud / Internet
                app = PartialApplication(id=f"app_{comp_count}")
                app.name = fv(label, Confidence.HIGH, SRC)
                app.dc_or_region = fv(label, Confidence.HIGH, SRC)
                if any(x in label.lower() for x in ("aws", "amazon")):
                    app.platform = fv("aws", Confidence.MEDIUM, SRC)
                elif any(x in label.lower() for x in ("azure", "microsoft")):
                    app.platform = fv("azure", Confidence.MEDIUM, SRC)
                else:
                    app.platform = fv("private_dc", Confidence.MEDIUM, SRC)
                loc = re.search(r'\[([A-Z]{2,})\]', label)
                if loc:
                    app.country = fv(loc.group(1), Confidence.HIGH, SRC)
                if label.lower() not in ("internet", "user", "office_network"):
                    req.applications.append(app)

            elif depth == 1:
                # Zone / subnet
                req.open_items.append({"type": "zone", "label": label, "depth": depth})

            else:
                # Component (depth 2+)
                # Extract runtime hint from multi-line label
                runtime = ""
                for rt in ["K8s", "Internal K8s", "ECS", "Lambda", "VM", "AKS"]:
                    if rt.lower() in label.lower():
                        runtime = rt
                        break
                # Clean label (remove runtime/tech annotations)
                clean_label = re.sub(r'\s*\([^)]*\)', '', label).strip()
                clean_label = re.sub(r'\s*\[[^\]]*\]', '', clean_label).strip()
                clean_label = clean_label.lstrip("⚠ ").strip()

                comp = PartialComponent(id=f"comp_{comp_count}", app_id="unknown")
                comp.name = fv(clean_label or label, Confidence.HIGH, SRC)

                # Infer comp_type from original label hints
                orig = label.lower()
                if "load balancer" in orig or "f5" in orig or "waf" in orig or "alb" in orig:
                    comp.comp_type = fv("LB", Confidence.MEDIUM, SRC)
                elif "gateway" in orig or "wso2" in orig or "apih" in orig or "api gateway" in orig:
                    comp.comp_type = fv("IP", Confidence.MEDIUM, SRC)
                elif "kafka" in orig or "queue" in orig or "mq" in orig:
                    comp.comp_type = fv("MQ", Confidence.MEDIUM, SRC)
                elif "postgresql" in orig or "mysql" in orig or "redis" in orig or "rds" in orig:
                    comp.comp_type = fv("DB", Confidence.MEDIUM, SRC)
                elif "adfs" in orig or "entra" in orig or "key vault" in orig or "secrets" in orig:
                    comp.comp_type = fv("SEC", Confidence.MEDIUM, SRC)

                if runtime:
                    comp.runtime = fv(runtime, Confidence.LOW, SRC)

                # Extract language/framework from parenthetical hints
                lang_match = re.search(r'\(([^)]+)\)', label)
                if lang_match:
                    parts = [p.strip() for p in lang_match.group(1).split(",")]
                    if parts and any(x in parts[0].lower() for x in ("java", "python", "node", "go", ".net", "javascript")):
                        comp.language = fv(parts[0], Confidence.MEDIUM, SRC)
                    if len(parts) > 1:
                        comp.framework = fv(parts[1], Confidence.MEDIUM, SRC)

                if "⚠" in label or "restricted" in label.lower() or "confidential" in label.lower():
                    comp.sensitivity = fv("Company Confidential", Confidence.LOW, SRC,
                                          "Inferred from ⚠ marker")
                req.components.append(comp)

        # Update brace depth
        indent_depth += stripped.count('{') - stripped.count('}')
        indent_depth = max(0, indent_depth)

    req.no_coverage.extend(["user_auth", "credentials", "data_encryption"])
    return req


# ── arch YAML parser ──────────────────────────────────────────────────────────

def parse_arch_yaml(data: dict, source_file: str) -> PartialReq:
    """Direct mapping from arch: YAML format to PartialReq."""
    req = PartialReq(source_tool="arch-req-from-diagram", source_file=source_file)
    SRC = f"diagram:yaml:{Path(source_file).name}"
    arch = data.get("arch", data)

    # Project info
    if arch.get("name"):
        req.project_name = fv(arch["name"], Confidence.HIGH, SRC)
    if arch.get("id"):
        req.project_id = fv(arch["id"], Confidence.HIGH, SRC)

    # Deployment
    for region in arch.get("deployment", []):
        rid = region.get("id", "")
        app = PartialApplication(id=rid)
        app.dc_or_region = fv(region.get("location", rid), Confidence.HIGH, SRC)
        app.platform = fv(region.get("type", "private_dc"), Confidence.HIGH, SRC)
        if region.get("owner"):
            app.infra_owner = fv(region["owner"], Confidence.HIGH, SRC)
        # Extract country from location string
        loc = re.search(r'\[([A-Z]{2,})\]', region.get("location", ""))
        if loc:
            app.country = fv(loc.group(1), Confidence.HIGH, SRC)
        req.applications.append(app)

        # Components within zones
        zkey = "network_zones" if region.get("type") == "private_dc" else "subnets"
        for zone in region.get(zkey, []):
            for comp in zone.get("components", []):
                pc = PartialComponent(id=comp.get("id", ""), app_id=rid)
                pc.name = fv(comp.get("name", ""), Confidence.HIGH, SRC)
                pc.comp_type = fv(comp.get("type", "BE"), Confidence.HIGH, SRC)
                if comp.get("language"):
                    pc.language = fv(comp["language"], Confidence.HIGH, SRC)
                if comp.get("framework"):
                    pc.framework = fv(comp["framework"], Confidence.HIGH, SRC)
                if comp.get("runtime"):
                    pc.runtime = fv(comp["runtime"], Confidence.HIGH, SRC)
                if comp.get("sensitivity"):
                    pc.sensitivity = fv(comp["sensitivity"], Confidence.HIGH, SRC)
                req.components.append(pc)

    # Interactions
    for i, iact in enumerate(arch.get("interactions", [])):
        interaction = PartialInteraction(id=f"int_{i+1}")
        interaction.from_component = fv(iact.get("from", ""), Confidence.HIGH, SRC)
        interaction.to_component   = fv(iact.get("to", ""), Confidence.HIGH, SRC)
        if iact.get("protocol"):
            interaction.protocol = fv(iact["protocol"], Confidence.HIGH, SRC)
        auth = iact.get("auth", "")
        if auth and auth not in ("—", "-", ""):
            interaction.auth_method = fv(auth, Confidence.HIGH, SRC)
        req.interactions.append(interaction)

    # Security
    sec = arch.get("security", {})
    for env, solution in sec.get("key_management", {}).items():
        req.credentials.append({
            "environment": env,
            "solution": solution,
            "_source": SRC,
            "_confidence": "high",
        })
    if sec.get("user_auth_internal"):
        ua = sec["user_auth_internal"]
        pua = __import__("normalizer", fromlist=["PartialUserAuth"]).PartialUserAuth(
            entry_point="internal"
        )
        pua.auth_server = fv(ua.get("server", ""), Confidence.HIGH, SRC)
        pua.auth_protocol = fv(ua.get("protocol", ""), Confidence.HIGH, SRC)
        req.user_auth.append(pua)

    req.no_coverage.extend(["department", "project_scope"])
    return req


# ── PNG Vision (Claude API) ───────────────────────────────────────────────────

VISION_PROMPT = """You are an enterprise architecture analyst. Analyze this architecture diagram image and extract all information into structured JSON.

Extract:
1. All regions/data centers/clouds with their labels and apparent location (country/city)
2. All network zones (DMZ, App Zone, DB Zone, Intranet, VPC, Subnet, etc.)
3. All technical components with their names and apparent type
4. All connections/arrows with their labels (protocol, auth method if visible)
5. Any visible security components (ADFS, Enterprise ID, F5, WAF, etc.)
6. Any data sensitivity indicators (⚠, Restricted, Confidential labels)

Output ONLY valid JSON in this exact structure:
{
  "regions": [
    {
      "label": "exact text from diagram",
      "location_hint": "country or city if visible",
      "type": "private_dc|aws|azure|saas",
      "owner": "InfraSec|BizIT|third_party|unknown",
      "zones": [
        {
          "label": "zone name",
          "type": "dmz|app_zone|db_zone|intranet|hub|spoke|subnet",
          "components": [
            {
              "name": "component name",
              "type": "FE|BE|DB|MQ|IP|LB|SEC|NW",
              "shape_hint": "hexagon|parallelogram|cylinder|rectangle|circle|cloud",
              "runtime_hint": "K8s|Internal K8s|ECS|VM|Lambda|AKS|unknown",
              "sensitivity": "Restricted|Confidential|Internal|none"
            }
          ]
        }
      ]
    }
  ],
  "interactions": [
    {
      "from": "source component name (exact)",
      "to": "target component name (exact)",
      "protocol": "HTTPS|Kafka|SFTP|JDBC|RFC|TCP|unknown",
      "auth": "OAuth2.0|SAML|mTLS|SASL/SCRAM|PWD|unknown",
      "label_visible": "exact arrow label text if readable"
    }
  ],
  "confidence_notes": ["list of things uncertain or hard to read in the image"]
}
"""

def parse_png_via_vision(image_path: str, source_file: str) -> PartialReq:
    """Call Claude Vision API to extract architecture from an image."""
    req = PartialReq(source_tool="arch-req-from-diagram", source_file=source_file)
    SRC = f"diagram:vision:{Path(source_file).name}"

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        req.gaps.append("ANTHROPIC_API_KEY not set — cannot use vision extraction")
        return req

    # Read and base64-encode the image
    with open(image_path, "rb") as f:
        img_data = base64.standard_b64encode(f.read()).decode("utf-8")

    suffix = Path(image_path).suffix.lower()
    media_type_map = {".png": "image/png", ".jpg": "image/jpeg",
                      ".jpeg": "image/jpeg", ".webp": "image/webp"}
    media_type = media_type_map.get(suffix, "image/png")

    import urllib.request
    payload = json.dumps({
        "model": "claude-opus-4-6",
        "max_tokens": 4096,
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
        with urllib.request.urlopen(http_req, timeout=60) as resp:
            response = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        req.gaps.append(f"Vision API error: {e}")
        return req

    # Extract JSON from response
    text_content = ""
    for block in response.get("content", []):
        if block.get("type") == "text":
            text_content = block["text"]
            break

    # Parse JSON from response (may be wrapped in code fences)
    json_match = re.search(r'\{[\s\S]+\}', text_content)
    if not json_match:
        req.gaps.append("Vision API returned non-JSON response")
        return req

    try:
        extracted = json.loads(json_match.group())
    except json.JSONDecodeError as e:
        req.gaps.append(f"Vision API JSON parse error: {e}")
        return req

    # Map extracted data → PartialReq
    for i, region in enumerate(extracted.get("regions", [])):
        app = PartialApplication(id=f"vision_region_{i+1}")
        app.name = fv(region.get("label", ""), Confidence.MEDIUM, SRC)
        app.dc_or_region = fv(region.get("label", ""), Confidence.MEDIUM, SRC)
        app.platform = fv(region.get("type", "unknown"), Confidence.LOW, SRC)
        if region.get("location_hint"):
            app.country = fv(region["location_hint"], Confidence.LOW, SRC,
                             "Inferred from image — verify")
        if region.get("owner"):
            app.infra_owner = fv(region["owner"], Confidence.LOW, SRC)
        req.applications.append(app)

        for zone in region.get("zones", []):
            for j, comp in enumerate(zone.get("components", [])):
                pc = PartialComponent(
                    id=f"vision_comp_{i+1}_{j+1}",
                    app_id=f"vision_region_{i+1}"
                )
                pc.name = fv(comp.get("name", ""), Confidence.MEDIUM, SRC)
                pc.comp_type = fv(comp.get("type", "BE"), Confidence.LOW, SRC)
                if comp.get("runtime_hint") and comp["runtime_hint"] != "unknown":
                    pc.runtime = fv(comp["runtime_hint"], Confidence.LOW, SRC,
                                   "Inferred from image")
                if comp.get("sensitivity") and comp["sensitivity"] != "none":
                    pc.sensitivity = fv(comp["sensitivity"], Confidence.LOW, SRC)
                req.components.append(pc)

    for i, iact in enumerate(extracted.get("interactions", [])):
        interaction = PartialInteraction(id=f"vision_int_{i+1}")
        interaction.from_component = fv(iact.get("from", ""), Confidence.MEDIUM, SRC)
        interaction.to_component   = fv(iact.get("to", ""), Confidence.MEDIUM, SRC)
        if iact.get("protocol") and iact["protocol"] != "unknown":
            interaction.protocol = fv(iact["protocol"], Confidence.LOW, SRC)
        if iact.get("auth") and iact["auth"] != "unknown":
            interaction.auth_method = fv(iact["auth"], Confidence.LOW, SRC,
                                        "Extracted from image — verify accuracy")
        req.interactions.append(interaction)

    # Record confidence notes as gaps
    for note in extracted.get("confidence_notes", []):
        req.gaps.append(f"Vision uncertainty: {note}")

    req.no_coverage.extend(["user_auth", "credentials", "data_encryption",
                              "language", "framework", "department"])
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
    parser.add_argument("--json", action="store_true", help="Output JSON instead of YAML")
    args = parser.parse_args()

    req = parse_diagram(args.input)
    out = partial_req_to_yaml(req)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"✓ Partial requirements written: {args.output}")
        print(f"  Components found: {len(req.components)}")
        print(f"  Interactions found: {len(req.interactions)}")
        print(f"  Regions/DCs found: {len(req.applications)}")
        if req.gaps:
            print("  Gaps/notes:")
            for g in req.gaps:
                print(f"    • {g}")
    else:
        print(out)


if __name__ == "__main__":
    main()
