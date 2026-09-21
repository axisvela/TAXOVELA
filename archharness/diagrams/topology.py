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
