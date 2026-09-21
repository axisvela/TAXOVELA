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

FIREWALL_HINTS = ("firewall", "azfw", "pan-os", "fortigate", "waf")
BOUNDARY_ROLE = "zone_boundary"


GROUP_MIN_SIZE = 3          # fewer than this is not worth drawing as a group
GROUP_MAX_W = 340           # a group box never widens beyond this


def _is_boundary_component(comp: dict) -> bool:
    if comp.get("role") == BOUNDARY_ROLE:
        return True
    text = f"{comp.get('name', '')} {comp.get('id', '')}".lower()
    return any(hint in text for hint in FIREWALL_HINTS)


def zone_boundary_ids(arch: dict) -> set[str]:
    """IDs of private-cloud firewall nodes that act as zone boundaries."""
    ids: set[str] = set()
    deployment = arch.get("deployment", arch.get("arch", {}).get("deployment", [])) or []
    for region in deployment:
        # Public cloud keeps explicit firewall nodes (own subnet / peering rules).
        if region.get("type", "private_dc") != "private_dc":
            continue
        for zone in region.get("network_zones", []) or []:
            for comp in zone.get("components", []) or []:
                if _is_boundary_component(comp):
                    ids.add(comp.get("id"))
    return ids


def boundary_zones(arch: dict) -> set[str]:
    """Zone IDs that contain a boundary firewall (used to mark the zone)."""
    zones: set[str] = set()
    deployment = arch.get("deployment", arch.get("arch", {}).get("deployment", [])) or []
    for region in deployment:
        if region.get("type", "private_dc") != "private_dc":
            continue
        for zone in region.get("network_zones", []) or []:
            for comp in zone.get("components", []) or []:
                if _is_boundary_component(comp):
                    zones.add(zone.get("id"))
    return zones


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
        if region.get("type", "private_dc") != "private_dc":
            zones = region.get("subnets", []) or []
        else:
            zones = region.get("network_zones", []) or []
        for zone in zones:
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
