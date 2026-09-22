#!/usr/bin/env python3
"""
arch_diagram_gen.py — Architecture YAML → multiple diagram formats

Usage:
    # draw.io (default, keep always)
    python arch_diagram_gen.py -i arch.yaml -o output.drawio
    python arch_diagram_gen.py -i arch.yaml -o output.drawio --png output.png

    # D2 (full 4-level nesting, version-control friendly)
    python arch_diagram_gen.py -i arch.yaml --d2 output.d2
    d2 output.d2 output.svg                    # render with d2 CLI
    d2 --layout=elk output.d2 output.svg       # better layout for deep nesting

    # PlantUML Deployment Diagram
    python arch_diagram_gen.py -i arch.yaml --puml output.puml
    plantuml -tsvg output.puml                 # render locally
    # or paste into https://www.plantuml.com/plantuml/

    # All formats at once
    python arch_diagram_gen.py -i arch.yaml \\
        -o output.drawio --png output.png \\
        --d2 output.d2 --puml output.puml

Requirements:
    pip install pyyaml matplotlib

Exit codes:  0 = success  |  1 = input error  |  2 = write error
"""

import argparse
import json
import os
import sys
import yaml
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

from ..workspace import discover_project, get_project


# ── PNG helpers (draw.io path) ────────────────────────────────────────────────

def _export_png_via_drawio_cli(drawio_path: str, png_path: str) -> bool:
    import subprocess
    candidates = [
        "drawio",
        "/usr/bin/drawio",
        "/usr/local/bin/drawio",
        "/Applications/draw.io.app/Contents/MacOS/draw.io",
        r"C:\Program Files\draw.io\draw.io.exe",
    ]
    for cmd in candidates:
        try:
            result = subprocess.run(
                [cmd, "--export", "--format", "png", "--output", png_path, drawio_path],
                capture_output=True, timeout=30
            )
            if result.returncode == 0:
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return False


def _export_png_via_d2_cli(d2_path: str, png_path: str) -> bool:
    """Render the PNG from D2 — its auto-layout routes edges around nodes."""
    import subprocess
    candidates = [
        "d2",
        r"C:\Program Files\D2\d2.exe",
        "/usr/local/bin/d2",
        "/usr/bin/d2",
    ]
    for cmd in candidates:
        try:
            result = subprocess.run(
                [cmd, "--layout", "elk", d2_path, png_path],
                capture_output=True, timeout=180,
            )
            if result.returncode == 0 and Path(png_path).is_file():
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return False


def _export_png_via_matplotlib(arch: dict, png_path: str) -> bool:
    try:
        from .png_renderer import render_png
        render_png(arch, png_path, dpi=120)
        return True
    except Exception as e:
        import traceback
        print(f"  PNG renderer error: {e}", file=sys.stderr)
        traceback.print_exc()
        return False


# ── Write helper ──────────────────────────────────────────────────────────────

def _write(path: str, content: str, label: str):
    from ..files import atomic_write_text

    try:
        atomic_write_text(path, content)
        print(f"✓ {label} written: {path}")
    except OSError as e:
        print(f"ERROR: Could not write {path}: {e}", file=sys.stderr)
        raise


