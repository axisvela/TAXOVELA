"""Versioned contract schemas for ArchHarness artifacts.

Schemas live as JSON Schema documents under ``schemas/`` (shipped in the
wheel via ``archharness/data/schemas``). This module resolves them and
validates plain Python data against the subset of JSON Schema we use
(``type``, ``required``, ``properties``, ``additionalProperties`` including
boolean ``false``, ``items``, ``enum``, ``const``, ``pattern``, ``minimum``,
``maximum``, ``minProperties``, and local ``$ref`` pointers into ``$defs``).
The subset is deliberately dependency-free; anything richer should be validated
with an external ``jsonschema`` implementation against the same schema files.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

SCHEMA_IDS = ("req/v1", "req/v2", "artifact/v1", "validation/v1", "enforcement/v1")

_SCHEMA_FILES = {
    "req/v1": "req-v1.schema.json",
    "req/v2": "req-v2.schema.json",
    "artifact/v1": "artifact-v1.schema.json",
    "validation/v1": "validation-v1.schema.json",
    "enforcement/v1": "enforcement-v1.schema.json",
}


class SchemaError(ValueError):
    """Raised when data violates its contract schema."""


def schema_dir() -> Path:
    """Locate the schemas directory (checkout or installed package data)."""
    here = Path(__file__).resolve().parent
    candidates = [
        here.parent / "schemas",  # repository checkout
        here / "data" / "schemas",  # installed wheel
    ]
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("ArchHarness schemas directory not found")


def load_schema(schema_id: str) -> dict:
    """Load the JSON Schema document for a contract id like ``req/v1``."""
    if schema_id not in _SCHEMA_FILES:
        raise SchemaError(f"unknown schema: {schema_id}")
    path = schema_dir() / _SCHEMA_FILES[schema_id]
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise SchemaError(f"cannot load schema {schema_id}: {exc}") from exc


def _check_type(value: object, expected: object, path: str) -> None:
    types = [expected] if isinstance(expected, str) else list(expected or [])
    if not types:
        return
    ok = False
    for name in types:
        if name == "null" and value is None:
            ok = True
        elif name == "object" and isinstance(value, dict):
            ok = True
        elif name == "array" and isinstance(value, list):
            ok = True
        elif name == "string" and isinstance(value, str):
            ok = True
        elif name == "number" and isinstance(value, (int, float)) and not isinstance(value, bool):
            ok = True
        elif name == "integer" and isinstance(value, int) and not isinstance(value, bool):
            ok = True
        elif name == "boolean" and isinstance(value, bool):
            ok = True
    if not ok:
        raise SchemaError(f"{path}: expected type {expected}, got {type(value).__name__}")


def _resolve_ref(ref: str, root: dict) -> dict:
    """Resolve a local JSON Pointer ``$ref`` (``#/$defs/name``) against the root."""
    if not ref.startswith("#/"):
        raise SchemaError(f"unsupported $ref: {ref}")
    node: object = root
    for token in ref[2:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if not isinstance(node, dict) or token not in node:
            raise SchemaError(f"cannot resolve $ref: {ref}")
        node = node[token]
    if not isinstance(node, dict):
        raise SchemaError(f"$ref does not resolve to a schema: {ref}")
    return node


def _validate(node: object, schema: dict, path: str, root: dict | None = None) -> None:
    if not isinstance(schema, dict):
        return
    if root is None:
        root = schema
    if "$ref" in schema:
        _validate(node, _resolve_ref(schema["$ref"], root), path, root)
        return
    if "const" in schema and node != schema["const"]:
        raise SchemaError(f"{path}: expected {schema['const']!r}, got {node!r}")
    if "enum" in schema and node not in schema["enum"]:
        raise SchemaError(f"{path}: {node!r} is not an allowed value")
    if "pattern" in schema and isinstance(node, str):
        if not re.fullmatch(schema["pattern"], node):
            raise SchemaError(f"{path}: {node!r} does not match {schema['pattern']!r}")
    if isinstance(node, (int, float)) and not isinstance(node, bool):
        if "minimum" in schema and node < schema["minimum"]:
            raise SchemaError(f"{path}: {node!r} is below minimum {schema['minimum']!r}")
        if "maximum" in schema and node > schema["maximum"]:
            raise SchemaError(f"{path}: {node!r} is above maximum {schema['maximum']!r}")
    if isinstance(node, dict) and "minProperties" in schema:
        if len(node) < schema["minProperties"]:
            raise SchemaError(f"{path}: expected at least {schema['minProperties']} properties")
    if "type" in schema:
        _check_type(node, schema["type"], path)
    if isinstance(node, dict):
        for key in schema.get("required", []) or []:
            if key not in node:
                raise SchemaError(f"{path}: missing required key {key!r}")
        properties = schema.get("properties", {}) or {}
        for key, subschema in properties.items():
            if key in node:
                _validate(node[key], subschema, f"{path}.{key}", root)
        additional = schema.get("additionalProperties")
        if additional is False:
            for key in node:
                if key not in properties:
                    raise SchemaError(f"{path}: unexpected key {key!r}")
        elif isinstance(additional, dict):
            for key, value in node.items():
                if key not in properties:
                    _validate(value, additional, f"{path}.{key}", root)
    if isinstance(node, list):
        items = schema.get("items")
        if isinstance(items, dict):
            for index, item in enumerate(node):
                _validate(item, items, f"{path}[{index}]", root)


def validate(data: object, schema_id: str) -> None:
    """Validate ``data`` against a contract schema. Raises SchemaError."""
    _validate(data, load_schema(schema_id), "$")


def validate_final_req(doc: object) -> None:
    """Validate a final requirements document against ``req/v1``."""
    validate(doc, "req/v1")


def validate_final_req_v2(doc: object) -> None:
    """Validate a final requirements document against ``req/v2``."""
    validate(doc, "req/v2")


def validate_manifest(manifest: object) -> None:
    """Validate an artifact manifest against ``artifact/v1``."""
    validate(manifest, "artifact/v1")


def validate_validation_result(doc: object) -> None:
    """Validate a validation result against ``validation/v1``."""
    validate(doc, "validation/v1")


def validate_enforcement_result(doc: object) -> None:
    """Validate an enforcement decision against ``enforcement/v1``."""
    validate(doc, "enforcement/v1")
