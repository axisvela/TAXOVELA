"""
generator.py — Converts Architecture YAML → draw.io XML (.drawio).

Usage:
    from generator import generate_drawio
    xml_str = generate_drawio(arch_dict)

Or from command line via arch_diagram_gen.py.
"""

import uuid
import xml.etree.ElementTree as ET
from xml.dom import minidom

import styles
from layout import calculate_layout, REGION_TITLE_H, REGION_PAD, ZONE_GAP


# ── ID helpers ────────────────────────────────────────────────────────────────

def _id(prefix: str = "") -> str:
    """Generate a short unique cell ID."""
    return f"{prefix}{uuid.uuid4().hex[:12]}"


# ── Style selection helpers ───────────────────────────────────────────────────

def _comp_style(comp: dict, status: str = "unchanged") -> str:
    comp_type = comp.get("type", "BE")
    shape     = comp.get("shape", "")
    owner     = comp.get("owner", "org_it")

    # Integration / gateways
    if comp_type == "IP" or shape == "parallelogram":
        return styles.API_GATEWAY
    if comp_type == "MQ" or shape == "message_queue":
        return styles.KAFKA_EVENT_BUS
    if comp_type == "LB" or shape in ("hexagon", "trapezoid"):
        return styles.LOAD_BALANCER
    if comp_type == "DB" or shape == "cylinder":
        return styles.DATABASE_CYLINDER
    if comp_type in ("auth", "IDP") or shape == "circle":
        return styles.IDENTITY_AUTH_CIRCLE
    if shape == "bastion":
        return styles.BASTION_HOST

    # Application type by owner/status
    if owner == "biz_owned" or comp.get("owner_type") == "biz":
        return styles.BIZ_OWNED
    if owner == "third_party":
        return styles.THIRD_PARTY

    # Default: Company internal app (dashed border)
    return styles.COMPANY_APP


def _region_container_style(region: dict) -> str:
    rtype = region.get("type", "private_dc")
    if rtype == "aws_vpc":
        return styles.AWS_GROUP
    if rtype == "azure_vnet":
        # Use a styled container for Azure
        return (
            "points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],"
            "[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],"
            "[0,1],[0,0.75],[0,0.5],[0,0.25]];"
            "outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;"
            "container=1;pointerEvents=0;collapsible=0;recursiveResize=0;"
            "shape=mxgraph.azure.azure;fillColor=none;strokeColor=#0078D4;"
            "verticalAlign=top;align=left;spacingLeft=30;fontColor=#0078D4;dashed=0;"
        )
    # Private DC
    return styles.DC_CONTAINER


def _subnet_style(subnet: dict) -> str:
    stype = subnet.get("type", "private")
    if stype == "hub":
        return styles.AWS_GROUP
    if "public" in stype:
        return styles.AWS_SUBNET_PUBLIC
    return styles.AWS_SUBNET_PRIVATE


# ── Cell builders ─────────────────────────────────────────────────────────────

def _make_vertex(parent_el, cell_id, value, style, x, y, w, h, parent_id="1"):
    cell = ET.SubElement(parent_el, "mxCell",
        id=cell_id, value=value, style=style,
        parent=parent_id, vertex="1"
    )
    ET.SubElement(cell, "mxGeometry", x=str(x), y=str(y), width=str(w), height=str(h), **{"as": "geometry"})
    return cell


def _make_edge(parent_el, edge_id, label, style, source_id, target_id, parent_id="1"):
    cell = ET.SubElement(parent_el, "mxCell",
        id=edge_id, value=label, style=style,
        parent=parent_id, source=source_id, target=target_id,
        edge="1"
    )
    ET.SubElement(cell, "mxGeometry", relative="1", **{"as": "geometry"})
    return cell


# ── Tooltip / metadata builder ────────────────────────────────────────────────

def _comp_tooltip(comp: dict) -> str:
    """Build an HTML tooltip with component metadata."""
    parts = []
    if comp.get("language"):
        parts.append(f"Lang: {comp['language']}")
    if comp.get("framework"):
        parts.append(f"Framework: {comp['framework']}")
    if comp.get("runtime"):
        parts.append(f"Runtime: {comp['runtime']}")
    if comp.get("sensitivity"):
        parts.append(f"Classification: {comp['sensitivity']}")
    if comp.get("notes"):
        parts.append(f"Notes: {comp['notes']}")
    return " | ".join(parts) if parts else ""


