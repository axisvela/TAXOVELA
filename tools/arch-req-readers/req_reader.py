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
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from from_diagram   import parse_diagram
from from_document  import parse_document
from from_api       import fetch_from_api, fetch_from_csv
from normalizer     import partial_req_to_yaml


def main():
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
    parser.add_argument("-o", "--output", default="req-output.yaml",
                        help="Output merged req.yaml file")
    parser.add_argument("--report", default=None,
                        help="Gap report output file (default: gap-report.md)")
    parser.add_argument("--partial-dir", default=None,
                        help="Directory to save intermediate partial-req files (for debugging)")
    args = parser.parse_args()

    partial_files = []
    tmpdir = tempfile.mkdtemp()

    # ── Diagram reader ────────────────────────────────────────────────────────
    for i, diagram_path in enumerate(args.diagram or []):
        print(f"📐 Reading diagram: {diagram_path}")
        req = parse_diagram(diagram_path)
        out = partial_req_to_yaml(req)
        pfile = os.path.join(args.partial_dir or tmpdir, f"partial-diagram-{i+1}.yaml")
        with open(pfile, "w", encoding="utf-8") as f:
            f.write(out)
        partial_files.append(pfile)
        n_comps = len(req.components)
        n_ints  = len(req.interactions)
        print(f"  → {n_comps} components, {n_ints} interactions extracted")

    # ── Document reader ───────────────────────────────────────────────────────
    for i, doc_path in enumerate(args.doc or []):
        print(f"📄 Reading document: {doc_path}")
        req = parse_document(doc_path)
        out = partial_req_to_yaml(req)
        pfile = os.path.join(args.partial_dir or tmpdir, f"partial-doc-{i+1}.yaml")
        with open(pfile, "w", encoding="utf-8") as f:
            f.write(out)
        partial_files.append(pfile)
        n_apps  = len(req.applications)
        n_comps = len(req.components)
        print(f"  → {n_apps} applications, {n_comps} components extracted")

    # ── CSV import ────────────────────────────────────────────────────────────
    if args.csv:
        print(f"📊 Reading CSV: {args.csv}")
        req = fetch_from_csv(args.csv)
        out = partial_req_to_yaml(req)
        pfile = os.path.join(args.partial_dir or tmpdir, "partial-csv.yaml")
        with open(pfile, "w", encoding="utf-8") as f:
            f.write(out)
        partial_files.append(pfile)
        print(f"  → {len(req.applications)} applications from CSV")

    # ── CMDB API ──────────────────────────────────────────────────────────────
    if args.api:
        print(f"🔌 Fetching from CMDB API ({args.api})")
        req = fetch_from_api(args.api, args.app_id)
        out = partial_req_to_yaml(req)
        pfile = os.path.join(args.partial_dir or tmpdir, "partial-api.yaml")
        with open(pfile, "w", encoding="utf-8") as f:
            f.write(out)
        partial_files.append(pfile)
        print(f"  → {len(req.applications)} applications from API")
        if req.gaps:
            print(f"  ⚠ {req.gaps[0]}")

    if not partial_files:
        print("No input sources specified. Use --diagram, --doc, --csv, or --api.")
        parser.print_help()
        sys.exit(1)

    # ── Merge ─────────────────────────────────────────────────────────────────
    if len(partial_files) == 1:
        # Single source: copy directly, still run gap analysis
        import shutil
        shutil.copy(partial_files[0], args.output)
        print(f"✓ Requirements written: {args.output} (single source, no merge needed)")
    else:
        print(f"🔀 Merging {len(partial_files)} sources...")
        from merger import merge_partial_reqs
        merged_yaml, gap_report, gaps = merge_partial_reqs(partial_files)

        with open(args.output, "w", encoding="utf-8") as f:
            f.write(merged_yaml)
        print(f"✓ Merged requirements: {args.output}")

        report_path = args.report or "gap-report.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(gap_report)
        print(f"✓ Gap report: {report_path}")

        n_critical = len(gaps["critical"])
        n_conflicts = len(gaps["conflicts"])
        if n_critical == 0 and n_conflicts == 0:
            print("  ✓ All critical fields present. Ready for arch-design.")
        else:
            print(f"  ⚠ {n_critical} critical gap(s), {n_conflicts} conflict(s) — see {report_path}")
            print("  Run /arch-requirements to fill remaining gaps via interview.")


if __name__ == "__main__":
    main()
