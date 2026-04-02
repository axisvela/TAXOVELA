"""
plantuml_generator.py  — Architecture YAML → PlantUML Deployment Diagram (.puml)

PlantUML Deployment Diagram supports unlimited nested `node` blocks, making it
the best PlantUML diagram type for DC → Zone → App → Component hierarchies.

Rendering options:
    1. plantuml -tsvg output.puml          # local CLI
    2. https://www.plantuml.com/plantuml/  # online server
    3. Confluence PlantUML macro           # native Confluence support
    4. draw.io import: File → Import → PlantUML (via built-in conversion)

Shape keywords used:
    node         — DC, Zone, VPC/VNET containers (physical boundary)
    component    — Backend services, APIs (logical component)
    database     — Databases, caches, storage
    queue        — Kafka, message queues
    [<<frame>>]  — Technology platforms (Internal K8s, K8s cluster)
    agent        — API Gateways (parallelogram-like in PlantUML)
    card         — Integration platforms
    cloud        — Internet, SaaS nodes
    actor        — User / external entity
    hexagon      — Firewall, F5, load balancer
    storage      — File/object storage
    rectangle    — Generic component override

Skinparam colors match diagram-style.yaml:
    DMZ           #FFF9C4 / #D6B656
    App Zone      #E8F5E9 / #82B366
    DB Zone       #E3F2FD / #6C8EBF
    Intranet      #EDE7F6 / #9673A6
    Hub           #FFF8E1 / #F9A825
    Spoke         #E8F5E9 / #82B366
"""

import re


# ── Zone color mapping ────────────────────────────────────────────────────────

ZONE_COLORS = {
    "dmz":      ("#FFF9C4", "#D6B656"),
    "app_zone": ("#E8F5E9", "#82B366"),
    "db_zone":  ("#E3F2FD", "#6C8EBF"),
    "intranet": ("#EDE7F6", "#9673A6"),
    "hub":      ("#FFF8E1", "#F9A825"),
    "spoke":    ("#E8F5E9", "#4CAF50"),
    "default":  ("#F5F5F5", "#9E9E9E"),
}

REGION_COLORS = {
    "private_dc":  ("#FAFAFA", "#444444"),
    "aws_vpc":     ("#FAFAFA", "#232F3E"),
    "azure_vnet":  ("#FAFAFA", "#0078D4"),
    "saas":        ("#F5F5F5", "#888888"),
    "default":     ("#FAFAFA", "#666666"),
}

STATUS_COLORS = {
    "newly_created": "#D32F2F",
    "changed":       "#FBC02D",
    "in_plan":       "#66BB6A",
    "retired":       "#9E9E9E",
    "biz_owned":     "#8E24AA",
    "third_party":   "#FB8C00",
}

COMP_BG = {
    "LB":  "#FFCDD2",
    "IP":  "#E1BEE7",
    "MQ":  "#D1C4E9",
    "DB":  "#FFF9C4",
    "SEC": "#DCEDC8",
    "FE":  "#E3F2FD",
}


# ── ID helpers ────────────────────────────────────────────────────────────────

def _pid(raw: str) -> str:
    """Sanitise a YAML id for use as a PlantUML alias."""
    s = re.sub(r"[^a-zA-Z0-9_]", "_", raw)
    return s if not s[0].isdigit() else "_" + s


# ── Shape selector ────────────────────────────────────────────────────────────

def _pu_shape(comp: dict) -> str:
    """Return the PlantUML keyword for a component."""
    ctype = comp.get("type", "BE")
    shape = comp.get("shape", "")
    if ctype == "LB" or shape in ("hexagon", "trapezoid"):
        return "hexagon"
    if ctype == "IP" or shape == "parallelogram":
        return "agent"        # closest to parallelogram in PlantUML
    if ctype == "MQ" or shape == "message_queue":
        return "queue"
    if ctype == "DB" or shape == "cylinder":
        return "database"
    if ctype == "DS":
        return "storage"
    if ctype == "SEC" or shape == "circle":
        return "card"
    if ctype == "FE":
        return "rectangle"
    if shape == "bastion":
        return "rectangle"
    return "component"   # default: BE services


def _comp_stereotype(comp: dict) -> str:
    """Build a PlantUML <<stereotype>> annotation from component metadata."""
    parts = []
    if comp.get("runtime"):
        parts.append(comp["runtime"])
    return f" <<{', '.join(parts)}>>" if parts else ""


def _comp_label(comp: dict) -> str:
    """Build the label shown inside the component box."""
    name = comp.get("name", comp.get("id", ""))
    sens = comp.get("sensitivity", "")
    if "Restricted" in sens or "Confidential" in sens:
        name = "⚠ " + name
    lines = [name]
    tech = []
    if comp.get("language"):
        tech.append(comp["language"])
    if comp.get("framework"):
        short = comp["framework"].split("-")[0]
        tech.append(short)
    if tech:
        lines.append(f"({', '.join(tech)})")
    return "\\n".join(lines)


def _comp_color(comp: dict) -> str:
    """Return a PlantUML #RRGGBB color for the component background."""
    status = comp.get("status", "unchanged")
    owner  = comp.get("owner_type", "")
    ctype  = comp.get("type", "BE")
    if owner == "biz_owned":    return "#8E24AA"
    if owner == "third_party":  return "#FB8C00"
    if status in STATUS_COLORS: return STATUS_COLORS[status]
    return COMP_BG.get(ctype, "#FFFFFF")


# ── Generator ─────────────────────────────────────────────────────────────────

