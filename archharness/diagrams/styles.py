"""
styles.py — draw.io style strings extracted from the official Company template.

Every constant maps directly to a shape observed in _E2E_Template_RoW_drawio.xml
or the Private Cloud Architecture Diagram Shape Specification v1.0.
"""

# ── Container shapes ──────────────────────────────────────────────────────────

DC_CONTAINER = (
    "shape=ext;double=1;rounded=0;whiteSpace=wrap;html=1;"
    "shadow=1;sketch=0;align=left;verticalAlign=top;"
    "fontFamily=Helvetica;fontSize=12;"
)

ZONE_CONTAINER = (
    "shape=ext;double=1;rounded=0;whiteSpace=wrap;html=1;"
    "strokeColor=default;align=center;verticalAlign=top;"
    "fontFamily=Helvetica;fontSize=12;fontColor=default;fillColor=default;dashed=1;"
)

ZONE_PALETTE = {
    "dmz": ("#FFF9C4", "#D6B656"),
    "app_zone": ("#E8F5E9", "#82B366"),
    "db_zone": ("#E3F2FD", "#6C8EBF"),
    "public_subnet": ("#FFEBEE", "#E53935"),
    "private_subnet": ("#E8F5E9", "#82B366"),
}


def zone_container_style(zone_type: str) -> str:
    """Double-dashed zone frame with the standard security-zone palette."""
    fill, stroke = ZONE_PALETTE.get(zone_type, ("#F5F5F5", "#888888"))
    return f"{ZONE_CONTAINER}fillColor={fill};strokeColor={stroke};"

AWS_GROUP = (
    "points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],"
    "[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],"
    "[0,1],[0,0.75],[0,0.5],[0,0.25]];"
    "outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;fontStyle=0;"
    "container=1;pointerEvents=0;collapsible=0;recursiveResize=0;"
    "shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_aws_cloud;"
    "strokeColor=#232F3E;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;"
    "fontColor=#232F3E;dashed=0;"
)

AWS_SUBNET_PRIVATE = (
    "points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],"
    "[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],"
    "[0,1],[0,0.75],[0,0.5],[0,0.25]];"
    "outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;fontStyle=0;"
    "container=1;pointerEvents=0;collapsible=0;recursiveResize=0;"
    "shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_vpc_subnet_private;"
    "strokeColor=#147EBA;fillColor=#E6F2F8;verticalAlign=top;align=left;spacingLeft=30;"
    "fontColor=#147EBA;dashed=0;"
)

AWS_SUBNET_PUBLIC = (
    "points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],"
    "[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],"
    "[0,1],[0,0.75],[0,0.5],[0,0.25]];"
    "outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;fontStyle=0;"
    "container=1;pointerEvents=0;collapsible=0;recursiveResize=0;"
    "shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_vpc_subnet_public;"
    "strokeColor=#F58534;fillColor=#FEF6EE;verticalAlign=top;align=left;spacingLeft=30;"
    "fontColor=#F58534;dashed=0;"
)

# ── Component shapes ──────────────────────────────────────────────────────────
#
# Component labels are the primary reading target, so they use a larger font
# (COMPONENT_FONT) while edges/captions stay smaller (EDGE_FONT).

COMPONENT_FONT = "fontFamily=Helvetica;fontSize=14;"
EDGE_FONT = "fontSize=9;"

COMPANY_APP = (
    "rounded=0;whiteSpace=wrap;html=1;dashed=1;dashPattern=8 8;" + COMPONENT_FONT
)

BACKEND_SERVICE = (
    "rounded=0;whiteSpace=wrap;html=1;" + COMPONENT_FONT
)

WEB_FRONTEND = (
    "rounded=1;whiteSpace=wrap;html=1;" + COMPONENT_FONT
)

API_GATEWAY = (
    "shape=parallelogram;perimeter=parallelogramPerimeter;"
    "whiteSpace=wrap;html=1;fixedSize=1;" + COMPONENT_FONT
)

