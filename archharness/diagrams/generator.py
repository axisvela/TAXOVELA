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

from . import labels, styles, topology
from .layout import calculate_layout, REGION_TITLE_H, REGION_PAD, ZONE_GAP


# ── ID helpers ────────────────────────────────────────────────────────────────

def _id(prefix: str = "") -> str:
    """Generate a short unique cell ID."""
    return f"{prefix}{uuid.uuid4().hex[:12]}"


# ── Style selection helpers ───────────────────────────────────────────────────

def _comp_style(comp: dict, status: str = "unchanged") -> str:
    """Shape style plus the lifecycle colour (status is colour, never text)."""
    comp_type = comp.get("type", "BE")
    shape     = comp.get("shape", "")
    owner     = comp.get("owner", "org_it")

    if comp.get("is_group"):
        base = styles.LOGICAL_GROUP
    elif comp_type == "IP" or shape == "parallelogram":
        base = styles.API_GATEWAY
    elif comp_type == "MQ" or shape == "message_queue":
        base = styles.KAFKA_EVENT_BUS
    elif comp_type == "LB" or shape in ("hexagon", "trapezoid"):
        base = styles.LOAD_BALANCER
    elif comp_type == "DB" or shape == "cylinder":
        base = styles.DATABASE_CYLINDER
    elif comp_type in ("auth", "IDP") or shape == "circle":
        base = styles.IDENTITY_AUTH_CIRCLE
    elif shape == "bastion":
        base = styles.BASTION_HOST
    elif owner == "biz_owned" or comp.get("owner_type") == "biz":
        base = styles.BIZ_OWNED
    elif owner == "third_party":
        base = styles.THIRD_PARTY
    else:
        base = styles.COMPANY_APP

    colour = labels.component_fill(comp)
    return (f"{base}fillColor={colour['fill']};strokeColor={colour['stroke']};"
            f"fontColor={colour['text']};")


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
    """Component label: name plus a compact, lower-case technology line.

    A logical group lists its members so the collapsed components stay visible.
    """
    tech = labels.tech_line(comp)
    if comp.get("is_group"):
        # Members are drawn as real nodes inside the frame, so the title is just
        # the group name plus its shared technology.
        head = comp.get("name", "group")
        return f"{head}\n{tech}" if tech else head
    name = labels.component_name(comp)      # lifecycle markers live in the colour
    return f"{name}\n{tech}" if tech else name


# ── Reference integrity ─────────────────────────────────────────────────────

RESERVED_NODES = {"internet", "user", "office-network"}


def _collect_declared_ids(arch: dict) -> tuple[set[str], list[str]]:
    """Collect region/zone/component IDs and report duplicates."""
    seen: set[str] = set()
    declared: set[str] = set()
    duplicates: list[str] = []
    deployment = arch.get("deployment", arch.get("arch", {}).get("deployment", []))

    def _add(node_id: str) -> None:
        if not node_id:
            return
        if node_id in seen:
            if node_id not in duplicates:
                duplicates.append(node_id)
        else:
            seen.add(node_id)
            declared.add(node_id)

    for region in deployment or []:
        _add(region.get("id", ""))
        for zone in topology.region_zones(region):
            _add(zone.get("id", ""))
            for comp in zone.get("components", []) or []:
                _add(comp.get("id", ""))
    return declared, duplicates


def validate_architecture_refs(arch: dict) -> set[str]:
    """Fail closed on duplicate IDs and dangling interaction endpoints."""
    if not isinstance(arch, dict):
        raise ValueError("Architecture input must be a mapping")
    declared, duplicates = _collect_declared_ids(arch)
    if duplicates:
        raise ValueError(f"Duplicate component IDs: {', '.join(sorted(duplicates))}")

    allowed = set(declared) | set(RESERVED_NODES)
    interactions = arch.get("interactions", arch.get("arch", {}).get("interactions", [])) or []
    unresolved: list[str] = []
    for interaction in interactions:
        src = interaction.get("from", "")
        tgt = interaction.get("to", "")
        if src not in allowed or tgt not in allowed:
            unresolved.append(f"{src or '?'} -> {tgt or '?'}")
    if unresolved:
        raise ValueError(f"Unresolved interaction references: {'; '.join(unresolved)}")
    return allowed


# ── Main generation function ──────────────────────────────────────────────────

