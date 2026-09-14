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

    workflow = commands.add_parser(
        "workflow", help="Check and advance the artifact-gated pipeline state"
    )
    workflow_sub = workflow.add_subparsers(dest="workflow_command", required=True)
    workflow_sub.add_parser("status", help="Show per-stage readiness")
    can_parser = workflow_sub.add_parser("can", help="Exit 0 if a stage may start, 1 otherwise")
    can_parser.add_argument("stage", help="Stage id, e.g. design")
    record_parser = workflow_sub.add_parser("record", help="Record a manifest or decision under an artifact name")
    record_parser.add_argument("--name", required=True, help="Artifact name, e.g. req.yaml")
    record_parser.add_argument("--file", required=True, help="artifact/v1 or enforcement/v1 JSON document")
    complete_parser = workflow_sub.add_parser("complete", help="Mark a stage complete after gate checks")
    complete_parser.add_argument("stage", help="Stage id, e.g. design")
    for sub in (workflow, workflow_sub.choices["status"], workflow_sub.choices["can"],
                workflow_sub.choices["record"], workflow_sub.choices["complete"]):
        sub.add_argument("--workspace", default=None)
        sub.add_argument("--project", default=None)

    commands.add_parser("root", help="Print the ArchHarness resource root directory")

    commands.add_parser("plugins", help="List discovered plugins and their capabilities")

    sketch = commands.add_parser(
        "sketch", help="Render a one-shot 'A -> B' sketch into a diagram"
    )
    sketch.add_argument("text", nargs="?", default=None, help="Sketch text, e.g. 'Browser -> API -> DB'")
    sketch.add_argument("--from-file", default=None, help="Read sketch text from a file (or - for stdin)")
    sketch.add_argument("--title", default="Sketch", help="Diagram title")
    sketch.add_argument("-o", "--output", default=None, help="Output .drawio file")
    sketch.add_argument("--png", default=None, help="Export PNG alongside the draw.io file")
    sketch.add_argument("--yaml", default=None, dest="model_yaml", help="Save the compiled Architecture model YAML")
    sketch.add_argument("--view", default="technical-deployment", help="Viewpoint id (only supported views render)")
    sketch.add_argument("--workspace", default=None)
    sketch.add_argument("--project", default=None)

    view = commands.add_parser(
        "view", help="Recommend a viewpoint for a question"
    )
    view.add_argument("question", nargs="?", default="", help="What do you want to understand?")

    model = commands.add_parser(
        "model", help="Semantic model operations (diff, not pixels)"
    )
    model_sub = model.add_subparsers(dest="model_command", required=True)
    diff_parser = model_sub.add_parser("diff", help="Show the semantic change set between two model files")
    diff_parser.add_argument("before", help="Base Architecture YAML file")
    diff_parser.add_argument("after", help="Revised Architecture YAML file")
    apply_parser = model_sub.add_parser("apply", help="Apply a change set file to a model (dry-run by default)")
    apply_parser.add_argument("base", help="Base Architecture YAML file")
    apply_parser.add_argument("--changeset", required=True, help="Change set file (JSON or YAML with an `ops` list)")
    apply_parser.add_argument("-o", "--output", default=None, help="Output model file (required unless --dry-run)")
    apply_parser.add_argument("--dry-run", action="store_true", help="Print the summary without writing")

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
        from .files import atomic_write_text

        try:
            atomic_write_text(output, json.dumps(decision, indent=2))
        except OSError as exc:
            print(f"ERROR: Could not write {output}: {exc}", file=sys.stderr)
            return 2
        print(f"✓ Enforcement decision: {output}")
    return 0 if decision["decision"] in ("PASS", "WARN") else 1


def _print_plugins() -> int:
    from .plugins import PLUGIN_API_VERSION, discover_plugins

    print(f"plugin API: {PLUGIN_API_VERSION}")
    plugins = discover_plugins()
    if not plugins:
        print("  note  no plugins installed — extensions register via entry points")
        print("        [project.entry-points.\"archharness.plugins\"]")
        return 0
    for name in sorted(plugins):
        caps = ", ".join(plugins[name].capabilities)
        print(f"  [ok]  {name} (api {plugins[name].api_version}): {caps}")
    return 0


def _run_view(question: str) -> int:
    from .diagrams.viewpoints import recommend

    result = recommend(question)
    print(f"viewpoint: {result['viewpoint']}")
    print(f"supported: {'yes' if result['supported'] else 'no'}")
    print(f"reason: {result['reason']}")
    return 0


