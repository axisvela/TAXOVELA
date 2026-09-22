"""
topology.py — private-cloud zone-boundary semantics for the diagram renderers.

**Private cloud**: a firewall is a *container-class infra node*. It sits on the
network-zone boundary, so every flow entering or leaving that zone passes through
it implicitly. Such a node must not be drawn as a component with per-component
edges — the renderers contract it out of the interaction graph (``A → FW → B``
becomes ``A → B``) and mark the zone as firewalled instead.

**Public cloud**: a firewall may instead live in its own dedicated subnet and be
addressed explicitly, so those nodes stay in the graph as ordinary nodes.
"""

from __future__ import annotations

BOUNDARY_ROLE = "zone_boundary"
PROVIDER_ROLE = "service_provider"

# Policy fallback, used only when standards/diagram-roles.yaml cannot be read.
_FALLBACK_POLICY = {
    "regions": {
        "default": {"zones_key": "subnets", "boundary_roles": []},
        "by_type": {"private_dc": {"zones_key": "network_zones",
                                   "boundary_roles": ["zone_boundary"]}},
    },
    "roles": {
        "zone_boundary": {"attribute": "role", "signals": {
            "node_kind": ["firewall", "waf", "security_gateway"], "type": ["FW"]}},
        "service_provider": {"attribute": "role", "direction": "inbound_only",
                             "signals": {"component_role": ["message_bus"], "type": ["MQ"],
                                         "shape": ["message_queue"]}},
        "logical_group": {"attribute": "group", "min_size": 3},
    },
    "layout": {"max_group_width": 470, "max_component_width": 260},
}


def _load_policy() -> dict:
    try:
        import yaml
        from ..paths import require_archharness_root
        path = require_archharness_root() / "standards" / "diagram-roles.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return data if data.get("roles") else _FALLBACK_POLICY
    except Exception:
        return _FALLBACK_POLICY


POLICY = _load_policy()
_ROLES = POLICY.get("roles") or {}
_REGIONS = POLICY.get("regions") or {}
LAYOUT_POLICY = POLICY.get("layout") or {}
GROUP_MIN_SIZE = int((_ROLES.get("logical_group") or {}).get("min_size", 3))
GROUP_MAX_W = int(LAYOUT_POLICY.get("max_group_width", 470))


def region_policy(region: dict) -> dict:
    """Merge the default region policy with the one for this region's type."""
    merged = dict((_REGIONS.get("default") or {"zones_key": "subnets",
                                               "boundary_roles": []}))
    merged.update((_REGIONS.get("by_type") or {}).get(region.get("type", ""), {}))
    return merged


def region_zones_key(region: dict) -> str:
    return region_policy(region).get("zones_key", "subnets")


def region_zones(region: dict) -> list:
    return region.get(region_zones_key(region), []) or []


RESERVED_NODES = {"internet", "user", "office-network"}

_ZONE_BEARING_KEYS = ("deployment", "subnets", "network_zones")


def deployment_of(arch: dict) -> list:
    """Return the deployment list, accepting both top-level and ``arch:`` nesting."""
    if not isinstance(arch, dict):
        return []
    nested = arch.get("arch")
    if isinstance(nested, dict) and isinstance(nested.get("deployment"), list):
        return nested["deployment"]
    return arch.get("deployment") or []


def interactions_of(arch: dict) -> list:
    """Return the interaction list, accepting both top-level and ``arch:`` nesting."""
    if not isinstance(arch, dict):
        return []
    nested = arch.get("arch")
    if isinstance(nested, dict) and isinstance(nested.get("interactions"), list):
        return nested["interactions"]
    return arch.get("interactions") or []


