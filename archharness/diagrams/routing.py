"""Deterministic orthogonal routing for draw.io edges.

draw.io's automatic router is a useful fallback, but it does not know the
semantic region/zone layout emitted by ArchHarness.  This module emits stable
Manhattan waypoints, choosing a clear side of each endpoint and rejecting paths
that pass through another component.  It intentionally has no graph-layout or
draw.io runtime dependency.
"""

from __future__ import annotations

from dataclasses import dataclass
import heapq

from . import topology


def _load_policy() -> dict[str, int]:
    """Load router controls from the shared diagram style standard."""
    defaults = {"gutter": 28, "lane_gap": 14, "max_visibility_nodes": 256}
    try:
        import yaml
        from ..paths import require_archharness_root
        raw = yaml.safe_load((require_archharness_root() / "standards" / "diagram-style.yaml").read_text(
            encoding="utf-8")) or {}
        configured = raw.get("routing") or {}
        return {key: int(configured.get(key, value)) for key, value in defaults.items()}
    except Exception:
        return defaults


ROUTING_POLICY = _load_policy()
GUTTER = ROUTING_POLICY["gutter"]
LANE_GAP = ROUTING_POLICY["lane_gap"]
MAX_VISIBILITY_NODES = ROUTING_POLICY["max_visibility_nodes"]


@dataclass(frozen=True)
class Rect:
    x: float
    y: float
    w: float
    h: float

    @property
    def right(self) -> float:
        return self.x + self.w

    @property
    def bottom(self) -> float:
        return self.y + self.h

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2

    def expanded(self, margin: float) -> "Rect":
        return Rect(self.x - margin, self.y - margin,
                    self.w + margin * 2, self.h + margin * 2)


@dataclass(frozen=True)
class Route:
    """Connection constraints and root-canvas waypoints for one edge."""
    points: tuple[tuple[int, int], ...]
    exit_x: float
    exit_y: float
    entry_x: float
    entry_y: float
    fallback: bool = False
    strategy: str = "direct"


def _segment_hits_rect(a: tuple[float, float], b: tuple[float, float], rect: Rect) -> bool:
    """Return whether an axis-aligned segment intersects *rect* inclusively."""
    ax, ay = a
    bx, by = b
    if ax == bx:
        return rect.x <= ax <= rect.right and min(ay, by) <= rect.bottom and max(ay, by) >= rect.y
    if ay == by:
        return rect.y <= ay <= rect.bottom and min(ax, bx) <= rect.right and max(ax, bx) >= rect.x
    raise ValueError("Only orthogonal segments can be routed")


def _path_clear(points: list[tuple[float, float]], obstacles: list[Rect]) -> bool:
    return not any(
        _segment_hits_rect(a, b, obstacle)
        for a, b in zip(points, points[1:])
        for obstacle in obstacles
    )


def _side_point(rect: Rect, x: float, y: float) -> tuple[float, float, float, float]:
    """Closest boundary point to a proposed first/last waypoint plus constraint."""
    dx, dy = x - rect.cx, y - rect.cy
    if abs(dx) >= abs(dy):
        if dx >= 0:
            return rect.right, rect.cy, 1.0, 0.5
        return rect.x, rect.cy, 0.0, 0.5
    if dy >= 0:
        return rect.cx, rect.bottom, 0.5, 1.0
    return rect.cx, rect.y, 0.5, 0.0


def _offset_port(x: float, y: float, lane: int) -> tuple[float, float]:
    """Spread parallel edges along their selected source/target perimeter."""
    # Keep ports away from corners, whose custom-shape perimeters vary in
    # draw.io.  The lane's first two offsets produce 0.62 and 0.38.
    port_offset = max(-0.3, min(0.3, _lane(lane) / LANE_GAP * 0.12))
    if x in (0.0, 1.0):
        return x, max(0.15, min(0.85, y + port_offset))
    return max(0.15, min(0.85, x + port_offset)), y


