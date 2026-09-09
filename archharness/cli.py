"""ArchHarness command-line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .workspace import find_workspace, get_project, init_project, init_workspace, list_projects


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="archharness", description="Manage ArchHarness workspaces")
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

    doctor = commands.add_parser("doctor", help="Check workspace and project configuration")
    doctor.add_argument("--workspace", default=None)
    doctor.add_argument("--project", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
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
        elif args.command == "doctor":
            context = get_project(args.workspace, args.project)
            context.ensure_dirs()
            print(f"OK workspace={context.workspace_root} project={context.project_id}")
            print(f"input={context.input_path}")
            print(f"working={context.working_path}")
            print(f"output={context.output_path}")
        return 0
    except (FileExistsError, FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