def collect_declared_ids(arch: dict) -> tuple[set[str], list[str]]:
    """Collect region/zone/component IDs, reporting duplicates once each."""
    seen: set[str] = set()
    declared: set[str] = set()
    duplicates: list[str] = []

    def _add(node_id: str) -> None:
        if not node_id:
            return
        if node_id in seen:
            if node_id not in duplicates:
                duplicates.append(node_id)
        else:
            seen.add(node_id)
            declared.add(node_id)

    for region in deployment_of(arch):
        if not isinstance(region, dict):
            continue
        _add(region.get("id", ""))
        for zone in region_zones(region):
            if not isinstance(zone, dict):
                continue
            _add(zone.get("id", ""))
            for comp in zone.get("components", []) or []:
                if isinstance(comp, dict):
                    _add(comp.get("id", ""))
    return declared, duplicates


def node_has_role(comp: dict, role: str) -> bool:
    """Explicit attribute first, then structural signals, then opt-in patterns."""
    spec = _ROLES.get(role) or {}
    attribute = spec.get("attribute")
    if attribute and comp.get(attribute) == role:
        return True
    for key, values in (spec.get("signals") or {}).items():
        value = comp.get(key)
        if value is not None and value in (values or []):
            return True
    text = f"{comp.get('name', '')} {comp.get('id', '')}".lower()
    return any(str(p).lower() in text for p in (spec.get("name_patterns") or []))


def _regions_with_role(arch: dict, role: str):
    """Yield (region, zone, component) for every node carrying ``role``."""
    deployment = arch.get("deployment", arch.get("arch", {}).get("deployment", [])) or []
    for region in deployment:
        if role not in (region_policy(region).get("boundary_roles") or []):
            continue
        for zone in region_zones(region):
            for comp in zone.get("components", []) or []:
                if node_has_role(comp, role):
                    yield region, zone, comp


def zone_boundary_ids(arch: dict) -> set[str]:
    """IDs of nodes that act as zone boundaries (per region policy)."""
    return {comp.get("id") for _r, _z, comp in _regions_with_role(arch, BOUNDARY_ROLE)}


def boundary_zones(arch: dict) -> set[str]:
    """Zone IDs that contain a boundary node (used to mark the zone)."""
    return {zone.get("id") for _r, zone, _c in _regions_with_role(arch, BOUNDARY_ROLE)}


def _all_components(arch: dict) -> list:
    out = []
    for region in arch.get("deployment", arch.get("arch", {}).get("deployment", [])) or []:
        for zone in region_zones(region):
            out.extend(zone.get("components", []) or [])
    return out


def normalize_provider_direction(arch: dict) -> dict:
    """A message bus is a *service provider*: every edge points into it.

    Producers and consumers both initiate against the bus, so an edge that leaves
    the bus is reversed (the label stays the same). This keeps the arrow meaning
    "caller → provider" everywhere, which is what the reader expects of a broker.
    """
    bus_ids = {c.get("id") for c in _all_components(arch)
               if node_has_role(c, PROVIDER_ROLE)}
    if not bus_ids:
        return arch
    interactions = arch.get("interactions", arch.get("arch", {}).get("interactions", [])) or []
    for edge in interactions:
        src, tgt = edge.get("from", ""), edge.get("to", "")
        if src in bus_ids and tgt not in bus_ids:
            edge["from"], edge["to"] = tgt, src
    return arch


def prepare(arch: dict, min_size: int = GROUP_MIN_SIZE):
    """Normalise provider direction, then fold interchangeable siblings."""
    arch = normalize_provider_direction(arch)
    return collapse_groups(arch, min_size=min_size)


def _relations(interactions: list, skip: set[str]) -> dict:
    """Signature of every component's edges: {(dir, other, protocol)}."""
    rel: dict[str, set] = {}
    for edge in interactions or []:
        src, tgt = edge.get("from", ""), edge.get("to", "")
        if src in skip or tgt in skip:
            continue
        protocol = edge.get("protocol", "")
        rel.setdefault(src, set()).add(("out", tgt, protocol))
        rel.setdefault(tgt, set()).add(("in", src, protocol))
    return rel


