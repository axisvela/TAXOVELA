"""
png_renderer.py — High-quality PNG renderer for architecture diagrams.

Key improvements over v1:
  - Dynamic row splitting so AWS Spoke never overflows
  - External (Internet→DC) edges routed to DC top boundary, not component centres
  - Internal edges routed between component nearest edges with readable labels
  - Consistent shape sizes, double-border DC containers
"""

import math
import textwrap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Polygon
import numpy as np

# ── Color palette ─────────────────────────────────────────────────────────────

ZONE_COLORS = {
    "dmz":      {"bg": "#FFF9C4", "border": "#D6B656", "label": "#7A6020"},
    "app_zone": {"bg": "#E8F5E9", "border": "#5A9E5A", "label": "#2E5E2E"},
    "db_zone":  {"bg": "#E3F2FD", "border": "#5A7DBF", "label": "#1A3A6A"},
    "intranet": {"bg": "#EDE7F6", "border": "#8060A0", "label": "#3A1565"},
    "hub":      {"bg": "#FFF8E1", "border": "#E0A020", "label": "#6A4A00"},
    "spoke":    {"bg": "#E8F5E9", "border": "#5A9E5A", "label": "#2E5E2E"},
    "default":  {"bg": "#F5F5F5", "border": "#888888", "label": "#333333"},
}

COMP_COLORS = {
    "LB":      {"bg": "#FFCDD2", "border": "#B71C1C", "text": "#7F0000"},
    "IP":      {"bg": "#E1BEE7", "border": "#6A1B9A", "text": "#380060"},
    "MQ":      {"bg": "#D1C4E9", "border": "#4527A0", "text": "#1A0080"},
    "DB":      {"bg": "#FFF9C4", "border": "#E0A000", "text": "#6A4A00"},
    "BE":      {"bg": "#FAFAFA", "border": "#888888", "text": "#222222"},
    "FE":      {"bg": "#E3F2FD", "border": "#1565C0", "text": "#0D47A1"},
    "SEC":     {"bg": "#DCEDC8", "border": "#33691E", "text": "#1B5E20"},
    "BIZ":     {"bg": "#CE93D8", "border": "#6A1B9A", "text": "#FFFFFF"},
    "3P":      {"bg": "#FFCC80", "border": "#E65100", "text": "#5D2800"},
    "default": {"bg": "#FAFAFA", "border": "#888888", "text": "#222222"},
}

# ── Shape helpers ─────────────────────────────────────────────────────────────

def _hexagon_pts(cx, cy, w, h):
    pts = []
    for i in range(6):
        a = math.radians(60 * i - 30)
        pts.append((cx + (w/2)*math.cos(a), cy + (h/2)*math.sin(a)))
    return pts

def _draw_hexagon(ax, cx, cy, w, h, fc, ec, lw=1.5, z=4):
    poly = Polygon(_hexagon_pts(cx, cy, w, h), closed=True,
                   facecolor=fc, edgecolor=ec, linewidth=lw, zorder=z)
    ax.add_patch(poly)

def _draw_parallelogram(ax, x, y, w, h, fc, ec, lw=1.5, skew=0.13, z=4):
    off = w * skew
    pts = [(x+off, y), (x+w+off, y), (x+w, y+h), (x, y+h)]
    poly = Polygon(pts, closed=True, facecolor=fc, edgecolor=ec, linewidth=lw, zorder=z)
    ax.add_patch(poly)

def _draw_cylinder(ax, x, y, w, h, fc, ec, lw=1.0, z=4):
    ry = max(h * 0.13, 6)
    rect = FancyBboxPatch((x, y+ry), w, h-2*ry,
        boxstyle="square,pad=0", facecolor=fc, edgecolor=ec, linewidth=lw, zorder=z)
    ax.add_patch(rect)
    for cy_e, zo in [(y+ry, z+1), (y+h-ry, z+1)]:
        e = mpatches.Ellipse((x+w/2, cy_e), w, ry*2,
            facecolor=fc, edgecolor=ec, linewidth=lw, zorder=zo)
        ax.add_patch(e)
    # cover the mid seam of bottom ellipse with body color (top half only)
    cover = mpatches.Ellipse((x+w/2, y+h-ry), w, ry*2,
        facecolor=fc, edgecolor='none', linewidth=0, zorder=z+2, clip_on=True)
    ax.add_patch(cover)
    # re-draw the bottom ellipse outline on top
    bot_line = mpatches.Arc((x+w/2, y+h-ry), w, ry*2,
        angle=0, theta1=0, theta2=180, color=ec, linewidth=lw, zorder=z+3)
    ax.add_patch(bot_line)