def _dedupe(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    result: list[tuple[float, float]] = []
    for point in points:
        if not result or point != result[-1]:
            result.append(point)
    return result


def _lane(index: int) -> float:
    """Symmetric, deterministic offsets: 0, +1, -1, +2, -2 ..."""
    if index == 0:
        return 0
    magnitude = (index + 1) // 2
    return LANE_GAP * magnitude * (1 if index % 2 else -1)


def _visibility_path(src: Rect, tgt: Rect, obstacles: list[Rect]) -> list[tuple[float, float]] | None:
    """Find the shortest bounded orthogonal path around component rectangles.

    The graph contains only component clearance boundaries plus endpoint centres,
    keeping it deterministic and small while covering routes that the fixed L
    candidates cannot express.  The caller removes the endpoint centres before
    serialising the remaining vertices as draw.io waypoints.
    """
    if not obstacles:
        return None
    start = (src.cx, src.cy)
    goal = (tgt.cx, tgt.cy)
    xs = {start[0], goal[0]}
    ys = {start[1], goal[1]}
    for obstacle in obstacles:
        # One canvas unit outside the inclusive clearance rectangle ensures a
        # path that follows a boundary is still treated as obstacle-free.
        xs.update((obstacle.x - 1, obstacle.right + 1))
        ys.update((obstacle.y - 1, obstacle.bottom + 1))

    # Complex diagrams retain the proven outer-gutter fallback instead of
    # allocating an unbounded Cartesian grid for an exceptional route.
    if len(xs) * len(ys) > MAX_VISIBILITY_NODES:
        return None

    nodes = [(x, y) for x in sorted(xs) for y in sorted(ys)
             if (x, y) in (start, goal) or not any(
                 obstacle.x <= x <= obstacle.right and obstacle.y <= y <= obstacle.bottom
                 for obstacle in obstacles)]
    node_set = set(nodes)
    if start not in node_set or goal not in node_set:
        return None

    neighbours: dict[tuple[float, float], list[tuple[tuple[float, float], float]]] = {
        node: [] for node in nodes
    }

    def add_adjacent(nodes_on_line: list[tuple[float, float]]) -> None:
        """Connect only adjacent visible grid nodes on one horizontal/vertical line.

        Connecting every collinear pair is quadratic in the grid size and
        becomes impractical for large diagrams.  Adjacent visible nodes retain
        all reachable Manhattan paths while making the graph linear in edges.
        """
        for node, other in zip(nodes_on_line, nodes_on_line[1:]):
            if not _path_clear([node, other], obstacles):
                continue
            distance = abs(node[0] - other[0]) + abs(node[1] - other[1])
            neighbours[node].append((other, distance))
            neighbours[other].append((node, distance))

    by_x: dict[float, list[tuple[float, float]]] = {}
    by_y: dict[float, list[tuple[float, float]]] = {}
    for node in nodes:
        by_x.setdefault(node[0], []).append(node)
        by_y.setdefault(node[1], []).append(node)
    for line in by_x.values():
        add_adjacent(sorted(line, key=lambda point: point[1]))
    for line in by_y.values():
        add_adjacent(sorted(line, key=lambda point: point[0]))

    distances = {start: 0.0}
    previous: dict[tuple[float, float], tuple[float, float]] = {}
    queue = [(0.0, start)]
    while queue:
        distance, node = heapq.heappop(queue)
        if distance != distances.get(node):
            continue
        if node == goal:
            path = [goal]
            while path[-1] != start:
                path.append(previous[path[-1]])
            return list(reversed(path))
        for other, edge_distance in neighbours[node]:
            candidate = distance + edge_distance
            if candidate < distances.get(other, float("inf")):
                distances[other] = candidate
                previous[other] = node
                heapq.heappush(queue, (candidate, other))
    return None


def route(src: Rect, tgt: Rect, obstacles: list[Rect], *, lane: int = 0,
          rails_x: tuple[float, ...] = (), rails_y: tuple[float, ...] = ()) -> Route:
    """Choose a short obstacle-free orthogonal route.

    ``rails_x`` and ``rails_y`` are pre-reserved region/zone gutter coordinates.
    The first clear candidate wins, making output deterministic and easy to
    reason about.  If every route is blocked we return a constraint-only route;
    draw.io then applies its normal automatic orthogonal routing.
    """
    offset = _lane(lane)
    expanded = [rect.expanded(GUTTER / 2) for rect in obstacles]
    candidates: list[tuple[str, list[tuple[float, float]]]] = []

    # Direct routes are the clearest when endpoints are aligned and unblocked.
    if src.cy == tgt.cy:
        candidates.append(("direct-horizontal", []))
    if src.cx == tgt.cx:
        candidates.append(("direct-vertical", []))

    # Region/zone gutters take priority where supplied so cross-boundary flows
    # use a visible, repeatable channel instead of cutting through a container.
    for rail in rails_x:
        candidates.append(("region-gutter", [(rail + offset, src.cy), (rail + offset, tgt.cy)]))
    for rail in rails_y:
        candidates.append(("zone-gutter", [(src.cx, rail + offset), (tgt.cx, rail + offset)]))

    # Midpoint candidates favour the shortest H-V-H / V-H-V path for local flows
    # and act as a fallback if a selected gutter is obstructed.
    midpoint_x = (src.cx + tgt.cx) / 2 + offset
    midpoint_y = (src.cy + tgt.cy) / 2 + offset
    candidates.extend([
        ("midpoint-x", [(midpoint_x, src.cy), (midpoint_x, tgt.cy)]),
        ("midpoint-y", [(src.cx, midpoint_y), (tgt.cx, midpoint_y)]),
    ])

    # If fixed L routes are blocked, find a compact path along obstacle
    # clearance boundaries before resorting to a canvas-wide outer detour.
    visibility_path = _visibility_path(src, tgt, expanded)
    if visibility_path and len(visibility_path) > 2:
        candidates.append(("visibility-graph", visibility_path[1:-1]))

    # Last resort: route around the outside of all component rectangles.
    if expanded:
        candidates.extend([
            ("outer-left", [(min(r.x for r in expanded) - GUTTER + offset, src.cy),
                            (min(r.x for r in expanded) - GUTTER + offset, tgt.cy)]),
            ("outer-right", [(max(r.right for r in expanded) + GUTTER + offset, src.cy),
                             (max(r.right for r in expanded) + GUTTER + offset, tgt.cy)]),
            ("outer-top", [(src.cx, min(r.y for r in expanded) - GUTTER + offset),
                           (tgt.cx, min(r.y for r in expanded) - GUTTER + offset)]),
            ("outer-bottom", [(src.cx, max(r.bottom for r in expanded) + GUTTER + offset),
                              (tgt.cx, max(r.bottom for r in expanded) + GUTTER + offset)]),
        ])

    for strategy, candidate in candidates:
        candidate = _dedupe(candidate)
        first_x, first_y = candidate[0] if candidate else (tgt.cx, tgt.cy)
        last_x, last_y = candidate[-1] if candidate else (src.cx, src.cy)
        sx, sy, exit_x, exit_y = _side_point(src, first_x, first_y)
        tx, ty, entry_x, entry_y = _side_point(tgt, last_x, last_y)
        exit_x, exit_y = _offset_port(exit_x, exit_y, lane)
        entry_x, entry_y = _offset_port(entry_x, entry_y, lane)
        path = _dedupe([(sx, sy), *candidate, (tx, ty)])
        if _path_clear(path, expanded):
            points = tuple((round(x), round(y)) for x, y in candidate)
            return Route(points, exit_x, exit_y, entry_x, entry_y, strategy=strategy)

    # No explicit route: retain stable side selection and let draw.io recover.
    _sx, _sy, exit_x, exit_y = _side_point(src, tgt.cx, tgt.cy)
    _tx, _ty, entry_x, entry_y = _side_point(tgt, src.cx, src.cy)
    exit_x, exit_y = _offset_port(exit_x, exit_y, lane)
    entry_x, entry_y = _offset_port(entry_x, entry_y, lane)
    return Route((), exit_x, exit_y, entry_x, entry_y, fallback=True, strategy="drawio-fallback")


def routing_context(arch: dict, layout: dict) -> tuple[
        dict[str, Rect], dict[str, tuple[str, str]],
        dict[str, tuple[float, ...]], dict[str, tuple[float, ...]]]:
    """Build component obstacles, ownership, and container-specific gutters.

    Rails remain scoped to their owning region or zone.  A route between two
    containers can therefore use only its endpoints' outside channels instead
    of taking an unrelated third container's rail across the whole canvas.
    """
    positions = layout["positions"]
    absolute = layout["abs_positions"]
    deployment = arch.get("deployment", arch.get("arch", {}).get("deployment", [])) or []
    owner: dict[str, tuple[str, str]] = {}
    region_rects: dict[str, Rect] = {}
    zone_rects: dict[str, Rect] = {}
    for region in deployment:
        rid = region["id"]
        if rid in positions:
            region_rects[rid] = Rect(*positions[rid])
        for zone in topology.region_zones(region):
            zid = zone["id"]
            if zid in positions and rid in region_rects:
                zx, zy, zw, zh = positions[zid]
                rr = region_rects[rid]
                zone_rects[zid] = Rect(rr.x + zx, rr.y + zy, zw, zh)
            for comp in zone.get("components", []) or []:
                owner[comp.get("id", "")] = (rid, zid)
                for member in comp.get("member_specs", []) or []:
                    owner[member.get("id", "")] = (rid, zid)

    rects = {cid: Rect(*pos) for cid, pos in absolute.items()}
    region_rails_x = {
        rid: (round(rect.x - GUTTER), round(rect.right + GUTTER))
        for rid, rect in region_rects.items()
    }
    zone_rails_y = {
        zid: (round(rect.y - GUTTER), round(rect.bottom + GUTTER))
        for zid, rect in zone_rects.items()
    }
    return rects, owner, region_rails_x, zone_rails_y


def scoped_rails(src_owner: tuple[str, str] | None, tgt_owner: tuple[str, str] | None,
                 region_rails_x: dict[str, tuple[float, ...]],
                 zone_rails_y: dict[str, tuple[float, ...]]) -> tuple[tuple[float, ...], tuple[float, ...]]:
    """Return only the gutters relevant to a cross-container interaction."""
    if not src_owner or not tgt_owner:
        return (), ()
    rails_x: tuple[float, ...] = ()
    rails_y: tuple[float, ...] = ()
    if src_owner[0] != tgt_owner[0]:
        rails_x = tuple(sorted(set(
            region_rails_x.get(src_owner[0], ()) + region_rails_x.get(tgt_owner[0], ())
        )))
    if src_owner[1] != tgt_owner[1]:
        rails_y = tuple(sorted(set(
            zone_rails_y.get(src_owner[1], ()) + zone_rails_y.get(tgt_owner[1], ())
        )))
    return rails_x, rails_y