KAFKA_EVENT_BUS = (
    "shape=parallelogram;html=1;strokeWidth=1;"
    "perimeter=parallelogramPerimeter;whiteSpace=wrap;rounded=1;arcSize=12;size=0.23;"
    + COMPONENT_FONT
)

DATABASE_CYLINDER = (
    "shape=mxgraph.flowchart.database;whiteSpace=wrap;html=1;" + COMPONENT_FONT
)

CACHE_ELLIPSE = (
    "ellipse;whiteSpace=wrap;html=1;" + COMPONENT_FONT
)

IDENTITY_AUTH_CIRCLE = (
    "ellipse;whiteSpace=wrap;html=1;aspect=fixed;"
    "shadow=0;gradientColor=none;fillColor=default;" + COMPONENT_FONT
)

FIREWALL_HEXAGON = (
    "shape=hexagon;perimeter=hexagonPerimeter2;whiteSpace=wrap;html=1;fixedSize=1;"
    + COMPONENT_FONT
)

LOAD_BALANCER = (
    "shape=trapezoid;perimeter=trapezoidPerimeter;whiteSpace=wrap;html=1;fixedSize=1;"
    + COMPONENT_FONT
)

VPN_MPLS = (
    "outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#5A30B5;"
    "strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;"
    "align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;pointerEvents=1;"
    "shape=mxgraph.aws4.vpn_gateway;direction=east;"
)

INTERNET_ICON = (
    "outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#232F3E;"
    "strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;"
    "align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;pointerEvents=1;"
    "shape=mxgraph.aws4.internet;"
)

BASTION_HOST = (
    "aspect=fixed;html=1;points=[];align=center;image;fontSize=12;"
    "image=img/lib/mscae/Bastion.svg;"
)

USER_ACTOR = (
    "shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;"
    "html=1;outlineConnect=0;align=center;fontFamily=Helvetica;fontSize=12;"
)

SAAS_CLOUD = (
    "whiteSpace=wrap;html=1;shape=mxgraph.basic.cloud_rect;dashed=1;dashPattern=8 8;"
)

BIZ_OWNED = (
    "rounded=0;whiteSpace=wrap;html=1;dashed=1;dashPattern=8 8;"
    "fillColor=#8E24AA;strokeColor=#6c8ebf;labelBorderColor=none;fontColor=#FFFFFF;"
)

THIRD_PARTY = (
    "rounded=0;whiteSpace=wrap;html=1;dashed=1;dashPattern=8 8;"
    "fillColor=#FB8C00;strokeColor=#6c8ebf;labelBorderColor=none;fontColor=#FFFFFF;"
)

LOGICAL_GROUP = (
    "rounded=0;whiteSpace=wrap;html=1;dashed=1;dashPattern=4 4;"
    "fillColor=#FAFAFA;strokeColor=#666666;verticalAlign=top;spacingTop=4;"
    + COMPONENT_FONT
)

TECH_PLATFORM_FRAME = (
    "shape=mxgraph.basic.frame;whiteSpace=wrap;html=1;verticalAlign=top;"
)

DATA_LAKE = (
    "verticalLabelPosition=bottom;verticalAlign=top;html=1;"
    "shape=mxgraph.basic.wave2;dy=0.3;"
)

# Explicit ``shape`` values from standards/diagram-style.yaml that have a
# native draw.io equivalent.  The generator consults this catalogue before its
# type-based defaults, so schema authors can choose a standard shape without
# inventing a renderer-specific style string.
STANDARD_SHAPES = {
    "pentagon": "shape=pentagon;whiteSpace=wrap;html=1;" + COMPONENT_FONT,
    "card": "shape=card;whiteSpace=wrap;html=1;" + COMPONENT_FONT,
    "stored_data": "shape=mxgraph.flowchart.stored_data;whiteSpace=wrap;html=1;" + COMPONENT_FONT,
    "double_ellipse": "shape=doubleEllipse;whiteSpace=wrap;html=1;" + COMPONENT_FONT,
    "diamond": "shape=rhombus;whiteSpace=wrap;html=1;" + COMPONENT_FONT,
    "document": "shape=document;whiteSpace=wrap;html=1;" + COMPONENT_FONT,
    "note": "shape=note;whiteSpace=wrap;html=1;" + COMPONENT_FONT,
    "step": "shape=mxgraph.flowchart.step;whiteSpace=wrap;html=1;" + COMPONENT_FONT,
    "pyramid": "shape=mxgraph.basic.pyramid;whiteSpace=wrap;html=1;" + COMPONENT_FONT,
    "cube": "shape=cube;whiteSpace=wrap;html=1;" + COMPONENT_FONT,
    "cloud": "shape=cloud;whiteSpace=wrap;html=1;" + COMPONENT_FONT,
}