def generate_drawio(arch: dict) -> str:
    """
    Convert an architecture YAML dict to a draw.io XML string.
    Returns the complete XML suitable for saving as a .drawio file.
    """
    # Fold interchangeable siblings into logical groups before validating and
    # laying out, so the group box — not each member — carries the edges.
    arch, _groups = topology.prepare(arch)
    validate_architecture_refs(arch)
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

    # Private-cloud firewalls are zone boundaries: contract them out of the graph
    # and mark the zone instead of drawing an edge per component.
    boundary_ids = topology.zone_boundary_ids(arch)
    firewall_zones = topology.boundary_zones(arch)

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
        for zone in topology.region_zones(region):
            zid = zone["id"]
            if zid not in positions:
                continue
            zx_rel, zy_rel, zw, zh = positions[zid]

            zone_cell_id = _id(f"zone-")
            cell_map[zid] = zone_cell_id

            zone_label = zone.get("name", zone.get("type", zid).replace("_", " ").upper())
            if zid in firewall_zones:
                zone_label += "  · FW"   # all in/out traffic passes the zone firewall

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
                if cid not in positions or cid in boundary_ids:
                    continue   # zone-boundary firewall: implied, not drawn
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

                # Logical group: its members are real component nodes nested
                # inside the frame (positions are group-relative).
                for member in comp.get("member_specs", []) or []:
                    mid = member.get("id")
                    if mid not in positions:
                        continue
                    mx, my, mw, mh = positions[mid]
                    member_cell_id = _id("comp-")
                    cell_map[mid] = member_cell_id
                    member_label = _comp_label(member)
                    if "Restricted" in member.get("sensitivity", "") or \
                            "Confidential" in member.get("sensitivity", ""):
                        member_label = "⚠ " + member_label
                    member_cell = _make_vertex(root, member_cell_id, member_label,
                        _comp_style(member), mx, my, mw, mh)
                    member_cell.set("parent", comp_cell_id)
                    member_tooltip = _comp_tooltip(member)
                    if member_tooltip:
                        member_cell.set("tooltip", member_tooltip)

    # ── Edges (interactions) ──────────────────────────────────────────────────
    interactions = topology.contract(
        arch.get("interactions", arch.get("arch", {}).get("interactions", [])),
        boundary_ids,
    )

    for i, interaction in enumerate(interactions):
        src_yaml = interaction.get("from", "")
        tgt_yaml = interaction.get("to", "")

        src_cell = cell_map.get(src_yaml)
        tgt_cell = cell_map.get(tgt_yaml)

        if not src_cell or not tgt_cell:
            raise ValueError(f"Unresolved interaction reference during render: {src_yaml!r} -> {tgt_yaml!r}")

        label = labels.edge_label(interaction)
        # Status drives the edge colour: EXISTING blue, NEW/CHANGE red,
        # REMOVE grey, unspecified/TBD blue-grey.
        color = labels.status_color(labels.parse_status(interaction))
        edge_style = f"{styles.EDGE_SOLID}strokeColor={color};fontColor={color};"

        edge_id = _id(f"edge-")
        edge_cell = _make_edge(root, edge_id, label, edge_style,
            src_cell, tgt_cell
        )
        edge_cell.set("parent", "1")

        if interaction.get("notes"):
            edge_cell.set("tooltip", interaction["notes"])

    # ── Legend ────────────────────────────────────────────────────────────────
    # Placed below the lowest region so it can never overlap the diagram.
    legend_y = layout.get("content_bottom", canvas_h - 240) + 30
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

    # ── Code legends ──────────────────────────────────────────────────────────
    # Edges carry only codes (P-… / AU-…); these blocks map them back to methods.
    title_style = (
        "text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;"
        "whiteSpace=wrap;rounded=0;fontFamily=Helvetica;fontSize=12;fontStyle=1;"
    )
    item_style = (
        "text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;"
        "whiteSpace=wrap;rounded=0;fontFamily=Helvetica;fontSize=10;"
    )

    def _legend_block(title: str, lines: list[str], y: int, prefix: str) -> int:
        _make_vertex(root, _id(f"{prefix}title-"), title, title_style, 40, y, 240, 16)
        for idx, line in enumerate(lines):
            _make_vertex(root, _id(prefix), line, item_style,
                         40, y + 22 + idx * 14, 560, 14)
        return y + 22 + 14 * len(lines) + 14

    code_y = legend_y + 212
    protocol_lines = labels.protocol_legend(interactions)
    if protocol_lines:
        code_y = _legend_block("Protocol codes", protocol_lines, code_y, "proto-")
    auth_lines = labels.auth_legend(interactions)
    if auth_lines:
        code_y = _legend_block("Auth codes", auth_lines, code_y, "auth-")

    # Grow the page to cover the legends.
    graph_model.set("pageHeight", str(int(max(canvas_h, code_y + 40))))

    # ── Serialize ─────────────────────────────────────────────────────────────
    raw_xml = ET.tostring(mxfile, encoding="unicode")
    pretty  = minidom.parseString(raw_xml).toprettyxml(indent="  ")
    # Remove the extra <?xml?> declaration added by toprettyxml
    lines = pretty.split("\n")
    if lines[0].startswith("<?xml"):
        lines[0] = '<?xml version="1.0" encoding="UTF-8"?>'
    return "\n".join(lines)