def _comp_label(comp: dict) -> str:
    """Build the component label. Includes tech stack in parentheses if present."""
    name = comp.get("name", comp.get("id", ""))
    tech_parts = []
    if comp.get("language"):
        tech_parts.append(comp["language"])
    if comp.get("framework"):
        tech_parts.append(comp["framework"])
    if tech_parts:
        name += f"\n({', '.join(tech_parts)})"
    return name


# ── Main generation function ──────────────────────────────────────────────────

def generate_drawio(arch: dict) -> str:
    """
    Convert an architecture YAML dict to a draw.io XML string.
    Returns the complete XML suitable for saving as a .drawio file.
    """
    layout = calculate_layout(arch)
    positions = layout["positions"]
    canvas_w  = layout["canvas_w"]
    canvas_h  = layout["canvas_h"]

    # ── XML skeleton ─────────────────────────────────────────────────────────
    mxfile = ET.Element("mxfile",
        host="arch-harness",
        version="24.6.4",
        type="device"
    )
    diagram = ET.SubElement(mxfile, "diagram",
        id=_id("diag-"),
        name="Page-1"
    )
    graph_model = ET.SubElement(diagram, "mxGraphModel",
        dx="2000", dy="1000",
        grid="1", gridSize="10", guides="1",
        tooltips="1", connect="1", arrows="1", fold="1",
        page="0", pageScale="1",
        pageWidth=str(canvas_w), pageHeight=str(canvas_h),
        math="0", shadow="0"
    )
    root = ET.SubElement(graph_model, "root")
    ET.SubElement(root, "mxCell", id="0")
    ET.SubElement(root, "mxCell", id="1", parent="0")

    # Track all component cell_ids for edge routing: yaml_id → cell_id
    cell_map: dict[str, str] = {}

    # ── Header metadata block ─────────────────────────────────────────────────
    meta = arch.get("arch", arch)
    arch_id   = meta.get("id", "")
    arch_name = meta.get("name", "Architecture")
    header_html = (
        f"<b>Diagram: {arch_name}</b><br/>"
        f"ID: {arch_id}<br/>"
        f"Platform: {meta.get('platform', '')}"
    )
    header_id = _id("hdr-")
    _make_vertex(root, header_id, header_html,
        "text;whiteSpace=wrap;overflow=hidden;rounded=0;"
        "fontFamily=Helvetica;fontSize=11;fillColor=#f5f5f5;strokeColor=#666666;",
        40, -120, 600, 80
    )

    # ── Internet node ─────────────────────────────────────────────────────────
    internet_id = _id("inet-")
    cell_map["internet"] = internet_id
    _make_vertex(root, internet_id, "Internet",
        styles.INTERNET_ICON,
        40, 80, 60, 40
    )

    # ── User actor ────────────────────────────────────────────────────────────
    user_id = _id("user-")
    cell_map["user"] = user_id
    _make_vertex(root, user_id, "User",
        styles.USER_ACTOR,
        160, 70, 37, 50
    )

    # ── Regions ───────────────────────────────────────────────────────────────
    deployment = arch.get("deployment", arch.get("arch", {}).get("deployment", []))

    for region in deployment:
        rid = region["id"]
        if rid not in positions:
            continue
        rx, ry, rw, rh = positions[rid]
        rtype = region.get("type", "private_dc")

        # Region container
        region_cell_id = _id(f"reg-")
        cell_map[rid] = region_cell_id
        region_label = region.get("location", region.get("name", rid))
        if region.get("owner"):
            region_label += f"\n({region['owner']})"

        region_style = _region_container_style(region)
        region_cell = _make_vertex(root, region_cell_id, region_label,
            region_style, rx, ry, rw, rh
        )
        region_cell.set("parent", "1")

        # Zones / subnets inside region
        zones_key = "network_zones" if rtype == "private_dc" else "subnets"
        for zone in region.get(zones_key, []):
            zid = zone["id"]
            if zid not in positions:
                continue
            zx_rel, zy_rel, zw, zh = positions[zid]

            zone_cell_id = _id(f"zone-")
            cell_map[zid] = zone_cell_id

            zone_label = zone.get("name", zone.get("type", zid).replace("_", " ").upper())

            if rtype == "private_dc":
                zone_style = styles.ZONE_CONTAINER
            else:
                zone_style = _subnet_style(zone)

            zone_cell = _make_vertex(root, zone_cell_id, zone_label,
                zone_style, zx_rel, zy_rel, zw, zh
            )
            zone_cell.set("parent", region_cell_id)

            # Components inside zone
            for comp in zone.get("components", []):
                cid = comp["id"]
                if cid not in positions:
                    continue
                cx_rel, cy_rel, cw, ch = positions[cid]

                comp_cell_id = _id(f"comp-")
                cell_map[cid] = comp_cell_id

                comp_label = _comp_label(comp)
                comp_tooltip = _comp_tooltip(comp)
                comp_style = _comp_style(comp)

                # Add sensitivity marker to label if restricted
                sensitivity = comp.get("sensitivity", "")
                if "Restricted" in sensitivity or "Confidential" in sensitivity:
                    comp_label = "⚠ " + comp_label

                comp_cell = _make_vertex(root, comp_cell_id, comp_label,
                    comp_style, cx_rel, cy_rel, cw, ch
                )
                comp_cell.set("parent", zone_cell_id)
                if comp_tooltip:
                    comp_cell.set("tooltip", comp_tooltip)

    # ── Edges (interactions) ──────────────────────────────────────────────────
    interactions = arch.get("interactions", arch.get("arch", {}).get("interactions", []))

    for i, interaction in enumerate(interactions):
        src_yaml = interaction.get("from", "")
        tgt_yaml = interaction.get("to", "")

        src_cell = cell_map.get(src_yaml)
        tgt_cell = cell_map.get(tgt_yaml)

        if not src_cell or not tgt_cell:
            # Skip unresolved references silently
            continue

        protocol = interaction.get("protocol", "")
        auth     = interaction.get("auth", "")
        label    = protocol
        if auth and auth != "—":
            label += f"\n({auth})"

        edge_id = _id(f"edge-")
        edge_cell = _make_edge(root, edge_id, label, styles.EDGE_SOLID,
            src_cell, tgt_cell
        )
        edge_cell.set("parent", "1")

        if interaction.get("notes"):
            edge_cell.set("tooltip", interaction["notes"])

    # ── VPN/MPLS connections between DCs ─────────────────────────────────────
    # Add VPN icons between private DC pairs
    dc_ids = [r["id"] for r in deployment if r.get("type") == "private_dc"]
    for i in range(len(dc_ids) - 1):
        vpn_id = _id("vpn-")
        _make_vertex(root, vpn_id, "MPLS",
            styles.VPN_MPLS,
            layout["right_x"] - 40, 100 + i * 40, 28, 28
        )

    # ── Legend ────────────────────────────────────────────────────────────────
    legend_y = canvas_h - 240
    legend_id = _id("lgnd-")
    legend_group = ET.SubElement(root, "mxCell",
        id=legend_id, value="", style="group",
        parent="1", vertex="1", connectable="0"
    )
    ET.SubElement(legend_group, "mxGeometry",
        x="40", y=str(legend_y), width="640", height="200",
        **{"as": "geometry"}
    )

    legend_title_id = _id("ltitle-")
    _make_vertex(root, legend_title_id, "Legend",
        "text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;"
        "whiteSpace=wrap;rounded=0;fontFamily=Helvetica;fontSize=14;fontStyle=1;",
        0, -30, 100, 30, parent_id=legend_id
    )

    legend_items = [
        ("Internal App (IT Org)", styles.COMPANY_APP),
        ("API Gateway / Integration", styles.API_GATEWAY),
        ("Database", styles.DATABASE_CYLINDER),
        ("Firewall / LB",  styles.FIREWALL_HEXAGON),
        ("Identity / Auth", styles.IDENTITY_AUTH_CIRCLE),
        ("Biz Owned", styles.BIZ_OWNED),
        ("Third Party", styles.THIRD_PARTY),
    ]
    for idx, (label, style) in enumerate(legend_items):
        lx = (idx % 4) * 155
        ly = (idx // 4) * 56
        _make_vertex(root, _id("li-"), label, style, lx, ly, 140, 40, parent_id=legend_id)

    # ── Serialize ─────────────────────────────────────────────────────────────
    raw_xml = ET.tostring(mxfile, encoding="unicode")
    pretty  = minidom.parseString(raw_xml).toprettyxml(indent="  ")
    # Remove the extra <?xml?> declaration added by toprettyxml
    lines = pretty.split("\n")
    if lines[0].startswith("<?xml"):
        lines[0] = '<?xml version="1.0" encoding="UTF-8"?>'
    return "\n".join(lines)
