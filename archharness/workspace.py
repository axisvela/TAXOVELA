"""Workspace discovery, project initialization, and path resolution."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


WORKSPACE_DIR = ".archharness"
WORKSPACE_FILE = "workspace.yaml"
PROJECT_FILE = "project.yaml"
PROJECT_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


@dataclass(frozen=True)
class ProjectContext:
    workspace_root: Path
    project_id: str
    project_root: Path
    config_path: Path
    input_path: Path
    working_path: Path
    output_path: Path

    def ensure_dirs(self) -> None:
        for path in (self.input_path, self.working_path, self.output_path):
            path.mkdir(parents=True, exist_ok=True)

    def resolve_input(self, value: str | Path) -> Path:
        path = Path(value)
        if path.is_absolute() or path.exists():
            return path.resolve()
        return (self.input_path / path).resolve()

    def resolve_output(self, value: str | Path, category: str | None = None) -> Path:
        path = Path(value)
        if path.is_absolute():
            return path
        base = self.output_path / category if category else self.output_path
        return (base / path).resolve()


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        value = yaml.safe_load(stream) or {}
    if not isinstance(value, dict):
        raise ValueError(f"Expected a YAML mapping in {path}")
    return value


def find_workspace(start: str | Path | None = None) -> Path | None:
    current = Path(start or Path.cwd()).resolve()
    if current.is_file():
        current = current.parent
    for directory in (current, *current.parents):
        if (directory / WORKSPACE_DIR / WORKSPACE_FILE).is_file():
            return directory
    return None


def load_workspace(workspace: str | Path | None = None) -> tuple[Path, dict[str, Any]]:
    root = Path(workspace).resolve() if workspace else find_workspace()
    if root is None:
        raise FileNotFoundError(
            "ArchHarness workspace not found. Run 'archharness init-workspace' first."
        )
    metadata_dir = root / WORKSPACE_DIR
    config_path = metadata_dir / WORKSPACE_FILE
    if not config_path.is_file():
        metadata_dir.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            yaml.safe_dump(
                {"schema_version": 1, "default_project": None, "projects_dir": "./projects"},
                sort_keys=False,
                allow_unicode=True,
            ),
            encoding="utf-8",
        )
    return root, _read_yaml(config_path)


def validate_project_id(project_id: str) -> str:
    if not PROJECT_ID_PATTERN.fullmatch(project_id):
        raise ValueError(
            "Project ID must start with a lowercase letter or digit and contain only "
            "lowercase letters, digits, '-' or '_' (maximum 64 characters)."
        )
    return project_id


def init_workspace(root: str | Path, force: bool = False) -> Path:
    root_path = Path(root).resolve()
    metadata_dir = root_path / WORKSPACE_DIR
    metadata_path = metadata_dir / WORKSPACE_FILE
    if metadata_path.exists() and not force:
        raise FileExistsError(f"Workspace already exists: {metadata_path}")
    metadata_dir.mkdir(parents=True, exist_ok=True)
    (root_path / "projects").mkdir(parents=True, exist_ok=True)
    metadata = {
        "schema_version": 1,
        "default_project": None,
        "projects_dir": "./projects",
    }
    metadata_path.write_text(
        yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    return metadata_path


def init_project(
    workspace: str | Path,
    project_id: str,
    name: str | None = None,
    platform: str = "unspecified",
    classification: str = "internal",
    make_default: bool = False,
) -> ProjectContext:
    project_id = validate_project_id(project_id)
    root, metadata = load_workspace(workspace)
    projects_dir = (root / metadata.get("projects_dir", "./projects")).resolve()
    project_root = projects_dir / project_id
    config_path = project_root / PROJECT_FILE
    if config_path.exists():
        raise FileExistsError(f"Project already exists: {project_id}")

    for relative in (
        "input/documents",
        "input/diagrams",
        "input/api",
        "input/requirements",
        "working",
        "output/requirements",
        "output/designs",
        "output/diagrams",
        "output/validation",
        "output/reports",
    ):
        (project_root / relative).mkdir(parents=True, exist_ok=True)
    for top_level in ("input", "working", "output"):
        (project_root / top_level / ".gitkeep").touch()

    project_config = {
        "schema_version": 1,
        "project": {
            "id": project_id,
            "name": name or project_id,
            "platform": platform,
            "data_classification": classification,
        },
        "paths": {"input": "./input", "working": "./working", "output": "./output"},
    }
    config_path.write_text(
        yaml.safe_dump(project_config, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    scaffold_project_inputs(project_root, project_id, name or project_id,
                           platform, classification)

    if make_default or not metadata.get("default_project"):
        metadata["default_project"] = project_id
        (root / WORKSPACE_DIR / WORKSPACE_FILE).write_text(
            yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True), encoding="utf-8"
        )
    return get_project(root, project_id)


#: One placeholder entity per registry table, so a new project starts from a
#: registry that parses and cites cleanly instead of a wall of checker errors.
_SCAFFOLD_ROWS = {
    "R1 — Infra nodes": (
        "| 编号 | 参考图原名 | node_kind | infra_type | network_type | 父节点 | 位置/国家 | 文档用名 | 备注 |",
        "|------|-----------|-----------|------------|--------------|--------|-----------|----------|------|",
        "| INF-01 | Example data center | data_center | private_cloud | prod_network | - | TBD | example-dc | replace with the real location |",
    ),
    "R2 — Systems": (
        "| 编号 | 参考图原名 | type | owner | vendor | 文档用名 | 备注 |",
        "|------|-----------|------|-------|--------|----------|------|",
        "| APP-01 | Example application | new | org_it | - | example-app | replace with the real system |",
    ),
    "R3 — Components / services": (
        "| 编号 | 参考图原名 | 所属系统 | 子系统 | kind | layer | component_role | 静态加密 | 文档用名 | 备注 |",
        "|------|-----------|----------|--------|------|-------|----------------|----------|----------|------|",
        "| CMP-01 | Example service | APP-01 | - | service | be | backend_service | - | example-service | replace with the real component |",
    ),
    "R4 — Deployments": (
        "| 编号 | 参考图原名 | 组件 | 环境 | deployment_type | location_type | infra 节点 | runtime_type | 实例数 | 文档用名 | 备注 |",
        "|------|-----------|------|------|-----------------|---------------|-----------|--------------|--------|----------|------|",
        "| DEP-01 | Example deployment | CMP-01 | prod | private_cloud | data_center | INF-01 | container | 2 | example-deploy | replace with the real placement |",
    ),
    "R5 — Component flows": (
        "| 编号 | 参考图原名 | 发起组件 | 提供组件 | protocol | port | auth_method | 加密 | 跨境 | via | 备注 |",
        "|------|-----------|----------|----------|----------|------|-------------|------|------|-----|------|",
        "| FLOW-01 | user -> service | internet | CMP-01 | HTTPS | 443 | OAuth2_ClientCredentials | TLS1.3 | 否 | INF-01 | replace with the real flow |",
    ),
    "R6 — Infra network links": (
        "| 编号 | 参考图原名 | 源 infra | 目标 infra | method | 带宽 | 加密 | 管理方 | 备注 |",
        "|------|-----------|----------|------------|--------|------|------|--------|------|",
    ),
    "R7 — Auth": (
        "| 编号 | 参考图原名 | subject | 适用入口 | auth_server | protocol | authorization | MFA | 备注 |",
        "|------|-----------|---------|----------|-------------|----------|---------------|-----|------|",
        "| AUTH-01 | Example sign-in | user | CMP-01 | INF-01 | OIDC | RBAC | 是 | replace with the real identity provider |",
    ),
}


def scaffold_project_inputs(project_root: Path, project_id: str, name: str,
                            platform: str, classification: str) -> list[Path]:
    """Write the starter inputs a new project needs for its first pipeline run.

    The files are deliberately valid: the registry parses, the prompt cites
    every in-scope row, and the README lists the commands. A new team can run
    the pipeline end to end, then replace the placeholders with real content.
    """
    written: list[Path] = []

    registry = project_root / "input" / "systems-registry.md"
    if not registry.exists():
        lines = [
            f"# Systems Registry — {name}",
            "",
            "Single source of truth for every system / service name in this project.",
            "",
            "- **参考图不做脱敏**：`input/diagrams/` 下的参考图保留原名。",
            "- **文档只引用编号**：`prompt.md`、`documents/`、`README.md`、`config.yaml`",
            "  中所有系统/服务均以类型化编号引用（`INF-` 基础设施、`APP-` 系统、",
            "  `CMP-` 组件，以及 `DEP`/`FLOW`/`LNK`/`AUTH` 派生层），不直接写名字。",
            "- **唯一具名文件**：本注册表是唯一出现具名实体的文件。",
            "- **范围标记**：默认全部纳入设计范围；有意不纳入的行，在「备注」列写上 `OUT-OF-SCOPE`。",
            "",
            "Replace every example row below with the real inventory.",
            "",
        ]
        for title, rows in _SCAFFOLD_ROWS.items():
            lines += [f"## {title}", ""] + list(rows) + [""]
        registry.write_text("\n".join(lines), encoding="utf-8")
        written.append(registry)

    prompt = project_root / "input" / "prompt.md"
    if not prompt.exists():
        prompt.write_text(
            f"""# One-shot prompt — {name}

