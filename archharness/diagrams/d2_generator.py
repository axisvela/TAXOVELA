"""
d2_generator.py  — Architecture YAML → D2 diagram (.d2)

D2 (https://d2lang.com) natively supports arbitrary container nesting via
dot-notation IDs and {} blocks, making it the best text format for deep
enterprise topology (DC → Zone → App Group → Component).

Usage:
    python arch_diagram_gen.py -i arch.yaml --d2 output.d2
    d2 output.d2 output.svg          # render with d2 CLI
    d2 --layout=elk output.d2 output.svg   # elk layout for deep nesting

D2 shape mapping (closest approximation to Company shape spec):
    firewalls (hexagon)  → shape: hexagon
    LB / trapezoid       → rectangle (D2 has no trapezoid)
    standard shapes      → see _D2_STANDARD_SHAPES
    IP / parallelogram   → shape: parallelogram
    MQ / message_queue   → shape: queue
    DB / cylinder        → shape: cylinder    (D2 native)
    DC container         → shape: cloud (outer) or plain container
    Zone                 → plain labeled container
    AWS VPC              → shape: cloud
    FE                   → shape: rectangle (rounded via style)
    BE (default)         → shape: rectangle  + dashed border
    SEC / circle         → shape: oval
    bastion              → shape: diamond

Shapes without a D2 equivalent (pentagon, cube, pyramid) fall back to the
default rectangle rather than to a misleading approximation.
"""

import re
from typing import Optional

from . import labels, styles


# ── D2 style constants ────────────────────────────────────────────────────────

# Status → fill color (D2 style.fill)
STATUS_FILL = {
    "newly_created": "#D32F2F",
    "changed":       "#FBC02D",
    "unchanged":     "#FFFFFF",
    "in_plan":       "#66BB6A",
    "retired":       "#9E9E9E",
    "biz_owned":     "#8E24AA",
    "third_party":   "#FB8C00",
}

STATUS_FONT = {
    "newly_created": "#FFFFFF",
    "changed":       "#000000",
    "retired":       "#FFFFFF",
    "biz_owned":     "#FFFFFF",
    "third_party":   "#000000",
}

ZONE_FILL = {
    "dmz":      "#FFFDE7",
    "app_zone": "#F1F8E9",
    "db_zone":  "#E3F2FD",
    "intranet": "#F3E5F5",
    "hub":      "#FFF8E1",
    "spoke":    "#E8F5E9",
    "default":  "#FAFAFA",
}

ZONE_STROKE = {
    "dmz":      "#F9A825",
    "app_zone": "#558B2F",
    "db_zone":  "#1565C0",
    "intranet": "#7B1FA2",
    "hub":      "#E65100",
    "spoke":    "#2E7D32",
    "default":  "#BDBDBD",
}


# ── ID sanitiser ──────────────────────────────────────────────────────────────

def _d2id(raw: str) -> str:
    """Convert a YAML id to a valid D2 identifier (alphanum + underscore)."""
    s = re.sub(r"[^a-zA-Z0-9_]", "_", raw)
    if s and s[0].isdigit():
        s = "_" + s
    return s


# ── Shape selector ────────────────────────────────────────────────────────────
#
# Standard shapes mapped to the closest shape this D2 release supports. Shapes
# with no equivalent (pentagon, cube, pyramid) stay D2's default rectangle.

_D2_STANDARD_SHAPES = {
    "card": "page",
    "stored_data": "stored_data",
    "double_ellipse": "oval",
    "diamond": "diamond",
    "document": "document",
    "note": "callout",
    "step": "step",
    "cloud": "cloud",
}


def _d2_shape(comp: dict) -> Optional[str]:
    ctype = comp.get("type", "BE")
    shape = comp.get("shape", "")
    if shape in _D2_STANDARD_SHAPES:               return _D2_STANDARD_SHAPES[shape]
    if shape == "hexagon":                         return "hexagon"
    if ctype == "LB" or shape == "trapezoid":
        # D2 has no trapezoid; a plain rectangle keeps the load balancer from
        # being confused with the firewall hexagon.
        return None
    if ctype == "IP" or shape == "parallelogram":  return "parallelogram"
    if ctype == "MQ" or shape == "message_queue":  return "queue"
    if ctype == "DB" or shape == "cylinder":       return "cylinder"
    if ctype == "SEC" or shape == "circle":        return "oval"
    if ctype == "FE":                              return "rectangle"
    if shape == "bastion":                         return "diamond"
    return None   # rectangle is D2 default


