"""ArchHarness command-line interface."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

from . import __version__
from .paths import find_archharness_root, require_archharness_root
from .tool_runners import run_tool
from .workspace import (
    find_workspace,
    get_project,
    init_project,
    init_workspace,
    list_projects,
)

PASSTHROUGH_COMMANDS = ("diagram", "req", "validate-yaml")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="archharness",
        description="ArchHarness — enterprise architecture skills and multi-project workspace tools",
    )
    parser.add_argument("--version", action="version", version=f"ArchHarness {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    workspace = commands.add_parser("init-workspace", help="Initialize a multi-project workspace")
    workspace.add_argument("path", nargs="?", default=".")
    workspace.add_argument("--force", action="store_true")

    project = commands.add_parser("init-project", help="Create an isolated architecture project")
    project.add_argument("project_id")
    project.add_argument("--workspace", default=None)
    project.add_argument("--name")
    project.add_argument("--platform", default="unspecified")
    project.add_argument("--classification", default="internal")
    project.add_argument("--default", action="store_true", dest="make_default")

    listing = commands.add_parser("list-projects", help="List projects in a workspace")
    listing.add_argument("--workspace", default=None)

    doctor = commands.add_parser(
        "doctor", help="Check installation, workspace, and project configuration"
    )
    doctor.add_argument("--workspace", default=None)
    doctor.add_argument("--project", default=None)

    enforce = commands.add_parser(
        "enforce", help="Evaluate a validation result against the gate policy (deterministic)"
    )
    enforce.add_argument("--validation", required=True, help="validation/v1 result file (JSON or YAML)")
    enforce.add_argument("--policy", default=None, help="Gate policy file (default: standards/arch-gate-policy.yaml)")
    enforce.add_argument("--output", default=None, help="Write enforcement/v1 decision JSON here")

    commands.add_parser("root", help="Print the ArchHarness resource root directory")

    for name in PASSTHROUGH_COMMANDS:
        commands.add_parser(name, add_help=False, help=f"Run the {name} tool")
    return parser


def _print_doctor(workspace: str | None = None, project: str | None = None) -> int:
    try:
        root = require_archharness_root()
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    problems: list[str] = []
    # A repository checkout keeps skills under .claude/skills; the wheel ships
    # them as top-level skills/ plus config.yaml. config.yaml alone must not
    # imply a checkout, otherwise an installed package is misdiagnosed.
    is_repo = (root / ".claude" / "skills").is_dir()
    print(f"ArchHarness {__version__}")
    print(f"resource root: {root} ({'repository' if is_repo else 'installed package data'})")

    skills_dir = (root / ".claude" / "skills") if is_repo else (root / "skills")
    checks = [
        ("standards/", (root / "standards").is_dir()),
        ("schemas/", (root / "schemas").is_dir()),
        ("skills/", skills_dir.is_dir()),
        ("tools/arch-diagram-gen/", (root / "tools" / "arch-diagram-gen").is_dir()),
        ("tools/arch-req-readers/", (root / "tools" / "arch-req-readers").is_dir()),
    ]
    if is_repo:
        checks += [
            (".opencode/agents/", (root / ".opencode" / "agents").is_dir()),
            (".agents/skills/ (Codex mirror)", (root / ".agents" / "skills").is_dir()),
        ]
    for label, ok in checks:
        if ok:
            print(f"  [ok]  {label}")
        else:
            print(f"  [!!]  {label} — missing")
            problems.append(label)

    if not is_repo:
        print("  note  workspace/project features require a repository checkout")
    else:
        workspace_root = workspace or find_workspace()
        if workspace_root is None:
            print("  note  no workspace initialized — run `archharness init-workspace .`")
        else:
            print(f"  [ok]  workspace: {workspace_root}")
            try:
                context = get_project(workspace_root, project) if (workspace or project) else get_project()
            except (FileNotFoundError, ValueError) as exc:
                if workspace or project:
                    print(f"  [!!]  project selection failed — {exc}")
                    problems.append(f"project:{project or 'default'}")
                context = None
            if context is None:
                if not (workspace or project):
                    print("  note  no default project — run `archharness init-project <id> --default`")
            else:
                print(f"  [ok]  active project: {context.project_id}")
                print(f"        input={context.input_path}")
                print(f"        output={context.output_path}")

    if os.environ.get("ARCHHARNESS_HOME"):
        print(f"  env   ARCHHARNESS_HOME={os.environ['ARCHHARNESS_HOME']}")

    if problems:
        print("doctor: FAIL", file=sys.stderr)
        return 1
    print("doctor: OK")
    return 0


def _run_enforce(validation: str, policy: str | None, output: str | None) -> int:
    """Evaluate the gate policy. Returns 0 (PASS/WARN), 1 (BLOCK), 2 (error)."""
    import json

    from .enforcement import PolicyError, evaluate_files
    from .schemas import SchemaError

    if policy is None:
        try:
            root = require_archharness_root()
        except FileNotFoundError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        policy = str(root / "standards" / "arch-gate-policy.yaml")
    try:
        decision = evaluate_files(validation, policy)
    except (SchemaError, PolicyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"decision: {decision['decision']}")
    for reason in decision["reasons"]:
        print(f"  - {reason}")
    if output:
        try:
            Path(output).parent.mkdir(parents=True, exist_ok=True)
            with open(output, "w", encoding="utf-8") as handle:
                json.dump(decision, handle, indent=2)
        except OSError as exc:
            print(f"ERROR: Could not write {output}: {exc}", file=sys.stderr)
            return 2
        print(f"✓ Enforcement decision: {output}")
    return 0 if decision["decision"] in ("PASS", "WARN") else 1


def main(argv: list[str] | None = None) -> int:
    args_list = list(sys.argv[1:] if argv is None else argv)

    # Passthrough tools: forward everything after the command name.
    if args_list and args_list[0] in PASSTHROUGH_COMMANDS:
        return run_tool(args_list[0], args_list[1:])

    args = build_parser().parse_args(args_list)
    try:
        if args.command == "init-workspace":
            path = init_workspace(args.path, args.force)
            print(f"Workspace initialized: {path.parent.parent}")
        elif args.command == "init-project":
            workspace = args.workspace or find_workspace()
            context = init_project(
                workspace or Path.cwd(), args.project_id, args.name, args.platform,
                args.classification, args.make_default,
            )
            print(f"Project initialized: {context.project_root}")
        elif args.command == "list-projects":
            for project_id in list_projects(args.workspace):
                print(project_id)
        elif args.command == "root":
            print(require_archharness_root())
        elif args.command == "doctor":
            return _print_doctor(args.workspace, args.project)
        elif args.command == "enforce":
            return _run_enforce(args.validation, args.policy, args.output)
        return 0
    except (FileExistsError, FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