> Codes-only prompt. Every system/service is referenced by a typed code
> (`INF-` infra · `APP-` systems · `CMP-` components · the `DEP`/`FLOW`/`LNK`/
> `AUTH` derived layers), resolved through `input/systems-registry.md` (include
> that registry as context when supplying this prompt to an agent). No literal
> system names appear outside the registry.

Design the technical architecture for {name}. Platform: {platform}.
Data classification: {classification}.

Systems and infra in scope: APP-01; INF-01; CMP-01.

Requirements:

1. **Location**: where each component runs, and which network zone it sits in.
2. **Components**: the technical components, their runtime, and their owner.
3. **Integrations**: every communication path with its protocol and
   authentication method, and the mediator it passes through.
4. **Data**: what is stored where, its classification, and how it is encrypted.
5. **Open items**: what is still TBD and who owns it.
""",
            encoding="utf-8")
        written.append(prompt)

    readme = project_root / "README.md"
    if not readme.exists():
        readme.write_text(
            f"""# {name}

ArchHarness project ID: `{project_id}`.

## Quick start

```bash
# 1. Describe the system in input/prompt.md and input/systems-registry.md
# 2. Check the installation and this project
archharness doctor
# 3. Gather requirements (Path A: coded prompt, Path B: a document)
archharness req --doc input/documents/requirements.md -o output/requirements/req.yaml
archharness req-validate output/requirements/req.yaml
# 4. Design and draw (arch-design skill), then check the model
archharness arch-check -i output/designs/blueprint.yaml
archharness diagram -i output/designs/blueprint.yaml \\
    -o output/diagrams/diagram-v1.drawio --png output/diagrams/diagram-v1.png
# 5. Validate (arch-validate skill), then gate
archharness enforce --validation output/validation/validate_result.json
archharness workflow status
```

