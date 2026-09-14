"""One-shot sketches: tiny deterministic DSL -> Architecture model.

Grammar v1 (one statement per line, ``#`` starts a comment)::

    Browser -> API -> Redis -> PostgreSQL
    API -> PostgreSQL [JDBC fallback]

Rules:

- ``A -> B -> C`` expands to edges A->B and B->C.
- ``[label]`` after a node labels the edge arriving at that node.
  A label on the first node of a chain is rejected.
- The same node pair with two different labels is a conflict and fails.
- Node names may not contain ``->``, ``[``, ``]``.

The compiler emits a plain Architecture dict (single canvas region) that
flows into the existing renderers and reference validation unchanged, so
sketches get fail-closed reference checks for free. Natural-language
understanding (LLM) is a future front-end; it must target this same
compiler, never the renderers directly.
"""

from __future__ import annotations

import re

from .generator import generate_drawio, validate_architecture_refs

_EDGE_RE = re.compile(r"->")
_LABEL_RE = re.compile(r"^(?P<name>.*?)\s*\[(?P<label>[^\[\]]+)\]\s*$")


class SketchError(ValueError):
    """Raised for any sketch syntax or conflict error."""


def _strip_comment(line: str) -> str:
    return line.split("#", 1)[0].strip()


def _parse_node(token: str, first: bool, lineno: int) -> tuple[str, str | None]:
    token = token.strip()
    if not token:
        raise SketchError(f"line {lineno}: empty node next to '->'")
    match = _LABEL_RE.match(token)
    if match:
        name, label = match.group("name").strip(), match.group("label").strip()
        if not name:
            raise SketchError(f"line {lineno}: empty node name in {token!r}")
        if not label:
            raise SketchError(f"line {lineno}: empty label in {token!r}")
        if first:
            raise SketchError(f"line {lineno}: label on the first node of a chain: {token!r}")
        return name, label
    if "[" in token or "]" in token:
        raise SketchError(f"line {lineno}: malformed label in {token!r}")
    return token, None


def parse_sketch(text: str) -> tuple[list[str], list[tuple[str, str, str]]]:
    """Parse sketch DSL. Returns (nodes in first-seen order, edges).

    Each edge is ``(source, target, label)`` with ``""`` for unlabeled.
    Raises :class:`SketchError` on any syntax or label conflict.
    """
    nodes: list[str] = []
    seen: set[str] = set()
    edges: list[tuple[str, str, str]] = []
    edge_labels: dict[tuple[str, str], str] = {}

    def _node(name: str) -> None:
        if name not in seen:
            seen.add(name)
            nodes.append(name)

    lines = text.splitlines()
    if not any(_strip_comment(line) for line in lines):
        raise SketchError("empty sketch: describe at least one `A -> B` flow")

    for lineno, line in enumerate(lines, start=1):
        stripped = _strip_comment(line)
        if not stripped:
            continue
        parts = _EDGE_RE.split(stripped)
        if len(parts) < 2:
            raise SketchError(f"line {lineno}: expected at least one '->': {stripped!r}")
        chain: list[tuple[str, str | None]] = []
        for index, part in enumerate(parts):
            chain.append(_parse_node(part, first=index == 0, lineno=lineno))
        for (src, _), (tgt, label) in zip(chain, chain[1:]):
            _node(src)
            _node(tgt)
            key = (src, tgt)
            edge_label = label or ""
            if key in edge_labels and edge_labels[key] != edge_label:
                raise SketchError(
                    f"line {lineno}: conflicting labels for {src!r} -> {tgt!r}: "
                    f"{edge_labels[key]!r} vs {edge_label!r}"
                )
            edge_labels[key] = edge_label
            if (src, tgt, edge_label) not in edges:
                edges.append((src, tgt, edge_label))
    if not edges:
        raise SketchError("empty sketch: describe at least one `A -> B` flow")
    return nodes, edges


def _slug(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "sketch"


def render_sketch(
    text: str,
    output: str,
    *,
    title: str = "Sketch",
    view: str = "technical-deployment",
    png: str | None = None,
    model_yaml: str | None = None,
    workspace: str | None = None,
    project: str | None = None,
) -> int:
    """Compile sketch text and write draw.io (+model/PNG). Returns exit code.

    Shared core behind the ``sketch`` CLI command and :func:`archharness.api.run_sketch`.
    """
    import sys as _sys

    from ..workspace import discover_project, get_project
    from .viewpoints import require_supported

    try:
        require_supported(view)
        arch = compile_sketch(text, title=title)
    except (SketchError, ValueError) as exc:
        print(f"ERROR: {exc}", file=_sys.stderr)
        return 1

    try:
        context = get_project(workspace, project) if (workspace or project) else discover_project()
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=_sys.stderr)
        return 2
    if context is not None:
        context.ensure_dirs()
        out_path = str(context.resolve_output(output or "sketch.drawio", "diagrams"))
        png_path = str(context.resolve_output(png, "diagrams")) if png else None
        model_path = str(context.resolve_output(model_yaml, "diagrams")) if model_yaml else None
    else:
        out_path = output or "sketch.drawio"
        png_path = png
        model_path = model_yaml

    def _write(path: str, content: str, label: str) -> bool:
        from ..files import atomic_write_text

        try:
            atomic_write_text(path, content)
            print(f"✓ {label} written: {path}")
            return True
        except OSError as exc:
            print(f"ERROR: Could not write {path}: {exc}", file=_sys.stderr)
            return False

    try:
        xml = generate_drawio(arch)
    except ValueError as exc:
        print(f"ERROR: sketch render failed: {exc}", file=_sys.stderr)
        return 1
    if not _write(out_path, xml, "draw.io"):
        return 2
    if model_path:
        import yaml

        if not _write(model_path, yaml.safe_dump(arch, allow_unicode=True, sort_keys=False), "model"):
            return 2
    if png_path:
        from .command import _export_png_via_drawio_cli, _export_png_via_matplotlib

        print(f"  Attempting PNG export → {png_path}")
        if _export_png_via_drawio_cli(out_path, png_path):
            print(f"  ✓ PNG via draw.io CLI: {png_path}")
        elif _export_png_via_matplotlib(arch, png_path):
            print(f"  ✓ PNG via matplotlib: {png_path}")
        else:
            print("  ✗ PNG export failed. Install drawio CLI or: pip install matplotlib",
                  file=_sys.stderr)
            return 2
    return 0


def compile_sketch(text: str, title: str = "Sketch") -> dict:
    """Compile sketch DSL into an Architecture dict and validate references."""
    nodes, edges = parse_sketch(text)
    components = [{"id": _slug(name), "name": name, "type": "BE"} for name in nodes]
    by_name = {name: _slug(name) for name in nodes}
    interactions = [
        {"from": by_name[src], "to": by_name[tgt], "protocol": label or "calls"}
        for src, tgt, label in edges
    ]
    arch = {
        "id": _slug(title),
        "name": title,
        "platform": "sketch",
        "deployment": [{
            "id": "canvas",
            "type": "private_dc",
            "name": title,
            "network_zones": [{
                "id": "main",
                "type": "app_zone",
                "name": "Main",
                "components": components,
            }],
        }],
        "interactions": interactions,
    }
    validate_architecture_refs(arch)
    return arch
