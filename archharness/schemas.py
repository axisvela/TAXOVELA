"""Versioned contract schemas for ArchHarness artifacts.

Schemas live as JSON Schema documents under ``schemas/`` (shipped in the
wheel via ``archharness/data/schemas``). This module resolves them and
validates plain Python data against the subset of JSON Schema we use
(``type``, ``required``, ``properties``, ``items``, ``enum``, ``const``,
``pattern``). The subset is deliberately dependency-free; anything richer
should be validated with an external ``jsonschema`` implementation against
the same schema files.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

SCHEMA_IDS = ("req/v1", "artifact/v1")

_SCHEMA_FILES = {
    "req/v1": "req-v1.schema.json",
    "artifact/v1": "artifact-v1.schema.json",
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


def _validate(node: object, schema: dict, path: str) -> None:
    if not isinstance(schema, dict):
        return
    if "const" in schema and node != schema["const"]:
        raise SchemaError(f"{path}: expected {schema['const']!r}, got {node!r}")
    if "enum" in schema and node not in schema["enum"]:
        raise SchemaError(f"{path}: {node!r} is not an allowed value")
    if "pattern" in schema and isinstance(node, str):
        if not re.fullmatch(schema["pattern"], node):
            raise SchemaError(f"{path}: {node!r} does not match {schema['pattern']!r}")
    if "type" in schema:
        _check_type(node, schema["type"], path)
    if isinstance(node, dict):
        for key in schema.get("required", []) or []:
            if key not in node:
                raise SchemaError(f"{path}: missing required key {key!r}")
        for key, subschema in (schema.get("properties", {}) or {}).items():
            if key in node:
                _validate(node[key], subschema, f"{path}.{key}")
    if isinstance(node, list):
        items = schema.get("items")
        if isinstance(items, dict):
            for index, item in enumerate(node):
                _validate(item, items, f"{path}[{index}]")


def validate(data: object, schema_id: str) -> None:
    """Validate ``data`` against a contract schema. Raises SchemaError."""
    _validate(data, load_schema(schema_id), "$")


def validate_final_req(doc: object) -> None:
    """Validate a final requirements document against ``req/v1``."""
    validate(doc, "req/v1")


def validate_manifest(manifest: object) -> None:
    """Validate an artifact manifest against ``artifact/v1``."""
    validate(manifest, "artifact/v1")
