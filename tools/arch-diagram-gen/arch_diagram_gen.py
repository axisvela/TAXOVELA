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
import os
import sys
import yaml


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


def _export_png_via_matplotlib(arch: dict, png_path: str) -> bool:
    try:
        from png_renderer import render_png
        render_png(arch, png_path, dpi=120)
        return True
    except Exception as e:
        import traceback
        print(f"  PNG renderer error: {e}", file=sys.stderr)
        traceback.print_exc()
        return False


# ── Write helper ──────────────────────────────────────────────────────────────

def _write(path: str, content: str, label: str):
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✓ {label} written: {path}")
    except IOError as e:
        print(f"ERROR: Could not write {path}: {e}", file=sys.stderr)
        sys.exit(2)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Convert Architecture YAML to diagram formats"
    )
    parser.add_argument("-i", "--input",  required=True, help="Input YAML file")
    parser.add_argument("-o", "--output", default=None,  help="Output .drawio file")
    parser.add_argument("--png",  default=None, help="Export PNG (draw.io CLI or matplotlib)")
    parser.add_argument("--d2",   default=None, help="Output D2 file (.d2)")
    parser.add_argument("--puml", default=None, help="Output PlantUML file (.puml)")
    args = parser.parse_args()

    # ── Load YAML ────────────────────────────────────────────────────────────
    if not os.path.exists(args.input):
        print(f"ERROR: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"ERROR: Failed to parse YAML: {e}", file=sys.stderr)
        sys.exit(1)

    arch = raw.get("arch", raw) if isinstance(raw, dict) else raw

    # ── draw.io ───────────────────────────────────────────────────────────────
    if args.output or not (args.d2 or args.puml):
        from generator import generate_drawio
        out_path = args.output or (os.path.splitext(args.input)[0] + ".drawio")
        try:
            xml_str = generate_drawio(arch)
        except Exception as e:
            import traceback
            print(f"ERROR: draw.io generation failed: {e}", file=sys.stderr)
            traceback.print_exc()
            sys.exit(1)
        _write(out_path, xml_str, "draw.io")

        if args.png:
            print(f"  Attempting PNG export → {args.png}")
            if _export_png_via_drawio_cli(out_path, args.png):
                print(f"  ✓ PNG via draw.io CLI: {args.png}")
            elif _export_png_via_matplotlib(arch, args.png):
                print(f"  ✓ PNG via matplotlib: {args.png}")
                print("  ⚠  For full-fidelity PNG, install the draw.io desktop CLI.")
            else:
                print("  ✗ PNG export failed. Install drawio CLI or: pip install matplotlib",
                      file=sys.stderr)

    # ── D2 ────────────────────────────────────────────────────────────────────
    if args.d2:
        from d2_generator import generate_d2
        try:
            d2_str = generate_d2(arch)
        except Exception as e:
            import traceback
            print(f"ERROR: D2 generation failed: {e}", file=sys.stderr)
            traceback.print_exc()
            sys.exit(1)
        _write(args.d2, d2_str, "D2")
        print("  Render with: d2 --layout=elk " + args.d2 + " output.svg")

    # ── PlantUML ──────────────────────────────────────────────────────────────
    if args.puml:
        from plantuml_generator import generate_plantuml
        try:
            puml_str = generate_plantuml(arch)
        except Exception as e:
            import traceback
            print(f"ERROR: PlantUML generation failed: {e}", file=sys.stderr)
            traceback.print_exc()
            sys.exit(1)
        _write(args.puml, puml_str, "PlantUML")
        print("  Render with: plantuml -tsvg " + args.puml)
        print("  Or paste at: https://www.plantuml.com/plantuml/")
        print("  Or import in draw.io: Extras → Edit Diagram → paste PlantUML")


if __name__ == "__main__":
    main()
