"""ArchHarness command-line interface."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

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

    commands.add_parser("root", help="Print the ArchHarness resource root directory")

    for name in PASSTHROUGH_COMMANDS:
        commands.add_parser(name, add_help=False, help=f"Run the {name} tool")
    return parser


def _print_doctor() -> int:
    try:
        root = require_archharness_root()
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    problems: list[str] = []
    print(f"ArchHarness {__version__}")
    print(f"resource root: {root}")

    checks = [
        ("standards/", (root / "standards").is_dir()),
        (".claude/skills/", (root / ".claude" / "skills").is_dir()),
        (".opencode/agents/", (root / ".opencode" / "agents").is_dir()),
        (".agents/skills/ (Codex mirror)", (root / ".agents" / "skills").is_dir()),
        ("tools/arch-diagram-gen/", (root / "tools" / "arch-diagram-gen").is_dir()),
        ("tools/arch-req-readers/", (root / "tools" / "arch-req-readers").is_dir()),
    ]
    for label, ok in checks:
        if ok:
            print(f"  [ok]  {label}")
        else:
            print(f"  [!!]  {label} — missing")
            problems.append(label)

    workspace = find_workspace()
    if workspace is None:
        print("  note  no workspace initialized — run `archharness init-workspace .`")
    else:
        print(f"  [ok]  workspace: {workspace}")
        try:
            context = get_project()
        except (FileNotFoundError, ValueError):
            context = None
        if context is None:
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
            return _print_doctor()
        return 0
    except (FileExistsError, FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