def _comp_style_block(comp: dict) -> str:
    """D2 style block: the lifecycle status drives the fill (default blue-grey)."""
    lines = []
    ctype = comp.get("type", "BE")
    sens  = comp.get("sensitivity", "")

    colour = labels.component_fill(comp)
    lines.append(f'fill: "{colour["fill"]}"')
    lines.append(f'stroke: "{colour["stroke"]}"')
    lines.append(f'font-color: "{colour["text"]}"')

    if ctype in ("BE", "FE", "API", "BFF"):
        lines.append("stroke-dash: 5")
    if comp.get("is_group"):
        lines.append("stroke-dash: 4")

    # Sensitive data: bold label
    if "Restricted" in sens or "Confidential" in sens:
        lines.append("bold: true")

    return "{\n    style {\n      " + "\n      ".join(lines) + "\n    }\n  }"


# ── Component label ────────────────────────────────────────────────────────────

def _comp_label(comp: dict) -> str:
    name = labels.component_name(comp)      # lifecycle markers live in the colour
    sens = comp.get("sensitivity", "")
    if "Restricted" in sens or "Confidential" in sens:
        name = "⚠ " + name
    tech = labels.tech_line(comp)
    parts = [name] + ([tech] if tech else [])
    return "\\n".join(parts)   # D2 uses \n for multi-line labels


# ── Main generator ─────────────────────────────────────────────────────────────

def validate_d2_refs(arch: dict) -> None:
    """Fail closed on duplicate IDs and dangling interaction endpoints."""
    reserved = {"internet", "user", "office-network"}
    seen: set[str] = set()
    duplicates: list[str] = []
    declared: set[str] = set(reserved)

    def _add(node_id: str) -> None:
        if not node_id or node_id in reserved:
            return
        if node_id in seen:
            if node_id not in duplicates:
                duplicates.append(node_id)
        else:
            seen.add(node_id)
            declared.add(node_id)

    for region in arch.get("deployment", []) or []:
        _add(region.get("id", ""))
        zones_key = "network_zones" if region.get("type", "private_dc") == "private_dc" else "subnets"
        for zone in region.get(zones_key, []) or []:
            _add(zone.get("id", ""))
            for comp in zone.get("components", []) or []:
                _add(comp.get("id", ""))
    if duplicates:
        raise ValueError(f"Duplicate component IDs: {', '.join(sorted(duplicates))}")

    unresolved = [
        f"{iact.get('from', '') or '?'} -> {iact.get('to', '') or '?'}"
        for iact in arch.get("interactions", []) or []
        if iact.get("from", "") not in declared or iact.get("to", "") not in declared
    ]
    if unresolved:
        raise ValueError(f"Unresolved interaction references: {'; '.join(unresolved)}")