def _run_model(subcommand: str, args) -> int:
    import yaml

    from .changes import diff_arch, summarize

    if subcommand == "diff":
        models = []
        for path in (args.before, args.after):
            try:
                with open(path, encoding="utf-8") as handle:
                    doc = yaml.safe_load(handle)
            except OSError as exc:
                print(f"ERROR: cannot read {path}: {exc}", file=sys.stderr)
                return 2
            except yaml.YAMLError as exc:
                print(f"ERROR: invalid YAML {path}: {exc}", file=sys.stderr)
                return 1
            models.append(doc.get("arch", doc) if isinstance(doc, dict) else doc)
        lines = summarize(diff_arch(models[0], models[1]))
        if not lines:
            print("no semantic changes")
        for line in lines:
            print(line)
        return 0
    if subcommand == "apply":
        from .changes import ChangeError, apply_changeset

        try:
            with open(args.base, encoding="utf-8") as handle:
                base = yaml.safe_load(handle)
        except OSError as exc:
            print(f"ERROR: cannot read {args.base}: {exc}", file=sys.stderr)
            return 2
        except yaml.YAMLError as exc:
            print(f"ERROR: invalid YAML {args.base}: {exc}", file=sys.stderr)
            return 1
        try:
            with open(args.changeset, encoding="utf-8") as handle:
                changeset = yaml.safe_load(handle)
        except OSError as exc:
            print(f"ERROR: cannot read {args.changeset}: {exc}", file=sys.stderr)
            return 2
        except yaml.YAMLError as exc:
            print(f"ERROR: invalid change set {args.changeset}: {exc}", file=sys.stderr)
            return 1
        base = base.get("arch", base) if isinstance(base, dict) else base
        try:
            result = apply_changeset(base, changeset)
        except ChangeError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        for line in summarize(changeset):
            print(line)
        if args.dry_run:
            print("dry-run: model unchanged")
            return 0
        if not args.output:
            print("ERROR: --output is required unless --dry-run", file=sys.stderr)
            return 2
        from .files import atomic_write_text

        try:
            atomic_write_text(args.output, yaml.safe_dump(
                result, allow_unicode=True, sort_keys=False))
        except OSError as exc:
            print(f"ERROR: Could not write {args.output}: {exc}", file=sys.stderr)
            return 2
        print(f"✓ Model written: {args.output}")
        return 0
    print(f"ERROR: unknown model subcommand {subcommand!r}", file=sys.stderr)
    return 2


def _run_sketch(args) -> int:
    from .diagrams.sketch import render_sketch

    if args.from_file in (None, "") and not args.text:
        print("ERROR: provide sketch text or --from-file", file=sys.stderr)
        return 2
    if args.from_file == "-":
        text = sys.stdin.read()
    elif args.from_file:
        try:
            text = Path(args.from_file).read_text(encoding="utf-8")
        except OSError as exc:
            print(f"ERROR: cannot read {args.from_file}: {exc}", file=sys.stderr)
            return 1
    else:
        text = args.text or ""
    return render_sketch(
        text,
        args.output or "sketch.drawio",
        title=args.title,
        view=args.view,
        png=args.png,
        model_yaml=args.model_yaml,
        workspace=args.workspace,
        project=args.project,
    )


def _workflow_state_path(workspace: str | None, project: str | None) -> Path:
    from .workspace import discover_project, get_project
    from .workflow import STATE_FILENAME

    context = None
    if workspace or project:
        try:
            context = get_project(workspace, project)
        except (FileNotFoundError, ValueError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            raise SystemExit(2)
    else:
        context = discover_project()
    if context is not None:
        context.ensure_dirs()
        return context.working_path / STATE_FILENAME
    return Path.cwd() / STATE_FILENAME


def _run_workflow(subcommand: str, args) -> int:
    import json

    from .workflow import (
        WorkflowError,
        can_start,
        complete_stage,
        load_spec,
        load_state,
        record_artifact,
        save_state,
        status_rows,
    )

    try:
        spec = load_spec()
    except WorkflowError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    state_path = _workflow_state_path(args.workspace, args.project)
    try:
        state = load_state(state_path)
    except WorkflowError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if subcommand == "status":
        print(f"workflow state: {state_path}")
        for row in status_rows(state, spec):
            flag = "done" if row["completed"] else ("ready" if row["ready"] else "blocked")
            print(f"  [{flag:>7}] {row['stage']}")
            if row["missing"]:
                print(f"            missing: {', '.join(row['missing'])}")
            if row["blocked"]:
                print(f"            blocked: {row['blocked']}")
        return 0
    if subcommand == "can":
        try:
            ok, missing, blocked = can_start(args.stage, state, spec)
        except WorkflowError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        if ok:
            print(f"stage {args.stage!r} may start")
            return 0
        detail = f"missing: {', '.join(missing)}" if missing else blocked
        print(f"stage {args.stage!r} may not start ({detail})")
        return 1
    if subcommand == "record":
        try:
            doc = json.loads(Path(args.file).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            print(f"ERROR: cannot read {args.file}: {exc}", file=sys.stderr)
            return 2
        from .workspace import discover_project, get_project

        try:
            if args.workspace or args.project:
                context = get_project(args.workspace, args.project)
            else:
                context = discover_project()
        except (FileNotFoundError, ValueError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        base = context.project_root if context else Path(args.file).parent
        try:
            record_artifact(state, args.name, doc, base)
            save_state(state_path, state)
        except WorkflowError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        print(f"✓ Recorded {args.name} from {args.file}")
        return 0
    if subcommand == "complete":
        try:
            complete_stage(args.stage, state, spec)
            save_state(state_path, state)
        except WorkflowError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        print(f"✓ Stage complete: {args.stage}")
        return 0
    print(f"ERROR: unknown workflow subcommand {subcommand!r}", file=sys.stderr)
    return 2


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
        elif args.command == "plugins":
            return _print_plugins()
        elif args.command == "sketch":
            return _run_sketch(args)
        elif args.command == "view":
            return _run_view(args.question)
        elif args.command == "model":
            return _run_model(args.model_command, args)
        elif args.command == "doctor":
            return _print_doctor(args.workspace, args.project)
        elif args.command == "enforce":
            return _run_enforce(args.validation, args.policy, args.output)
        elif args.command == "workflow":
            return _run_workflow(args.workflow_command, args)
        return 0
    except (FileExistsError, FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
