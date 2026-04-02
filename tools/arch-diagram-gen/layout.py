"""
layout.py — Size and position calculations for all draw.io elements.

Layout strategy:
  - Header area: title block
  - Top strip: Internet node (left) + user actor
  - Main grid: regions in 2 columns, auto-sized
  - Each DC: zones stacked, each zone auto-sized from its components
  - Zone interior: components in rows, centred, respecting max row width
"""

# ── Spacing constants ─────────────────────────────────────────────────────────

CANVAS_MARGIN   = 50
REGION_GAP      = 70       # gap between columns
REGION_PAD      = 22       # padding inside DC/cloud container
ZONE_GAP        = 18       # gap between zones
ZONE_HEADER     = 32       # zone label height
ZONE_PAD        = 16       # padding inside zone

# Component sizes
COMP_W          = 150      # backend service
COMP_H          = 52
DB_W            = 120
DB_H            = 64
GW_W            = 150      # API gateway / integration
GW_H            = 56
HEX_W           = 110      # hexagon (F5 / FW / LB)
HEX_H           = 60

COMP_GAP_H      = 14       # horizontal gap between components
COMP_GAP_V      = 14       # vertical gap between rows

REGION_MIN_W    = 380
REGION_TITLE_H  = 44

# Max components per row — computed dynamically, see _row_budget()
MAX_ROW_W       = 460      # max usable width inside a zone for a single row


def _component_size(comp: dict) -> tuple[int, int]:
    t = comp.get("type", "BE")
    s = comp.get("shape", "")
    if t == "DB" or s == "cylinder":
        return DB_W, DB_H
    if t in ("IP", "MQ") or s in ("parallelogram", "message_queue"):
        return GW_W, GW_H
    if t == "LB" or s in ("hexagon", "trapezoid"):
        return HEX_W, HEX_H
    return COMP_W, COMP_H


def _split_into_rows(components: list, max_row_w: int = MAX_ROW_W) -> list[list]:
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


def _zone_size(zone: dict) -> tuple[int, int]:
    components = zone.get("components", [])
    if not components:
        return REGION_MIN_W - 2 * REGION_PAD, ZONE_HEADER + ZONE_PAD * 2 + 40

    rows = _split_into_rows(components)
    max_row_w = 0
    total_h = ZONE_HEADER + ZONE_PAD
    for row in rows:
        rw = sum(_component_size(c)[0] for c in row) + COMP_GAP_H * (len(row) - 1)
        rh = max(_component_size(c)[1] for c in row)
        max_row_w = max(max_row_w, rw)
        total_h += rh + COMP_GAP_V
    total_h += ZONE_PAD

    total_w = max_row_w + ZONE_PAD * 2
    return max(total_w, REGION_MIN_W - 2 * REGION_PAD), total_h


def _region_width(region: dict) -> int:
    rtype = region.get("type", "private_dc")
    zones_key = "network_zones" if rtype == "private_dc" else "subnets"
    zones = region.get(zones_key, [])
    if not zones:
        return REGION_MIN_W
    fake_zones = [{"components": z.get("components", [])} for z in zones]
    max_zw = max((_zone_size(fz)[0] for fz in fake_zones), default=REGION_MIN_W - 2 * REGION_PAD)
    return max(max_zw + REGION_PAD * 2, REGION_MIN_W)


def _region_height(region: dict) -> int:
    rtype = region.get("type", "private_dc")
    zones_key = "network_zones" if rtype == "private_dc" else "subnets"
    zones = region.get(zones_key, [])
    if not zones:
        return 200
    total_h = REGION_TITLE_H + REGION_PAD
    for zone in zones:
        fake = {"components": zone.get("components", [])}
        _, zh = _zone_size(fake)
        total_h += zh + ZONE_GAP
    total_h += REGION_PAD
    return total_h


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

    # ── Assign regions to two columns ────────────────────────────────────────
    left_regions  = [r for i, r in enumerate(deployment) if i % 2 == 0]
    right_regions = [r for i, r in enumerate(deployment) if i % 2 == 1]

    # Column widths = max region width in that column
    left_col_w  = max((_region_width(r)  for r in left_regions),  default=REGION_MIN_W)
    right_col_w = max((_region_width(r)  for r in right_regions), default=REGION_MIN_W)

    left_x  = CANVAS_MARGIN
    right_x = left_x + left_col_w + REGION_GAP
    start_y = 140   # space for header + internet node

    left_y  = start_y
    right_y = start_y

    for region in deployment:
        rid = region["id"]
        rtype = region.get("type", "private_dc")
        rw = left_col_w if rid in {r["id"] for r in left_regions} else right_col_w
        rh = _region_height(region)

        if rid in {r["id"] for r in left_regions}:
            positions[rid] = (left_x, left_y, rw, rh)
            left_y += rh + REGION_GAP
        else:
            positions[rid] = (right_x, right_y, rw, rh)
            right_y += rh + REGION_GAP

    # ── Place zones and components ────────────────────────────────────────────
    for region in deployment:
        rid = region["id"]
        rx, ry, rw, rh = positions[rid]
        rtype = region.get("type", "private_dc")
        zones_key = "network_zones" if rtype == "private_dc" else "subnets"

        avail_zone_w = rw - 2 * REGION_PAD
        zone_y_off   = REGION_TITLE_H + REGION_PAD

        for zone in region.get(zones_key, []):
            zid   = zone["id"]
            comps = zone.get("components", [])
            fake  = {"components": comps}
            _, zh = _zone_size(fake)

            positions[zid] = (REGION_PAD, zone_y_off, avail_zone_w, zh)
            zone_y_off += zh + ZONE_GAP

            # Layout components inside the zone (relative to zone top-left)
            rows  = _split_into_rows(comps, max_row_w=avail_zone_w - ZONE_PAD * 2)
            cy    = ZONE_HEADER + ZONE_PAD

            for row in rows:
                row_w = sum(_component_size(c)[0] for c in row) + COMP_GAP_H * (len(row) - 1)
                row_h = max(_component_size(c)[1] for c in row)
                # Centre the row
                cx = (avail_zone_w - row_w) // 2

                for comp in row:
                    cw, ch = _component_size(comp)
                    cid = comp["id"]
                    # Vertically centre within the tallest component in row
                    cy_adj = (row_h - ch) // 2
                    positions[cid] = (cx, cy + cy_adj, cw, ch)
                    cx += cw + COMP_GAP_H

                cy += row_h + COMP_GAP_V

    # ── Pre-compute absolute positions for components ─────────────────────────
    abs_positions: dict[str, tuple] = {}
    for region in deployment:
        rid = region["id"]
        rx, ry, rw, rh = positions[rid]
        rtype = region.get("type", "private_dc")
        zones_key = "network_zones" if rtype == "private_dc" else "subnets"

        for zone in region.get(zones_key, []):
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

    return {
        "positions":     positions,
        "abs_positions": abs_positions,
        "canvas_w":      canvas_w,
        "canvas_h":      canvas_h,
        "left_x":        left_x,
        "right_x":       right_x,
    }