def _draw_rect(ax, x, y, w, h, fc, ec, lw=1.0, dashed=False, z=3):
    ls = (0, (7, 4)) if dashed else "solid"
    p = FancyBboxPatch((x, y), w, h, boxstyle="square,pad=0",
        facecolor=fc, edgecolor=ec, linewidth=lw, linestyle=ls, zorder=z)
    ax.add_patch(p)

def _comp_colors(comp: dict) -> tuple:
    ctype = comp.get("type", "BE")
    otype = comp.get("owner_type", "")
    if otype == "biz_owned":  return COMP_COLORS["BIZ"]["bg"], COMP_COLORS["BIZ"]["border"], COMP_COLORS["BIZ"]["text"]
    if otype == "third_party": return COMP_COLORS["3P"]["bg"],  COMP_COLORS["3P"]["border"],  COMP_COLORS["3P"]["text"]
    c = COMP_COLORS.get(ctype, COMP_COLORS["default"])
    return c["bg"], c["border"], c["text"]

def _draw_component(ax, comp, ax_, ay, w, h):
    ctype = comp.get("type", "BE")
    shape = comp.get("shape", "")
    fc, ec, tc = _comp_colors(comp)

    if ctype == "LB" or shape == "hexagon":
        _draw_hexagon(ax, ax_+w/2, ay+h/2, w, h, fc, ec)
    elif ctype == "IP" or shape == "parallelogram":
        _draw_parallelogram(ax, ax_, ay, w, h, fc, ec)
    elif ctype == "MQ" or shape == "message_queue":
        _draw_parallelogram(ax, ax_, ay, w, h, fc, ec, skew=0.08)
    elif ctype == "DB" or shape == "cylinder":
        _draw_cylinder(ax, ax_, ay, w, h, fc, ec)
    else:
        _draw_rect(ax, ax_, ay, w, h, fc, ec, lw=1.0, dashed=True, z=4)

    # Label — char width depends on shape
    name = comp.get("name", comp.get("id", ""))
    sens = comp.get("sensitivity", "")
    if "Restricted" in sens or "Confidential" in sens:
        name = "⚠ " + name

    # Estimate usable text width in characters (≈ 7px per char at fontsize 6.5)
    chars = max(8, int(w * 0.9 / 7))
    wrapped = textwrap.fill(name, width=chars, max_lines=2)

    tech = ""
    if comp.get("language"):
        tech = comp["language"]
        if comp.get("framework"):
            short_fw = comp["framework"].split("-")[0]
            tech += f"/{short_fw}"

    label_y = ay + h/2 + (5 if tech else 0)
    ax.text(ax_+w/2, label_y, wrapped, fontsize=6.5, ha="center", va="center",
            color=tc, fontweight="bold", linespacing=1.15, zorder=7,
            clip_on=True)
    if tech:
        ax.text(ax_+w/2, ay+h/2-8, tech, fontsize=5.2, ha="center", va="center",
                color=tc, style="italic", alpha=0.75, zorder=7, clip_on=True)

# ── Edge helpers ──────────────────────────────────────────────────────────────

def _box_edge_point(bx, by, bw, bh, tx, ty):
    """Point on box boundary closest to (tx,ty)."""
    cx, cy = bx+bw/2, by+bh/2
    dx, dy = tx-cx, ty-cy
    if dx == 0 and dy == 0:
        return cx, cy
    sx = (bw/2)/abs(dx) if dx else 1e9
    sy = (bh/2)/abs(dy) if dy else 1e9
    s  = min(sx, sy)
    return cx + dx*s, cy + dy*s

