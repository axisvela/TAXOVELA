"""Artifact manifests: provenance records for governed files.

A manifest binds an artifact file to its content hash, schema, producer,
and lineage. Workflow gates and reviews reference manifests, never bare
filenames, so a decision can always be traced to exact bytes.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from .schemas import validate_manifest


def sha256_file(path: str | Path) -> str:
    """Return the hex SHA-256 of a file's exact bytes."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def make_manifest(
    *,
    artifact_id: str,
    artifact_type: str,
    schema: str,
    path: str | Path,
    project_root: str | Path | None = None,
    model_version: str | None = None,
    producer: str | None = None,
    input_artifacts: list[str] | None = None,
) -> dict:
    """Build and schema-validate a manifest for an existing artifact file."""
    file_path = Path(path)
    if project_root is not None:
        try:
            stored = str(file_path.resolve().relative_to(Path(project_root).resolve()))
        except ValueError:
            stored = str(file_path)
    else:
        stored = str(file_path)
    manifest = {
        "schema_version": "artifact/v1",
        "id": artifact_id,
        "type": artifact_type,
        "schema": schema,
        "path": stored,
        "sha256": sha256_file(file_path),
        "model_version": model_version,
        "producer": producer,
        "produced_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "input_artifacts": list(input_artifacts or []),
    }
    validate_manifest(manifest)
    return manifest


def verify_manifest(manifest: dict, base_dir: str | Path | None = None) -> bool:
    """Recompute the hash and report whether the artifact is unchanged."""
    validate_manifest(manifest)
    path = Path(manifest["path"])
    if base_dir is not None and not path.is_absolute():
        path = Path(base_dir) / path
    if not path.is_file():
        return False
    return sha256_file(path) == manifest["sha256"]