# ── Region containers ─────────────────────────────────────────────────────────
#
# One palette for every hosting kind, so a new platform is a data change rather
# than a new branch in four renderers. ``double`` marks the private-cloud
# double border; ``dashed`` marks logical (SaaS/office) boundaries.

REGION_CONTAINERS = {
    "private_dc":  {"stroke": "#444444", "fill": "#FAFAFA", "double": True},
    "plant":       {"stroke": "#444444", "fill": "#FAFAFA", "double": True},
    "aws_vpc":     {"stroke": "#232F3E", "fill": "#FAFAFA"},
    "azure_vnet":  {"stroke": "#0078D4", "fill": "#FAFAFA"},
    "gcp_vpc":     {"stroke": "#1A73E8", "fill": "#FAFAFA"},
    "aliyun_vpc":  {"stroke": "#FF6A00", "fill": "#FAFAFA"},
    "m365_tenant": {"stroke": "#D83B01", "fill": "#FFF7F2", "dashed": True},
    "power_platform": {"stroke": "#742774", "fill": "#FAF5FA", "dashed": True},
    "dynamics365": {"stroke": "#002050", "fill": "#F2F5FA", "dashed": True},
    "saas_tenant": {"stroke": "#5C6BC0", "fill": "#F3F6FF", "dashed": True},
    "office_network": {"stroke": "#666666", "fill": "none", "dashed": True},
    "factory_network": {"stroke": "#666666", "fill": "none", "dashed": True},
    "lab_network": {"stroke": "#666666", "fill": "none", "dashed": True},
    "third_party": {"stroke": "#B85450", "fill": "none", "dashed": True},
}


def region_container_style(region_type: str) -> str:
    """Container style for a hosting kind (an unknown kind is a plain DC box)."""
    palette = REGION_CONTAINERS.get(region_type, REGION_CONTAINERS["private_dc"])
    style = f"{DC_CONTAINER}strokeColor={palette['stroke']};"
    if palette.get("fill") and palette["fill"] != "none":
        style = f"fillColor={palette['fill']};" + style
    if palette.get("dashed"):
        style += "dashed=1;"
    return style


# ── Edge styles ───────────────────────────────────────────────────────────────

EDGE_SOLID = (
    "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;"
    "jettySize=auto;html=1;jumpStyle=arc;jumpSize=10;" + EDGE_FONT
)

EDGE_DASHED = (
    "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;"
    "jettySize=auto;html=1;dashed=1;dashPattern=8 8;" + EDGE_FONT
)

# ── Status fill colors ────────────────────────────────────────────────────────

STATUS_COLORS = {
    "newly_created": {"fill": "#D32F2F", "stroke": "#d6b656", "font": "#FFFFFF"},
    "changed":       {"fill": "#FBC02D", "stroke": "#d6b656", "font": "#000000"},
    "unchanged":     {"fill": "#FFFFFF", "stroke": "#000000", "font": "#000000"},
    "in_plan":       {"fill": "#66BB6A", "stroke": "#d6b656", "font": "#000000"},
    "retired":       {"fill": "#757575", "stroke": "#d6b656", "font": "#FFFFFF"},
    "biz_owned":     {"fill": "#8E24AA", "stroke": "#b85450", "font": "#FFFFFF"},
    "third_party":   {"fill": "#FB8C00", "stroke": "#b85450", "font": "#000000"},
}