def generate_d2(arch: dict) -> str:
    """
    Convert an architecture dict to a D2 diagram string.

    Hierarchy:
        region (DC/VPC)
          └── zone/subnet
                └── component
    Edges drawn at top level, referencing full dot-path IDs.
    """
    validate_d2_refs(arch)
    lines = []

    # ── Header comment ──────────────────────────────────────────────────────
    header_rows = labels.header_fields(arch)
    lines.append(f"# {header_rows[0][1]}")
    lines.append("# " + "  |  ".join(f"{label}: {value}" for label, value in header_rows[1:]))
    lines.append("")

    # ── D2 direction ────────────────────────────────────────────────────────
    lines.append("direction: right")
    lines.append("")

    # ── Internet / user virtual nodes ──────────────────────────────────────
    lines.append("internet: Internet {")
    lines.append('  shape: cloud')
    lines.append("  style {")
    lines.append('    fill: "#E8E8E8"')
    lines.append("  }")
    lines.append("}")
    lines.append("")

    # ── Build a component → full-path map for edge resolution ───────────────
    # comp_id → "region_id.zone_id.comp_id"  (D2 dot-path)
    comp_path: dict[str, str] = {}
    comp_path["internet"]       = "internet"
    comp_path["user"]           = "user"
    comp_path["office-network"] = "office_network"

    deployment = arch.get("deployment", [])

    for region in deployment:
        rid   = _d2id(region["id"])
        rtype = region.get("type", "private_dc")
        zkey  = "network_zones" if rtype == "private_dc" else "subnets"
        # Containers are addressable endpoints too: an interaction may name a
        # VNet peering or a DC-to-DC WAN link rather than a component.
        comp_path[region["id"]] = rid
        for zone in region.get(zkey, []):
            zid = _d2id(zone["id"])
            comp_path[zone["id"]] = f"{rid}.{zid}"
            for comp in zone.get("components", []):
                cid = _d2id(comp["id"])
                comp_path[comp["id"]] = f"{rid}.{zid}.{cid}"

    # ── Regions ─────────────────────────────────────────────────────────────
    for region in deployment:
        rid    = _d2id(region["id"])
        rtype  = region.get("type", "private_dc")
        rlabel = region.get("location", region.get("id", ""))
        if region.get("owner"):
            rlabel += f" [{region['owner']}]"
        zkey = "network_zones" if rtype == "private_dc" else "subnets"

        # Container shape
        palette = styles.REGION_CONTAINERS.get(rtype, styles.REGION_CONTAINERS["private_dc"])
        fill = palette.get("fill") or "#FAFAFA"
        stroke = palette["stroke"]
        if rtype in ("aws_vpc", "azure_vnet", "gcp_vpc", "aliyun_vpc"):
            container_shape = "cloud"
        else:
            container_shape = "rectangle"

        lines.append(f"{rid}: \"{rlabel}\" {{")
        if palette.get("double") or rtype in ("aws_vpc", "azure_vnet", "gcp_vpc", "aliyun_vpc"):
            lines.append(f"  shape: {container_shape}")
        lines.append(f"  style {{")
        lines.append(f'    fill: "{fill}"')
        lines.append(f'    stroke: "{stroke}"')
        lines.append(f'    stroke-width: 2')
        if palette.get("double"):
            lines.append(f'    double-border: true')
        if palette.get("dashed"):
            lines.append(f'    stroke-dash: 6')
        lines.append(f"  }}")
        lines.append("")

        # Zones / subnets
        for zone in region.get(zkey, []):
            zid    = _d2id(zone["id"])
            ztype  = zone.get("type", "default")
            zlabel = zone.get("name", ztype.replace("_", " ").title())
            zfill  = ZONE_FILL.get(ztype, ZONE_FILL["default"])
            zstroke = ZONE_STROKE.get(ztype, ZONE_STROKE["default"])

            lines.append(f"  {zid}: \"{zlabel}\" {{")
            lines.append(f"    style {{")
            lines.append(f'      fill: "{zfill}"')
            lines.append(f'      stroke: "{zstroke}"')
            lines.append(f"      stroke-dash: 6")
            lines.append(f"    }}")
            lines.append("")

            # Components
            for comp in zone.get("components", []):
                cid    = _d2id(comp["id"])
                clabel = _comp_label(comp)
                cshape = _d2_shape(comp)
                cstyle = _comp_style_block(comp)

                lines.append(f"    {cid}: \"{clabel}\" {{")
                if cshape:
                    lines.append(f"      shape: {cshape}")
                if cstyle:
                    # cstyle already contains style block, strip outer braces
                    inner = cstyle.strip().lstrip("{").rstrip("}").strip()
                    lines.append("      " + inner.replace("\n", "\n      "))
                lines.append(f"    }}")

            lines.append(f"  }}")   # close zone
            lines.append("")

        lines.append(f"}}")   # close region
        lines.append("")

    # ── Edges (interactions) ──────────────────────────────────────────────
    lines.append("# ── Interactions ──────────────────────────────────────")
    lines.append("")
    for i, iact in enumerate(arch.get("interactions", [])):
        src_yaml = iact.get("from", "")
        tgt_yaml = iact.get("to", "")
        src_path = comp_path.get(src_yaml)
        tgt_path = comp_path.get(tgt_yaml)

        if not src_path or not tgt_path:
            raise ValueError(f"Unresolved interaction reference during D2 render: {src_yaml!r} -> {tgt_yaml!r}")

        protocol = labels.clean_protocol(iact.get("protocol", ""))
        label = labels.edge_label(iact).replace("\n", "\\n")

        edge_style = ""
        # Dashed for async/logical
        if any(x in protocol.lower() for x in ("kafka", "amqp", "event")):
            edge_style = " { style { stroke-dash: 4 } }"

        lines.append(f'{src_path} -> {tgt_path}: "{label}"{edge_style}')

    lines.append("")

    # ── Security annotations as notes ───────────────────────────────────
    security = arch.get("security", {})
    if security:
        lines.append("# ── Security declarations ─────────────────────────")
        key_mgmt = security.get("key_management", {})
        for env, tool in key_mgmt.items():
            lines.append(f"# Key Management [{env}]: {tool}")
        auth_int = security.get("user_auth_internal", {})
        if auth_int:
            lines.append(f"# User Auth (Internal): {auth_int.get('server','')} / {auth_int.get('protocol','')}")
        auth_ext = security.get("user_auth_external", {})
        if auth_ext:
            lines.append(f"# User Auth (External): {auth_ext.get('server','')} / {auth_ext.get('protocol','')}")
        lines.append("")

    return "\n".join(lines)
