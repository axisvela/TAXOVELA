"""Stable programmatic contract for ArchHarness capabilities.

This is the API that enterprise extensions, plugins, and automation should
program against. Functions take keyword arguments (never argv strings),
perform file I/O as documented, and return integer exit codes:

- ``0`` — success (outputs written);
- ``1`` — input error (missing/unparseable input, failed checks);
- ``2`` — write error (requested output could not be produced).
"""

from __future__ import annotations

from collections.abc import Sequence

from .diagrams import command as diagram_command
from .requirements import command as req_command
from . import yaml_validate as yaml_validate_module


def run_sketch(
    text: str,
    *,
    title: str = "Sketch",
    view: str = "technical-deployment",
    output: str,
    png: str | None = None,
    model_yaml: str | None = None,
    workspace: str | None = None,
    project: str | None = None,
) -> int:
    """Render a one-shot ``A -> B`` sketch into a diagram."""
    from .diagrams.sketch import render_sketch

    return render_sketch(
        text,
        output,
        title=title,
        view=view,
        png=png,
        model_yaml=model_yaml,
        workspace=workspace,
        project=project,
    )


def recommend_view(question: str) -> dict:
    """Recommend a viewpoint for a free-text question."""
    from .diagrams.viewpoints import recommend

    return recommend(question)


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
    """Extract and merge requirements into a final ``req/v2`` document."""
    argv: list[str] = []
    if diagram:
        argv += ["--diagram", *diagram]
    if doc:
        argv += ["--doc", *doc]
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
    return req_command.main(argv) or 0


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
    return diagram_command.main(argv) or 0


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
    return yaml_validate_module.main(argv) or 0
