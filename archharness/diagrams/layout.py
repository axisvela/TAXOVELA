"""
layout.py — Size and position calculations for all draw.io elements.

Layout strategy:
  - Header area: title block
  - Top strip: Internet node (left) + user actor
  - Main grid: regions balanced across two columns by height, auto-sized
  - Each DC: zones stacked, each zone sized from the rows it will actually draw
  - Zone interior: components in rows, centred, respecting the usable width

Sizing and placement are driven by **one** row-splitting pass: the height of a
zone is computed from the rows it will contain at its final width, so a zone can
never be shorter than its content. Component boxes grow with their label
(up to ``MAX_COMP_W``) and get taller when the label wraps, so names are not
truncated.
"""

from . import labels

# ── Spacing constants ─────────────────────────────────────────────────────────

CANVAS_MARGIN   = 50
REGION_GAP      = 70       # gap between region boxes (rows and columns)
REGION_PAD      = 22       # padding inside DC/cloud container
ZONE_GAP        = 18       # gap between zones
ZONE_HEADER     = 32       # zone label height
ZONE_PAD        = 16       # padding inside zone

# Base component sizes (a label may grow the box beyond these)
COMP_W          = 150      # backend service
COMP_H          = 52
DB_W            = 120
DB_H            = 64
GW_W            = 150      # API gateway / integration
GW_H            = 56
HEX_W           = 110      # hexagon (F5 / FW / LB)
HEX_H           = 60

COMP_GAP_H      = 16       # horizontal gap between components
COMP_GAP_V      = 18       # vertical gap between rows

REGION_MIN_W    = 380
REGION_TITLE_H  = 44

# Component sizing
MAX_ROW_W       = 520      # preferred single-row width inside a zone
MAX_COMP_W      = 260      # a label never widens a box beyond this
MAX_GROUP_W     = 340      # logical-group boxes may be a little wider
CHAR_W          = 7.4      # ≈ px per character at fontSize 14
LINE_H          = 15       # ≈ px per label line


def _base_component_size(comp: dict) -> tuple[int, int]:
    t = comp.get("type", "BE")
    s = comp.get("shape", "")
    if t == "DB" or s == "cylinder":
        return DB_W, DB_H
    if t in ("IP", "MQ") or s in ("parallelogram", "message_queue"):
        return GW_W, GW_H
    if t == "LB" or s in ("hexagon", "trapezoid"):
        return HEX_W, HEX_H
    return COMP_W, COMP_H


def _label_text(comp: dict) -> tuple[str, str]:
    name = comp.get("name", comp.get("id", ""))
    tech = labels.tech_line(comp)
    return name, tech


