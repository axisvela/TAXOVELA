"""Stable programmatic contract for ArchHarness capabilities.

This is the API that enterprise extensions, plugins, and automation should
program against. Functions take keyword arguments (never argv strings),
perform file I/O as documented, and return integer exit codes:

- ``0`` — success (outputs written);
- ``1`` — input error (missing/unparseable input, failed checks);
- ``2`` — write error (requested output could not be produced).

Transitional note: implementations currently delegate to the standalone
tools under ``tools/`` via :mod:`archharness.tool_runners`. Signatures here
are the stable contract; the delegation underneath will be replaced by
direct package calls as tool logic moves into the package.
"""

from __future__ import annotations

from collections.abc import Sequence

from .tool_runners import run_tool


def run_requirements(
    *,
    diagram: Sequence[str] = (),
    doc: Sequence[str] = (),
    csv: str | None = None,
    api: str | None = None,
    app_ids: Sequence[str] = (),
    output: str,
    report: str | None = None,
    manifest: str | None = None,
    partial_dir: str | None = None,
    workspace: str | None = None,
    project: str | None = None,
) -> int:
    """Extract and merge requirements into a final ``req/v1`` document."""
    argv: list[str] = []
    for path in diagram:
        argv += ["--diagram", path]
    for path in doc:
        argv += ["--doc", path]
    if csv is not None:
        argv += ["--csv", csv]
    if api is not None:
        argv += ["--api", api]
    if app_ids:
        argv += ["--app-id", *app_ids]
    argv += ["-o", output]
    if report is not None:
        argv += ["--report", report]
    if manifest is not None:
        argv += ["--manifest", manifest]
    if partial_dir is not None:
        argv += ["--partial-dir", partial_dir]
    if workspace is not None:
        argv += ["--workspace", workspace]
    if project is not None:
        argv += ["--project", project]
    return run_tool("req", argv)


def run_diagram(
    *,
    input: str,
    output: str | None = None,
    png: str | None = None,
    d2: str | None = None,
    puml: str | None = None,
    workspace: str | None = None,
    project: str | None = None,
) -> int:
    """Render an Architecture YAML file into diagram formats."""
    argv = ["-i", input]
    if output is not None:
        argv += ["-o", output]
    if png is not None:
        argv += ["--png", png]
    if d2 is not None:
        argv += ["--d2", d2]
    if puml is not None:
        argv += ["--puml", puml]
    if workspace is not None:
        argv += ["--workspace", workspace]
    if project is not None:
        argv += ["--project", project]
    return run_tool("diagram", argv)


def validate_yaml_files(
    paths: Sequence[str],
    *,
    strict: bool = False,
    quiet: bool = True,
) -> int:
    """Validate YAML files. Returns 0 when all files are valid."""
    argv = list(paths)
    if strict:
        argv.append("--strict")
    if quiet:
        argv.append("--quiet")
    return run_tool("validate-yaml", argv)
