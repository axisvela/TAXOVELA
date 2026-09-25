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
            # Store POSIX separators so a manifest recorded on Windows resolves
            # on Linux (and vice versa). A backslash path is a literal filename
            # on POSIX, which makes the recorded artifact unverifiable.
            stored = file_path.resolve().relative_to(Path(project_root).resolve()).as_posix()
        except ValueError:
            stored = file_path.as_posix()
    else:
        # No project root: keep the manifest portable rather than embedding a
        # machine-specific absolute path. Prefer a path relative to the working
        # directory; otherwise just the file name (callers can pass a base_dir to
        # verify_manifest to resolve it).
        try:
            stored = file_path.resolve().relative_to(Path.cwd().resolve()).as_posix()
        except (ValueError, OSError):
            stored = file_path.name
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


def _portable_path(raw: str) -> Path:
    """Resolve a recorded path on any platform.

    Manifests written before separators were normalised may carry Windows
    backslashes; on POSIX those are literal filename characters and the lookup
    fails. Forward slashes resolve on every platform.
    """
    return Path(str(raw).replace("\\", "/"))


def verify_manifest(manifest: dict, base_dir: str | Path | None = None) -> bool:
    """Recompute the hash and report whether the artifact is unchanged."""
    validate_manifest(manifest)
    path = _portable_path(manifest["path"])
    if base_dir is not None and not path.is_absolute():
        path = Path(base_dir) / path
    if not path.is_file():
        return False
    return sha256_file(path) == manifest["sha256"]


def check_manifest(manifest: dict, base_dir: str | Path | None = None) -> dict:
    """Return machine-readable evidence for an artifact integrity check."""
    try:
        validate_manifest(manifest)
    except Exception as exc:
        return {"valid": False, "reason": "invalid-manifest", "detail": str(exc)}
    path = _portable_path(manifest["path"])
    if base_dir is not None and not path.is_absolute():
        path = Path(base_dir) / path
    if not path.is_file():
        return {"valid": False, "reason": "missing-file", "path": str(path)}
    actual = sha256_file(path)
    if actual != manifest["sha256"]:
        return {"valid": False, "reason": "digest-mismatch", "path": str(path),
                "expected_sha256": manifest["sha256"], "actual_sha256": actual}
    return {"valid": True, "path": str(path), "sha256": actual}