def _component_size(comp: dict) -> tuple[int, int]:
    """Adaptive size: the box grows with its label, up to MAX_COMP_W."""
    if comp.get("is_group"):
        names = comp.get("member_names") or []
        longest = max([len(comp.get("name", ""))] + [len(n) for n in names] + [0])
        width = max(COMP_W, min(int(longest * CHAR_W) + 26, MAX_GROUP_W))
        lines = 2 + len(names)          # header + one line per member + tech line
        return width, max(COMP_H, 14 + LINE_H * lines)

    base_w, base_h = _base_component_size(comp)
    name, tech = _label_text(comp)

    longest = max([len(name)] + [len(line) for line in tech.split("\n")] + [0])
    wanted_w = int(longest * CHAR_W) + 26           # text + inner padding
    w = max(base_w, min(wanted_w, MAX_COMP_W))

    # How many lines will the label need at this width?
    per_line = max(8, int((w - 22) / CHAR_W))
    name_lines = max(1, -(-len(name) // per_line))
    lines = name_lines + (1 if tech else 0)
    h = max(base_h, 14 + LINE_H * lines)
    return w, h


def _split_into_rows(components: list, max_row_w: int) -> list[list]:
    """Split components into rows such that each row fits within max_row_w."""
    rows, row, row_w = [], [], 0
    for comp in components:
        cw, _ = _component_size(comp)
        needed = cw + (COMP_GAP_H if row else 0)
        if row and row_w + needed > max_row_w:
            rows.append(row)
            row, row_w = [comp], cw
        else:
            row.append(comp)
            row_w += needed
    if row:
        rows.append(row)
    return rows


def _row_metrics(row: list) -> tuple[int, int]:
    width = sum(_component_size(c)[0] for c in row) + COMP_GAP_H * (len(row) - 1)
    height = max((_component_size(c)[1] for c in row), default=0)
    return width, height


def _zone_height(components: list, inner_w: int) -> int:
    """Height of a zone at ``inner_w`` — uses the same split as placement."""
    if not components:
        return ZONE_HEADER + ZONE_PAD * 2 + 40
    rows = _split_into_rows(components, inner_w)
    total = ZONE_HEADER + ZONE_PAD
    for row in rows:
        total += _row_metrics(row)[1] + COMP_GAP_V
    return total + ZONE_PAD


def _zone_natural_width(components: list) -> int:
    """Width a zone would like, laying rows out at the preferred max width."""
    if not components:
        return REGION_MIN_W - 2 * REGION_PAD
    rows = _split_into_rows(components, MAX_ROW_W)
    widest = max((_row_metrics(r)[0] for r in rows), default=0)
    return max(widest + ZONE_PAD * 2, REGION_MIN_W - 2 * REGION_PAD)


def _zones_of(region: dict) -> list:
    rtype = region.get("type", "private_dc")
    key = "network_zones" if rtype == "private_dc" else "subnets"
    return region.get(key, []) or []


def _region_natural_width(region: dict) -> int:
    zones = _zones_of(region)
    if not zones:
        return REGION_MIN_W
    widest = max((_zone_natural_width(z.get("components", [])) for z in zones),
                 default=REGION_MIN_W - 2 * REGION_PAD)
    return max(widest + REGION_PAD * 2, REGION_MIN_W)


def _region_height(region: dict, region_w: int) -> int:
    """Height of a region at its final width (single source of truth)."""
    zones = _zones_of(region)
    if not zones:
        return 200
    inner = region_w - 2 * REGION_PAD - 2 * ZONE_PAD
    total = REGION_TITLE_H + REGION_PAD
    for zone in zones:
        total += _zone_height(zone.get("components", []), inner) + ZONE_GAP
    return total + REGION_PAD


def _balance_columns(deployment: list, natural_w: dict, natural_h: dict) -> tuple[list, list]:
    """Greedy two-column packing: next region goes to the shorter column."""
    left, right, left_h, right_h = [], [], 0, 0
    for region in deployment:
        rid = region["id"]
        # Height at the natural width is a good proxy for the packing decision.
        h = natural_h[rid]
        if left_h <= right_h:
            left.append(region)
            left_h += h + REGION_GAP
        else:
            right.append(region)
            right_h += h + REGION_GAP
    return left, right


def calculate_layout(arch: dict) -> dict:
    """
    Compute absolute positions for every region, zone, and component.

    Returns:
      positions:  id → (x, y, w, h)  — component/zone positions are RELATIVE
                  to their parent's top-left; region positions are ABSOLUTE.
      canvas_w, canvas_h
      right_x: x-start of right column
      abs_positions: component_id → (abs_x, abs_y, w, h)  pre-computed absolutes
    """
    positions: dict[str, tuple] = {}
    deployment = arch.get("deployment", [])

    # ── Natural sizes, then balance the two columns ───────────────────────────
    natural_w = {r["id"]: _region_natural_width(r) for r in deployment}
    natural_h = {r["id"]: _region_height(r, natural_w[r["id"]]) for r in deployment}
    left_regions, right_regions = _balance_columns(deployment, natural_w, natural_h)
    left_ids = {r["id"] for r in left_regions}

    left_col_w = max((natural_w[r["id"]] for r in left_regions), default=REGION_MIN_W)
    right_col_w = max((natural_w[r["id"]] for r in right_regions), default=REGION_MIN_W)

    left_x = CANVAS_MARGIN
    right_x = left_x + left_col_w + REGION_GAP
    start_y = 140   # space for header + internet node

    left_y = right_y = start_y
    for region in deployment:
        rid = region["id"]
        rw = left_col_w if rid in left_ids else right_col_w
        rh = _region_height(region, rw)      # recompute at the final width
        origin_x = left_x if rid in left_ids else right_x
        if rid in left_ids:
            positions[rid] = (origin_x, left_y, rw, rh)
            left_y += rh + REGION_GAP
        else:
            positions[rid] = (origin_x, right_y, rw, rh)
            right_y += rh + REGION_GAP

    # ── Place zones and components (same split as the height calculation) ─────
    for region in deployment:
        rid = region["id"]
        rx, ry, rw, rh = positions[rid]
        avail_zone_w = rw - 2 * REGION_PAD
        inner_w = avail_zone_w - ZONE_PAD * 2
        zone_y_off = REGION_TITLE_H + REGION_PAD

        for zone in _zones_of(region):
            zid = zone["id"]
            comps = zone.get("components", [])
            zh = _zone_height(comps, inner_w)

            positions[zid] = (REGION_PAD, zone_y_off, avail_zone_w, zh)
            zone_y_off += zh + ZONE_GAP

            # Components inside the zone, relative to the zone top-left
            rows = _split_into_rows(comps, inner_w)
            cy = ZONE_HEADER + ZONE_PAD

            for row in rows:
                row_w, row_h = _row_metrics(row)
                cx = (avail_zone_w - row_w) // 2      # centre the row

                for comp in row:
                    cw, ch = _component_size(comp)
                    cid = comp["id"]
                    cy_adj = (row_h - ch) // 2        # centre within the row
                    positions[cid] = (cx, cy + cy_adj, cw, ch)
                    cx += cw + COMP_GAP_H

                cy += row_h + COMP_GAP_V

    # ── Pre-compute absolute positions for components ─────────────────────────
    abs_positions: dict[str, tuple] = {}
    for region in deployment:
        rid = region["id"]
        rx, ry, rw, rh = positions[rid]

        for zone in _zones_of(region):
            zid = zone["id"]
            zx_r, zy_r, zw, zh = positions[zid]
            abs_zx = rx + zx_r
            abs_zy = ry + zy_r

            for comp in zone.get("components", []):
                cid = comp["id"]
                if cid not in positions:
                    continue
                cx_r, cy_r, cw, ch = positions[cid]
                abs_positions[cid] = (abs_zx + cx_r, abs_zy + cy_r, cw, ch)

    # Fixed virtual nodes
    abs_positions["internet"]       = (left_x + 10, 60, 70, 44)
    abs_positions["user"]           = (left_x + 110, 52, 40, 56)
    abs_positions["office-network"] = (left_x + 180, 60, 90, 44)

    # ── Canvas size ────────────────────────────────────────────────────────────
    all_x2 = [pos[0] + pos[2] for pos in positions.values() if len(pos) == 4]
    all_y2 = [pos[1] + pos[3] for pos in positions.values() if len(pos) == 4]
    canvas_w = max(all_x2, default=800) + CANVAS_MARGIN * 2
    canvas_h = max(all_y2, default=600) + CANVAS_MARGIN * 2

    # Bottom of the lowest region — legends are placed below this, never on top
    # of the diagram (region positions are absolute; zone/component ones are not).
    region_ids = {r["id"] for r in deployment}
    content_bottom = max(
        (pos[1] + pos[3] for rid, pos in positions.items()
         if rid in region_ids and len(pos) == 4),
        default=600,
    )

    return {
        "positions":      positions,
        "abs_positions":  abs_positions,
        "canvas_w":       canvas_w,
        "canvas_h":       canvas_h,
        "content_bottom": content_bottom,
        "left_x":         left_x,
        "right_x":        right_x,
    }