See `standards/workflow.yaml` for the stage order and required artifacts;
`archharness workflow can <stage>` says whether a stage may start.
""",
            encoding="utf-8")
        written.append(readme)

    return written


def get_project(workspace: str | Path | None = None, project_id: str | None = None) -> ProjectContext:
    root, metadata = load_workspace(workspace)
    selected = project_id
    if not selected:
        projects_dir = (root / metadata.get("projects_dir", "./projects")).resolve()
        current = Path.cwd().resolve()
        try:
            relative = current.relative_to(projects_dir)
            if relative.parts and (projects_dir / relative.parts[0] / PROJECT_FILE).is_file():
                selected = relative.parts[0]
        except ValueError:
            pass
    selected = selected or metadata.get("default_project")
    if not selected:
        raise ValueError("No project selected and workspace has no default_project.")
    validate_project_id(selected)
    projects_dir = (root / metadata.get("projects_dir", "./projects")).resolve()
    project_root = projects_dir / selected
    config_path = project_root / PROJECT_FILE
    if not config_path.is_file():
        raise FileNotFoundError(f"Project not found: {selected}")
    raw = _read_yaml(config_path)
    paths = raw.get("paths", {})

    def resolve(value: str) -> Path:
        path = Path(value)
        return path if path.is_absolute() else (project_root / path).resolve()

    return ProjectContext(
        workspace_root=root,
        project_id=selected,
        project_root=project_root,
        config_path=config_path,
        input_path=resolve(paths.get("input", "./input")),
        working_path=resolve(paths.get("working", "./working")),
        output_path=resolve(paths.get("output", "./output")),
    )


def discover_project() -> ProjectContext | None:
    """Return the active project only when cwd is inside a project directory.

    Tools use this so that running inside `projects/<id>/` targets that
    project, while running at the workspace root keeps the legacy repo-root
    input/output behaviour. Explicit `--project` always wins.
    """
    root = find_workspace()
    if root is None:
        return None
    try:
        _, metadata = load_workspace(root)
    except (FileNotFoundError, ValueError):
        return None
    projects_dir = (root / metadata.get("projects_dir", "./projects")).resolve()
    try:
        relative = Path.cwd().resolve().relative_to(projects_dir)
    except ValueError:
        return None
    if not relative.parts:
        return None
    candidate = relative.parts[0]
    try:
        return get_project(root, candidate)
    except (FileNotFoundError, ValueError):
        return None


def list_projects(workspace: str | Path | None = None) -> list[str]:
    root, metadata = load_workspace(workspace)
    projects_dir = (root / metadata.get("projects_dir", "./projects")).resolve()
    if not projects_dir.exists():
        return []
    return sorted(
        path.name for path in projects_dir.iterdir() if (path / PROJECT_FILE).is_file()
    )
