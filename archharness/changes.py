"""Change sets: semantic diffs and verifiable model updates.

A change set is a list of typed operations over an Architecture model::

    {"op": "add_node", "node": {...}}
    {"op": "remove_node", "id": "..."}
    {"op": "update_node", "id": "...", "fields": {...}}
    {"op": "add_edge", "edge": {"from": ..., "to": ..., ...}}
    {"op": "remove_edge", "from": "...", "to": "..."}

Rules:

- Identity is by stable ``id`` (nodes) and ``(from, to)`` pairs (edges),
  never by label text or layout position.
- :func:`apply_changeset` is pure (returns a new model) and runs reference
  validation afterwards: an update that dangles is rejected, never stored.
- AI-assisted edits and imports must produce a change set first; humans
  review the semantic summary before anything is applied.
"""

from __future__ import annotations

import copy

from .diagrams.generator import validate_architecture_refs

OPS = ("add_node", "remove_node", "update_node", "add_edge", "remove_edge")


class ChangeError(ValueError):
    """Raised for malformed operations or invalid resulting models."""


def _zones(arch: dict) -> list[dict]:
    zones = []
    for region in arch.get("deployment", []) or []:
        key = "network_zones" if region.get("type", "private_dc") == "private_dc" else "subnets"
        zones.extend(region.get(key, []) or [])
    return zones


def _nodes(arch: dict) -> dict[str, dict]:
    found: dict[str, dict] = {}
    for zone in _zones(arch):
        for comp in zone.get("components", []) or []:
            found[comp["id"]] = comp
    return found


def _edges(arch: dict) -> dict[tuple[str, str], dict]:
    return {(i.get("from", ""), i.get("to", "")): i
            for i in arch.get("interactions", []) or []}


def diff_arch(before: dict, after: dict) -> dict:
    """Compute the semantic change set transforming ``before`` into ``after``."""
    ops: list[dict] = []
    old_nodes, new_nodes = _nodes(before), _nodes(after)
    for node_id in sorted(set(new_nodes) - set(old_nodes)):
        ops.append({"op": "add_node", "node": copy.deepcopy(new_nodes[node_id])})
    for node_id in sorted(set(old_nodes) - set(new_nodes)):
        ops.append({"op": "remove_node", "id": node_id,
                    "name": old_nodes[node_id].get("name", node_id)})
    for node_id in sorted(set(old_nodes) & set(new_nodes)):
        old = {k: v for k, v in old_nodes[node_id].items() if k != "id"}
        new = {k: v for k, v in new_nodes[node_id].items() if k != "id"}
        if old != new:
            ops.append({"op": "update_node", "id": node_id, "fields": copy.deepcopy(new)})
    old_edges, new_edges = _edges(before), _edges(after)
    for pair in sorted(set(new_edges) - set(old_edges)):
        ops.append({"op": "add_edge", "edge": copy.deepcopy(new_edges[pair])})
    for pair in sorted(set(old_edges) - set(new_edges)):
        ops.append({"op": "remove_edge", "from": pair[0], "to": pair[1]})
    for pair in sorted(set(old_edges) & set(new_edges)):
        if old_edges[pair] != new_edges[pair]:
            ops.append({"op": "remove_edge", "from": pair[0], "to": pair[1]})
            ops.append({"op": "add_edge", "edge": copy.deepcopy(new_edges[pair])})
    return {"ops": ops}


def summarize(changeset: dict) -> list[str]:
    """Render a human-readable semantic summary of a change set."""
    lines = []
    for op in changeset.get("ops", []) or []:
        kind = op.get("op")
        if kind == "add_node":
            lines.append(f"+ node {op['node'].get('name', op['node'].get('id'))}")
        elif kind == "remove_node":
            lines.append(f"- node {op.get('name', op['id'])}")
        elif kind == "update_node":
            fields = ", ".join(sorted(op.get("fields", {})))
            lines.append(f"~ node {op['id']} ({fields})")
        elif kind == "add_edge":
            edge = op["edge"]
            lines.append(f"+ edge {edge.get('from')} -> {edge.get('to')}")
        elif kind == "remove_edge":
            lines.append(f"- edge {op.get('from')} -> {op.get('to')}")
        else:
            raise ChangeError(f"unknown op: {kind!r}")
    return lines


def apply_changeset(arch: dict, changeset: dict) -> dict:
    """Apply a change set to a model copy and validate the result."""
    if not isinstance(changeset, dict) or not isinstance(changeset.get("ops", []), list):
        raise ChangeError("change set must be a mapping with an `ops` list")
    result = copy.deepcopy(arch)
    nodes = _nodes(result)
    edges = _edges(result)
    default_zone = _default_zone(result)

    for op in changeset["ops"]:
        kind = op.get("op")
        if kind == "add_node":
            node = copy.deepcopy(op.get("node") or {})
            node_id = node.get("id")
            if not node_id:
                raise ChangeError("add_node requires node.id")
            if node_id in nodes:
                raise ChangeError(f"node already exists: {node_id!r}")
            default_zone.setdefault("components", []).append(node)
            nodes[node_id] = node
        elif kind == "remove_node":
            node_id = op.get("id")
            if node_id not in nodes:
                raise ChangeError(f"unknown node: {node_id!r}")
            for zone in _zones(result):
                zone["components"] = [c for c in zone.get("components", []) or []
                                      if c.get("id") != node_id]
            nodes.pop(node_id)
            result["interactions"] = [i for i in result.get("interactions", []) or []
                                      if i.get("from") != node_id and i.get("to") != node_id]
            edges = _edges(result)
        elif kind == "update_node":
            node_id = op.get("id")
            if node_id not in nodes:
                raise ChangeError(f"unknown node: {node_id!r}")
            if not isinstance(op.get("fields"), dict):
                raise ChangeError(f"update_node {node_id!r} requires a fields mapping")
            nodes[node_id].update(copy.deepcopy(op["fields"]))
            nodes[node_id]["id"] = node_id
        elif kind == "add_edge":
            edge = copy.deepcopy(op.get("edge") or {})
            pair = (edge.get("from", ""), edge.get("to", ""))
            if not pair[0] or not pair[1]:
                raise ChangeError("add_edge requires from/to")
            result.setdefault("interactions", [])
            result["interactions"] = [i for i in result["interactions"]
                                      if (i.get("from"), i.get("to")) != pair]
            result["interactions"].append(edge)
            edges = _edges(result)
        elif kind == "remove_edge":
            pair = (op.get("from", ""), op.get("to", ""))
            result["interactions"] = [i for i in result.get("interactions", []) or []
                                      if (i.get("from"), i.get("to")) != pair]
            edges = _edges(result)
        else:
            raise ChangeError(f"unknown op: {kind!r}")

    try:
        validate_architecture_refs(result)
    except ValueError as exc:
        raise ChangeError(f"resulting model is invalid: {exc}") from exc
    return result


def _default_zone(arch: dict) -> dict:
    zones = _zones(arch)
    if not zones:
        raise ChangeError("model has no zone to host added nodes")
    return zones[0]
