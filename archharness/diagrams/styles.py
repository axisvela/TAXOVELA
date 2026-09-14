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

COMPANY_APP = (
    "rounded=0;whiteSpace=wrap;html=1;dashed=1;dashPattern=8 8;"
)

BACKEND_SERVICE = (
    "rounded=0;whiteSpace=wrap;html=1;"
)

WEB_FRONTEND = (
    "rounded=1;whiteSpace=wrap;html=1;"
)

API_GATEWAY = (
    "shape=parallelogram;perimeter=parallelogramPerimeter;"
    "whiteSpace=wrap;html=1;fixedSize=1;"
)

KAFKA_EVENT_BUS = (
    "shape=parallelogram;html=1;strokeWidth=1;"
    "perimeter=parallelogramPerimeter;whiteSpace=wrap;rounded=1;arcSize=12;size=0.23;"
)

DATABASE_CYLINDER = (
    "shape=mxgraph.flowchart.database;whiteSpace=wrap;html=1;"
)

CACHE_ELLIPSE = (
    "ellipse;whiteSpace=wrap;html=1;"
)

IDENTITY_AUTH_CIRCLE = (
    "ellipse;whiteSpace=wrap;html=1;aspect=fixed;"
    "shadow=0;gradientColor=none;fillColor=default;"
)

FIREWALL_HEXAGON = (
    "shape=hexagon;perimeter=hexagonPerimeter2;whiteSpace=wrap;html=1;fixedSize=1;"
)

LOAD_BALANCER = (
    "shape=hexagon;perimeter=hexagonPerimeter2;whiteSpace=wrap;html=1;fixedSize=1;"
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

TECH_PLATFORM_FRAME = (
    "shape=mxgraph.basic.frame;whiteSpace=wrap;html=1;verticalAlign=top;"
)

DATA_LAKE = (
    "verticalLabelPosition=bottom;verticalAlign=top;html=1;"
    "shape=mxgraph.basic.wave2;dy=0.3;"
)

# ── Edge styles ───────────────────────────────────────────────────────────────

EDGE_SOLID = (
    "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;"
    "jettySize=auto;html=1;jumpStyle=arc;jumpSize=10;"
)

EDGE_DASHED = (
    "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;"
    "jettySize=auto;html=1;dashed=1;dashPattern=8 8;"
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
