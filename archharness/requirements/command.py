#!/usr/bin/env python3
"""
req_reader.py — Main CLI: run one or more readers and merge into a single req.yaml.

Usage:
    # Single source
    python req_reader.py --diagram old-arch.drawio -o req-MyProject.yaml

    # Multiple sources merged
    python req_reader.py \\
        --diagram old-arch.drawio \\
        --doc requirements-brief.pdf \\
        --api servicenow --app-id OMS-001 \\
        -o req-MyProject.yaml --report gap-report.md

    # All sources
    python req_reader.py \\
        --diagram arch.png arch.d2 \\
        --doc brief.docx spec.md \\
        --csv cmdb_export.csv \\
        -o req.yaml --report gaps.md

Environment variables:
    ANTHROPIC_API_KEY      — required for PNG vision and document LLM extraction
    SERVICENOW_URL         — ServiceNow instance URL
    SERVICENOW_USER        — ServiceNow username
    SERVICENOW_PASSWORD    — ServiceNow password
    CMDB_URL               — Generic CMDB URL
    CMDB_TOKEN             — Generic CMDB bearer token
"""

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

from .from_diagram import parse_diagram
from .from_document import parse_document
from .from_api import fetch_from_api, fetch_from_csv
from .merger import merge_partial_reqs
from .normalizer import partial_req_to_yaml
from ..workspace import discover_project, get_project