def _draw_edge(ax, sx, sy, sw, sh, tx, ty, tw, th,
               label="", color="#555555", lw=0.75, rad=0.07):
    tcx, tcy = tx+tw/2, ty+th/2
    scx, scy = sx+sw/2, sy+sh/2
    ex0, ey0 = _box_edge_point(sx, sy, sw, sh, tcx, tcy)
    ex1, ey1 = _box_edge_point(tx, ty, tw, th, scx, scy)

    ax.annotate("",
        xy=(ex1, ey1), xytext=(ex0, ey0),
        arrowprops=dict(arrowstyle="-|>", color=color, lw=lw,
                        connectionstyle=f"arc3,rad={rad}"),
        zorder=8)

    if label:
        ang   = math.atan2(ey1-ey0, ex1-ex0)
        mx    = (ex0+ex1)/2 - math.sin(ang)*9
        my    = (ey0+ey1)/2 + math.cos(ang)*9
        ax.text(mx, my, label, fontsize=5.2, ha="center", va="center",
                color="#333333", zorder=9,
                bbox=dict(facecolor="white", alpha=0.88, edgecolor="none",
                          boxstyle="round,pad=0.8", lw=0))

def _draw_ingress_edge(ax, src_pos, dc_top_x, dc_top_y, dc_w,
                       label="", color="#888888"):
    """
    Draw a short stub from Internet/external node to the top centre of a DC,
    instead of drawing a long diagonal to a component inside.
    """
    sx, sy, sw, sh = src_pos
    ex0, ey0 = sx+sw/2, sy+sh
    ex1 = dc_top_x + dc_w/2
    ey1 = dc_top_y

    ax.annotate("",
        xy=(ex1, ey1), xytext=(ex0, ey0),
        arrowprops=dict(arrowstyle="-|>", color=color, lw=0.7,
                        connectionstyle="arc3,rad=0.05"),
        zorder=6)
    if label:
        mx, my = (ex0+ex1)/2, (ey0+ey1)/2 - 6
        ax.text(mx, my, label, fontsize=5, ha="center", va="center",
                color="#555555", zorder=7,
                bbox=dict(facecolor="white", alpha=0.85, edgecolor="none",
                          boxstyle="round,pad=0.7"))

# ── Legend ────────────────────────────────────────────────────────────────────

def _draw_legend(ax, lx, ly, lw, lh=90):
    _draw_rect(ax, lx, ly, lw, lh, "#FAFAFA", "#CCCCCC", lw=0.8, z=1)
    ax.text(lx+8, ly+lh-6, "Legend", fontsize=9, fontweight="bold",
            color="#333333", va="top", zorder=5)

    shapes = [
        ("F5 / LB / Firewall",      "hex",   COMP_COLORS["LB"]),
        ("API Gateway / WSO2",       "para",  COMP_COLORS["IP"]),
        ("Kafka / Event Bus",        "para2", COMP_COLORS["MQ"]),
        ("Database",                 "cyl",   COMP_COLORS["DB"]),
        ("Backend Service (Company)", "rect",  COMP_COLORS["BE"]),
        ("Biz Owned",                "rect",  COMP_COLORS["BIZ"]),
        ("Third-Party",              "rect",  COMP_COLORS["3P"]),
    ]
    col_w = lw / len(shapes)
    for i, (lbl, shape, c) in enumerate(shapes):
        ix = lx + i*col_w + col_w*0.1
        iy = ly + 16
        iw, ih = col_w*0.78, 28
        fc, ec = c["bg"], c["border"]
        if   shape == "hex":   _draw_hexagon(ax, ix+iw/2, iy+ih/2, iw, ih, fc, ec, lw=1.0, z=3)
        elif shape == "para":  _draw_parallelogram(ax, ix, iy, iw, ih, fc, ec, lw=1.0, z=3)
        elif shape == "para2": _draw_parallelogram(ax, ix, iy, iw, ih, fc, ec, lw=1.0, skew=0.08, z=3)
        elif shape == "cyl":   _draw_cylinder(ax, ix, iy, iw, ih, fc, ec, lw=0.8, z=3)
        else:                  _draw_rect(ax, ix, iy, iw, ih, fc, ec, lw=0.8, dashed=True, z=3)
        ax.text(ix+iw/2, iy-3, lbl, fontsize=5.2, ha="center", va="top",
                color="#444444", zorder=5)

    # Zone colors strip
    zones_legend = [
        ("DMZ",       ZONE_COLORS["dmz"]["bg"],      ZONE_COLORS["dmz"]["border"]),
        ("App Zone",  ZONE_COLORS["app_zone"]["bg"],  ZONE_COLORS["app_zone"]["border"]),
        ("DB Zone",   ZONE_COLORS["db_zone"]["bg"],   ZONE_COLORS["db_zone"]["border"]),
        ("Intranet",  ZONE_COLORS["intranet"]["bg"],  ZONE_COLORS["intranet"]["border"]),
        ("Hub/Spoke", ZONE_COLORS["hub"]["bg"],       ZONE_COLORS["hub"]["border"]),
    ]
    strip_col_w = lw / len(zones_legend)
    for i, (zlbl, zbg, zbd) in enumerate(zones_legend):
        zx = lx + i*strip_col_w + strip_col_w*0.1
        zy = ly + 56
        _draw_rect(ax, zx, zy, strip_col_w*0.78, 16, zbg, zbd, lw=0.8, dashed=True, z=3)
        ax.text(zx+strip_col_w*0.39, zy+8, zlbl, fontsize=5.2, ha="center", va="center",
                color=zbd, fontweight="bold", zorder=5)