def generate_plantuml(arch: dict) -> str:
    """
    Convert an architecture dict to a PlantUML Deployment Diagram string.
    """
    lines = []

    arch_name = arch.get("name", "Architecture")
    arch_id   = arch.get("id", "")

    # ── Preamble ──────────────────────────────────────────────────────────
    lines.append("@startuml")
    lines.append(f"' {arch_name}")
    lines.append(f"' ID: {arch_id}")
    lines.append("")
    lines.append("!theme plain")
    lines.append("skinparam backgroundColor #FFFFFF")
    lines.append("skinparam defaultFontName Helvetica")
    lines.append("skinparam defaultFontSize 11")
    lines.append("skinparam nodeRoundCorner 8")
    lines.append("skinparam nodeBorderThickness 1.5")
    lines.append("skinparam componentRoundCorner 6")
    lines.append("skinparam componentBorderThickness 1")
    lines.append("skinparam arrowThickness 1")
    lines.append("skinparam arrowColor #555555")
    lines.append("skinparam arrowFontSize 9")
    lines.append("skinparam arrowFontColor #333333")
    lines.append("skinparam databaseBackgroundColor #FFF9C4")
    lines.append("skinparam databaseBorderColor #F9A825")
    lines.append("skinparam queueBackgroundColor #D1C4E9")
    lines.append("skinparam queueBorderColor #4527A0")
    lines.append("skinparam hexagonBackgroundColor #FFCDD2")
    lines.append("skinparam hexagonBorderColor #B71C1C")
    lines.append("")

    # ── Build component → alias map ──────────────────────────────────────
    alias_map: dict[str, str] = {}
    alias_map["internet"]       = "INTERNET"
    alias_map["user"]           = "USER"
    alias_map["office-network"] = "OFFICE_NET"

    deployment = arch.get("deployment", [])
    for region in deployment:
        rtype = region.get("type", "private_dc")
        zkey  = "network_zones" if rtype == "private_dc" else "subnets"
        for zone in region.get(zkey, []):
            for comp in zone.get("components", []):
                alias_map[comp["id"]] = _pid(comp["id"]).upper()

    # ── Virtual external nodes ───────────────────────────────────────────
    lines.append("actor User as USER")
    lines.append("cloud Internet as INTERNET {")
    lines.append("}")
    lines.append("")

    # ── Regions ──────────────────────────────────────────────────────────
    for region in deployment:
        rid    = _pid(region["id"])
        rtype  = region.get("type", "private_dc")
        rlabel = region.get("location", region.get("id", ""))
        if region.get("owner"):
            rlabel += f"\\n[{region['owner']}]"
        zkey   = "network_zones" if rtype == "private_dc" else "subnets"
        rbg, rbd = REGION_COLORS.get(rtype, REGION_COLORS["default"])

        # node keyword is used for all physical containers
        lines.append(f'node "{rlabel}" as {rid} #{rbg[1:]} [{rbd[1:]}] {{')

        for zone in region.get(zkey, []):
            zid    = _pid(zone["id"])
            ztype  = zone.get("type", "default")
            zlabel = zone.get("name", ztype.replace("_", " ").title())
            zbg, zbd = ZONE_COLORS.get(ztype, ZONE_COLORS["default"])

            # Inner zones as node with dashed border
            lines.append(f'  node "{zlabel}" as {zid} #{zbg[1:]} [{zbd[1:]}] {{')

            for comp in zone.get("components", []):
                alias  = alias_map[comp["id"]]
                clabel = _comp_label(comp)
                cshape = _pu_shape(comp)
                ccolor = _comp_color(comp)
                stereo = _comp_stereotype(comp)
                cbg    = ccolor.lstrip("#")

                lines.append(f'    {cshape} "{clabel}"{stereo} as {alias} #{cbg}')

            lines.append("  }")   # close zone
            lines.append("")

        lines.append("}")   # close region
        lines.append("")

    # ── Edges ─────────────────────────────────────────────────────────────
    lines.append("' ── Interactions ────────────────────────────────────")
    lines.append("")
    for iact in arch.get("interactions", []):
        src_yaml = iact.get("from", "")
        tgt_yaml = iact.get("to", "")
        src = alias_map.get(src_yaml)
        tgt = alias_map.get(tgt_yaml)
        if not src or not tgt:
            lines.append(f"' UNRESOLVED: {src_yaml} -> {tgt_yaml}")
            continue

        protocol = iact.get("protocol", "")
        auth     = iact.get("auth", "")
        label    = protocol
        if auth and auth not in ("—", "-", ""):
            label += f"\\n({auth})"

        # Dashed arrow for async
        arrow = "..>" if any(x in protocol.lower() for x in ("kafka", "amqp", "event")) else "-->"
        lines.append(f'{src} {arrow} {tgt} : "{label}"')

    lines.append("")

    # ── Security notes ────────────────────────────────────────────────────
    security = arch.get("security", {})
    if security:
        lines.append("' ── Security ─────────────────────────────────────────")
        note_lines = []
        km = security.get("key_management", {})
        for env, tool in km.items():
            note_lines.append(f"Key Mgmt [{env}]: {tool}")
        ia = security.get("user_auth_internal", {})
        if ia:
            note_lines.append(f"User Auth (internal): {ia.get('server', '')} / {ia.get('protocol', '')}")
        ea = security.get("user_auth_external", {})
        if ea:
            note_lines.append(f"User Auth (external): {ea.get('server', '')} / {ea.get('protocol', '')}")

        if note_lines:
            lines.append('note as SECURITY_NOTE')
            for nl in note_lines:
                lines.append(f"  {nl}")
            lines.append('end note')
        lines.append("")

    lines.append("@enduml")
    return "\n".join(lines)