def main(argv: list[str] | None = None) -> int:
    """Run the readers and merge. Returns a process-style exit code (no sys.exit)."""
    parser = argparse.ArgumentParser(
        description="Extract and merge requirements from multiple sources",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--diagram", nargs="*", default=[],
                        help="Architecture diagram files (.drawio/.d2/.yaml/.png/.jpg)")
    parser.add_argument("--doc", nargs="*", default=[],
                        help="Document files (.pdf/.docx/.md/.txt)")
    parser.add_argument("--csv", default=None,
                        help="CMDB CSV export file")
    parser.add_argument("--api", default=None,
                        choices=["servicenow", "generic"],
                        help="Fetch from CMDB API")
    parser.add_argument("--app-id", nargs="*", default=[],
                        help="Application IDs to fetch from CMDB")
    parser.add_argument("-o", "--output", default=None,
                        help="Output merged req.yaml file")
    parser.add_argument("--report", default=None,
                        help="Gap report output file (default: gap-report.md)")
    parser.add_argument("--partial-dir", default=None,
                        help="Directory to save intermediate partial-req files (for debugging)")
    parser.add_argument("--manifest", default=None,
                        help="Write an artifact/v1 provenance manifest (JSON) for the output")
    parser.add_argument("--workspace", default=None, help="ArchHarness workspace root")
    parser.add_argument("--project", default=None, help="Project ID (defaults to workspace default)")
    args = parser.parse_args(argv)

    context = get_project(args.workspace, args.project) if (args.workspace or args.project) else discover_project()
    if context:
        context.ensure_dirs()
        args.diagram = [str(context.resolve_input(p)) for p in args.diagram]
        args.doc = [str(context.resolve_input(p)) for p in args.doc]
        if args.csv:
            args.csv = str(context.resolve_input(args.csv))
        args.output = str(context.resolve_output(args.output or "req-output.yaml", "requirements"))
        args.report = str(context.resolve_output(args.report or "gap-report.md", "requirements"))
        if args.partial_dir:
            args.partial_dir = str(context.resolve_output(args.partial_dir, "requirements"))
    else:
        args.output = args.output or "req-output.yaml"

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    if args.partial_dir:
        Path(args.partial_dir).mkdir(parents=True, exist_ok=True)

    class _WriteError(OSError):
        pass

    class _InputError(ValueError):
        pass

    def _fail_input(message: str) -> None:
        print(f"ERROR: {message}", file=sys.stderr)
        raise _InputError(message)

    def _write_text(path: str, content: str, label: str) -> None:
        from ..files import atomic_write_text

        try:
            atomic_write_text(path, content)
        except OSError as exc:
            print(f"ERROR: Could not write {label} {path}: {exc}", file=sys.stderr)
            raise _WriteError(str(path)) from exc

    def _run_readers(partial_dir: str) -> list[str]:
        collected: list[str] = []
        # ── Diagram reader ────────────────────────────────────────────────────
        for i, diagram_path in enumerate(args.diagram or []):
            print(f"📐 Reading diagram: {diagram_path}")
            try:
                req = parse_diagram(diagram_path)
            except (FileNotFoundError, ValueError) as exc:
                _fail_input(f"Cannot read diagram {diagram_path}: {exc}")
            out = partial_req_to_yaml(req)
            pfile = os.path.join(partial_dir, f"partial-diagram-{i+1}.yaml")
            _write_text(pfile, out, "partial requirements")
            collected.append(pfile)
            print(f"  → {len(req.components)} components, {len(req.interactions)} interactions extracted")

        # ── Document reader ───────────────────────────────────────────────────
        for i, doc_path in enumerate(args.doc or []):
            print(f"📄 Reading document: {doc_path}")
            try:
                req = parse_document(doc_path)
            except (FileNotFoundError, ValueError) as exc:
                _fail_input(f"Cannot read document {doc_path}: {exc}")
            out = partial_req_to_yaml(req)
            pfile = os.path.join(partial_dir, f"partial-doc-{i+1}.yaml")
            _write_text(pfile, out, "partial requirements")
            collected.append(pfile)
            print(f"  → {len(req.applications)} applications, {len(req.components)} components extracted")

        # ── CSV import ────────────────────────────────────────────────────────
        if args.csv:
            print(f"📊 Reading CSV: {args.csv}")
            try:
                req = fetch_from_csv(args.csv)
            except (FileNotFoundError, ValueError) as exc:
                _fail_input(f"Cannot read CSV {args.csv}: {exc}")
            out = partial_req_to_yaml(req)
            pfile = os.path.join(partial_dir, "partial-csv.yaml")
            _write_text(pfile, out, "partial requirements")
            collected.append(pfile)
            print(f"  → {len(req.applications)} applications from CSV")

        # ── CMDB API ──────────────────────────────────────────────────────────
        if args.api:
            print(f"🔌 Fetching from CMDB API ({args.api})")
            try:
                req = fetch_from_api(args.api, args.app_id)
            except (ValueError, OSError) as exc:
                _fail_input(f"CMDB fetch failed: {exc}")
            out = partial_req_to_yaml(req)
            pfile = os.path.join(partial_dir, "partial-api.yaml")
            _write_text(pfile, out, "partial requirements")
            collected.append(pfile)
            print(f"  → {len(req.applications)} applications from API")
            if req.gaps:
                print(f"  ⚠ {req.gaps[0]}")
        return collected

    def _finalize(partial_files: list[str]) -> int:
        if not partial_files:
            print("No input sources specified. Use --diagram, --doc, --csv, or --api.")
            parser.print_help()
            return 1

        # ── Merge ─────────────────────────────────────────────────────────
        print(f"🔀 Finalizing {len(partial_files)} source(s)...")
        try:
            merged_yaml, gap_report, gaps = merge_partial_reqs(partial_files)
        except (ValueError, OSError) as exc:
            print(f"ERROR: Requirements merge failed: {exc}", file=sys.stderr)
            return 1

        _write_text(args.output, merged_yaml, "final requirements")
        print(f"✓ Final requirements: {args.output}")

        if args.manifest:
            from archharness import __version__ as _cli_version
            from archharness.artifacts import make_manifest
            inputs = list(args.diagram or []) + list(args.doc or [])
            if args.csv:
                inputs.append(args.csv)
            if args.api:
                inputs.append(f"api:{args.api}")
            manifest = make_manifest(
                artifact_id=f"req-{Path(args.output).stem}",
                artifact_type="requirements",
                schema="req/v1",
                path=args.output,
                project_root=context.project_root if context else None,
                producer=f"archharness/{_cli_version}",
                input_artifacts=inputs,
            )
            _write_text(args.manifest, json.dumps(manifest, indent=2), "artifact manifest")
            print(f"✓ Artifact manifest: {args.manifest}")

        report_path = args.report or "gap-report.md"
        _write_text(report_path, gap_report, "gap report")
        print(f"✓ Gap report: {report_path}")

        n_critical = len(gaps["critical"])
        n_conflicts = len(gaps["conflicts"])
        if n_critical == 0 and n_conflicts == 0:
            print("  ✓ All critical fields present. Ready for arch-design.")
        else:
            print(f"  ⚠ {n_critical} critical gap(s), {n_conflicts} conflict(s) — see {report_path}")
            print("  Run /arch-requirements to fill remaining gaps via interview.")
        return 0

    try:
        if args.partial_dir:
            # Explicit --partial-dir keeps intermediates for debugging.
            return _finalize(_run_readers(args.partial_dir))
        with tempfile.TemporaryDirectory(prefix="archharness-req-") as tmpdir:
            return _finalize(_run_readers(tmpdir))
    except _WriteError:
        return 2
    except _InputError:
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