def collapse_groups(arch: dict, min_size: int = GROUP_MIN_SIZE):
    """Fold sibling components that are interchangeable into one logical group.

    Two components belong together when they live in the same zone, share a
    technology signature, and have **identical edge signatures** — same peers,
    same protocols, same direction. Such components are a logical group, so the
    diagram draws one dashed box per group and a single edge per peer instead of
    a fan of near-identical edges.

    Returns ``(arch, groups)``; ``groups`` maps group id → member ids.
    """
    import copy
    from . import labels

    arch = copy.deepcopy(arch)
    deployment = arch.get("deployment", arch.get("arch", {}).get("deployment", [])) or []
    interactions = arch.get("interactions", arch.get("arch", {}).get("interactions", [])) or []
    boundary = zone_boundary_ids(arch)
    rel = _relations(interactions, boundary)

    groups: dict[str, list[str]] = {}
    id_map: dict[str, str] = {}

    for region in deployment:
        for zone in region_zones(region):
            components = zone.get("components", []) or []
            buckets: dict = {}
            for comp in components:
                cid = comp.get("id")
                if not cid or cid in boundary:
                    continue
                signature = (
                    comp.get("group"),                      # explicit grouping wins
                    labels.tech_line(comp),
                    frozenset(rel.get(cid, set())),
                )
                buckets.setdefault(signature, []).append(comp)

            new_components = []
            consumed: set[str] = set()
            for comp in components:
                cid = comp.get("id")
                signature = (
                    comp.get("group"),
                    labels.tech_line(comp),
                    frozenset(rel.get(cid, set())),
                )
                members = buckets.get(signature, [])
                if cid in consumed:
                    continue                     # already folded into a group
                if len(members) < min_size:
                    new_components.append(comp)
                    continue

                gid = f"GRP-{members[0]['id']}"
                for member in members:
                    consumed.add(member.get("id"))
                    id_map[member.get("id")] = gid
                groups[gid] = [m.get("id") for m in members]
                new_components.append({
                    "id": gid,
                    "name": members[0].get("group") or f"{members[0].get('type', 'BE')} group ×{len(members)}",
                    "type": members[0].get("type", "BE"),
                    "shape": "group",
                    "language": members[0].get("language"),
                    "framework": members[0].get("framework"),
                    "runtime": members[0].get("runtime"),
                    "sensitivity": members[0].get("sensitivity"),
                    "is_group": True,
                    "members": [m.get("id") for m in members],
                    "member_names": [m.get("name", m.get("id", "")) for m in members],
                    # Full specs so the renderers draw the members as real nodes
                    # nested inside the group frame (not as a text list).
                    "member_specs": [dict(m) for m in members],
                })
            zone["components"] = new_components

    # Rewrite edges onto the group boxes; drop edges that become internal.
    rewritten, seen = [], set()
    for edge in interactions:
        src = id_map.get(edge.get("from", ""), edge.get("from", ""))
        tgt = id_map.get(edge.get("to", ""), edge.get("to", ""))
        if src == tgt:
            continue
        key = (src, tgt, edge.get("protocol", ""), edge.get("auth", ""))
        if key in seen:
            continue
        seen.add(key)
        merged = dict(edge)
        merged["from"], merged["to"] = src, tgt
        rewritten.append(merged)

    if "interactions" in arch:
        arch["interactions"] = rewritten
    else:
        arch.setdefault("arch", {})["interactions"] = rewritten
    return arch, groups


def contract(interactions: list, boundary_ids: set[str]) -> list:
    """Remove zone-boundary nodes from the interaction graph.

    A boundary firewall is *not* a hub, so an edge that names one is not a real
    component-to-component relation and is dropped (the zone's ``· FW`` marker
    says all its in/out traffic passes the firewall). Flows must be declared
    directly between the components that talk — see rule R-INF-4. Pairing
    ``A → FW`` against every ``FW → B`` would wrongly create a complete
    bipartite graph, so no reconnection is attempted.
    """
    interactions = list(interactions or [])
    if not boundary_ids:
        return interactions

    kept: list = []
    seen: set = set()
    for edge in interactions:
        if edge.get("from", "") in boundary_ids or edge.get("to", "") in boundary_ids:
            continue
        key = (edge.get("from", ""), edge.get("to", ""), edge.get("protocol", ""))
        if key in seen:
            continue
        seen.add(key)
        kept.append(edge)
    return kept