# ── Main ─────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    """Convert Architecture YAML to diagram formats. Returns an exit code."""
    parser = argparse.ArgumentParser(
        description="Convert Architecture YAML to diagram formats"
    )
    parser.add_argument("-i", "--input",  required=True, help="Input YAML file or project input-relative path")
    parser.add_argument("-o", "--output", default=None,  help="Output .drawio file")
    parser.add_argument("--png",  default=None, help="Export PNG (draw.io CLI, D2 CLI or matplotlib)")
    parser.add_argument("--png-engine", default="auto", choices=["auto", "drawio", "d2", "matplotlib"],
                        help="Which renderer produces the PNG (auto: draw.io, then D2, then matplotlib)")
    parser.add_argument("--d2",   default=None, help="Output D2 file (.d2)")
    parser.add_argument("--puml", default=None, help="Output PlantUML file (.puml)")
    parser.add_argument("--routing-diagnostics", default=None,
                        help="Output routing diagnostics JSON")
    parser.add_argument("--workspace", default=None, help="ArchHarness workspace root")
    parser.add_argument("--project", default=None, help="Project ID (defaults to workspace default)")
    args = parser.parse_args(argv)

    context = get_project(args.workspace, args.project) if (args.workspace or args.project) else discover_project()
    if context:
        context.ensure_dirs()
        args.input = str(context.resolve_input(args.input))

        def project_output(value, suffix):
            if value:
                return str(context.resolve_output(value, "diagrams"))
            return str(context.resolve_output(Path(args.input).stem + suffix, "diagrams"))

        if args.output is not None:
            args.output = project_output(args.output, ".drawio")
        if args.png is not None:
            args.png = project_output(args.png, ".png")
        if args.d2 is not None:
            args.d2 = project_output(args.d2, ".d2")
        if args.puml is not None:
            args.puml = project_output(args.puml, ".puml")
        if args.routing_diagnostics is not None:
            args.routing_diagnostics = project_output(args.routing_diagnostics, ".json")

    # ── Load YAML ────────────────────────────────────────────────────────────
    if not os.path.exists(args.input):
        print(f"ERROR: Input file not found: {args.input}", file=sys.stderr)
        return 1
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"ERROR: Failed to parse YAML: {e}", file=sys.stderr)
        return 1

    arch = raw.get("arch", raw) if isinstance(raw, dict) else raw

    # ── draw.io ───────────────────────────────────────────────────────────────
    out_path = None
    routing_diagnostics: list[dict] = []
    if args.output or args.png or not (args.d2 or args.puml):
        from .generator import generate_drawio
        out_path = args.output or (
            str(context.resolve_output(Path(args.input).stem + ".drawio", "diagrams"))
            if context else os.path.splitext(args.input)[0] + ".drawio"
        )
        try:
            xml_str = generate_drawio(arch, routing_diagnostics)
        except Exception as e:
            import traceback
            print(f"ERROR: draw.io generation failed: {e}", file=sys.stderr)
            traceback.print_exc()
            return 1
        try:
            _write(out_path, xml_str, "draw.io")
        except OSError:
            return 2

    if args.routing_diagnostics:
        report = {
            "schema_version": "routing-diagnostics/v1",
            "diagram": {"id": arch.get("id", ""), "name": arch.get("name", "")},
            "summary": {
                "routes": len(routing_diagnostics),
                "fallbacks": sum(item["fallback"] for item in routing_diagnostics),
                "total_duration_ns": sum(item["duration_ns"] for item in routing_diagnostics),
            },
            "routes": routing_diagnostics,
        }
        try:
            _write(args.routing_diagnostics, json.dumps(report, ensure_ascii=False, indent=2),
                   "routing diagnostics")
        except OSError:
            return 2

    # ── D2 ────────────────────────────────────────────────────────────────────
    if args.d2:
        from .d2_generator import generate_d2
        try:
            d2_str = generate_d2(arch)
        except Exception as e:
            import traceback
            print(f"ERROR: D2 generation failed: {e}", file=sys.stderr)
            traceback.print_exc()
            return 1
        try:
            _write(args.d2, d2_str, "D2")
        except OSError:
            return 2
        print("  Render with: d2 --layout=elk " + args.d2 + " output.svg")

    # ── PNG (engine-selectable: D2 routes edges around nodes) ─────────────────
    if args.png:
        print(f"  Attempting PNG export → {args.png}")
        engine = args.png_engine
        exported = False
        if engine in ("auto", "drawio") and out_path:
            if _export_png_via_drawio_cli(out_path, args.png):
                print(f"  ✓ PNG via draw.io CLI: {args.png}")
                exported = True
        if not exported and engine in ("auto", "d2") and args.d2 and Path(args.d2).is_file():
            if _export_png_via_d2_cli(args.d2, args.png):
                print(f"  ✓ PNG via D2 CLI: {args.png}")
                exported = True
        if not exported and engine in ("auto", "matplotlib"):
            if _export_png_via_matplotlib(arch, args.png):
                print(f"  ✓ PNG via matplotlib: {args.png}")
                print("  ⚠  Install the draw.io or D2 CLI for routed edges.")
                exported = True
        if not exported:
            print("  ✗ PNG export failed. Install the drawio or d2 CLI, or: pip install matplotlib",
                  file=sys.stderr)
            return 2

    # ── PlantUML ──────────────────────────────────────────────────────────────
    if args.puml:
        from .plantuml_generator import generate_plantuml
        try:
            puml_str = generate_plantuml(arch)
        except Exception as e:
            import traceback
            print(f"ERROR: PlantUML generation failed: {e}", file=sys.stderr)
            traceback.print_exc()
            return 1
        try:
            _write(args.puml, puml_str, "PlantUML")
        except OSError:
            return 2
        print("  Render with: plantuml -tsvg " + args.puml)
        print("  Or paste at: https://www.plantuml.com/plantuml/")
        print("  Or import in draw.io: Extras → Edit Diagram → paste PlantUML")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