# ── Main render ───────────────────────────────────────────────────────────────

def render_png(arch: dict, png_path: str, dpi: int = 130):
    from layout import calculate_layout

    layout = calculate_layout(arch)
    positions    = layout["positions"]
    abs_pos      = layout["abs_positions"]
    canvas_w     = layout["canvas_w"]
    canvas_h     = layout["canvas_h"] + 130  # legend

    fig, ax = plt.subplots(figsize=(canvas_w/dpi, canvas_h/dpi))
    ax.set_xlim(0, canvas_w)
    ax.set_ylim(0, canvas_h)
    ax.invert_yaxis()
    ax.axis("off")
    ax.set_aspect("equal")
    fig.patch.set_facecolor("white")

    deployment = arch.get("deployment", [])

    # ── Identify external-ingress interactions ────────────────────────────────
    # target component id → its DC region id
    comp_to_region = {}
    for region in deployment:
        rid   = region["id"]
        rtype = region.get("type", "private_dc")
        zkey  = "network_zones" if rtype == "private_dc" else "subnets"
        for zone in region.get(zkey, []):
            for comp in zone.get("components", []):
                comp_to_region[comp["id"]] = rid

    external_sources = {"internet", "user", "office-network"}
    # group: dc_id → list of (protocol, auth)
    ingress_by_dc: dict[str, list] = {}
    internal_interactions = []
    for iact in arch.get("interactions", []):
        if iact.get("from", "") in external_sources:
            tgt = iact.get("to", "")
            dc  = comp_to_region.get(tgt)
            if dc:
                if dc not in ingress_by_dc:
                    ingress_by_dc[dc] = []
                ingress_by_dc[dc].append(iact.get("protocol", ""))
        else:
            internal_interactions.append(iact)

    # ── Draw regions ──────────────────────────────────────────────────────────
    for region in deployment:
        rid   = region["id"]
        if rid not in positions:
            continue
        rx, ry, rw, rh = positions[rid]
        rtype = region.get("type", "private_dc")
        zkey  = "network_zones" if rtype == "private_dc" else "subnets"

        # Container
        is_aws    = rtype == "aws_vpc"
        is_azure  = rtype == "azure_vnet"
        bg_col    = "#FAFAFA"
        bdr_col   = "#232F3E" if is_aws else ("#0078D4" if is_azure else "#444444")
        bdr_lw    = 1.5 if (is_aws or is_azure) else 2.5

        _draw_rect(ax, rx, ry, rw, rh, bg_col, bdr_col, lw=bdr_lw, z=1)
        if rtype == "private_dc":
            _draw_rect(ax, rx+4, ry+4, rw-8, rh-8, "none", bdr_col, lw=0.6, z=1)

        # Region label
        rlabel = region.get("location", region.get("id", ""))
        if region.get("owner"):
            rlabel += f"  [{region['owner']}]"
        ax.text(rx+10, ry+8, rlabel, fontsize=8, fontweight="bold",
                color=bdr_col, va="top", zorder=5)

        # Zones
        for zone in region.get(zkey, []):
            zid   = zone["id"]
            if zid not in positions:
                continue
            zxr, zyr, zw, zh = positions[zid]
            azx = rx + zxr
            azy = ry + zyr
            zt  = zone.get("type", "default")
            zc  = ZONE_COLORS.get(zt, ZONE_COLORS["default"])

            zp = FancyBboxPatch((azx, azy), zw, zh, boxstyle="square,pad=0",
                facecolor=zc["bg"], edgecolor=zc["border"],
                linewidth=1.2, linestyle=(0, (9, 4)), zorder=2)
            ax.add_patch(zp)
            zp2 = FancyBboxPatch((azx+2, azy+2), zw-4, zh-4, boxstyle="square,pad=0",
                facecolor="none", edgecolor=zc["border"],
                linewidth=0.45, linestyle=(0, (9, 4)), zorder=2)
            ax.add_patch(zp2)
            zlabel = zone.get("name", zt.replace("_"," ").upper())
            ax.text(azx+6, azy+5, zlabel, fontsize=6.5, fontweight="bold",
                    color=zc["label"], va="top", zorder=5)

            # Components
            for comp in zone.get("components", []):
                cid = comp["id"]
                if cid not in abs_pos:
                    continue
                cx, cy, cw, ch = abs_pos[cid]
                _draw_component(ax, comp, cx, cy, cw, ch)

    # ── Internet node ─────────────────────────────────────────────────────────
    inet = abs_pos["internet"]
    ax.text(inet[0]+inet[2]/2, inet[1]+inet[3]/2,
            "Internet", fontsize=8.5, ha="center", va="center",
            fontweight="bold", color="#232F3E",
            bbox=dict(facecolor="#E8E8E8", edgecolor="#555555",
                      boxstyle="round,pad=4", lw=1.5), zorder=6)

    # ── External ingress edges (Internet → DC top) ─────────────────────────────
    inet_pos = abs_pos["internet"]
    for dc_id, protocols in ingress_by_dc.items():
        if dc_id not in positions:
            continue
        dcx, dcy, dcw, dch = positions[dc_id]
        proto_label = protocols[0] if protocols else "HTTPS"
        _draw_ingress_edge(ax, inet_pos, dcx, dcy, dcw,
                           label=proto_label, color="#888888")

    # ── Internal edges ────────────────────────────────────────────────────────
    for iact in internal_interactions:
        src_id = iact.get("from", "")
        tgt_id = iact.get("to", "")
        sp = abs_pos.get(src_id)
        tp = abs_pos.get(tgt_id)
        if not sp or not tp:
            continue
        proto = iact.get("protocol", "")
        auth  = iact.get("auth", "")
        label = proto
        if auth and auth not in ("—", "-", ""):
            label += f"\n({auth})"

        # Use alternate curvature for same-region vs cross-region
        same_dc = comp_to_region.get(src_id) == comp_to_region.get(tgt_id)
        rad = 0.04 if same_dc else 0.12

        _draw_edge(ax, sp[0], sp[1], sp[2], sp[3],
                       tp[0], tp[1], tp[2], tp[3],
                       label=label, rad=rad)

    # ── Legend ────────────────────────────────────────────────────────────────
    leg_y = layout["canvas_h"] + 18
    _draw_legend(ax, CANVAS_MARGIN := 50, leg_y, canvas_w - 100, lh=95)

    # ── Header ────────────────────────────────────────────────────────────────
    name     = arch.get("name", "Architecture Diagram")
    arch_id  = arch.get("id", "")
    platform = arch.get("platform", "")
    ax.text(canvas_w/2, 14,
            f"{name}  |  {arch_id}  |  {platform}",
            fontsize=9.5, ha="center", va="top", color="#222222",
            fontweight="bold", zorder=10)

    plt.tight_layout(pad=0)
    plt.savefig(png_path, dpi=dpi, bbox_inches="tight",
                facecolor="white", format="png")
    plt.close()
    return True
