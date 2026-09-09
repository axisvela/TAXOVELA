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
    (project_root / "README.md").write_text(
        f"# {name or project_id}\n\nArchHarness project ID: `{project_id}`.\n",
        encoding="utf-8",
    )

    if make_default or not metadata.get("default_project"):
        metadata["default_project"] = project_id
        (root / WORKSPACE_DIR / WORKSPACE_FILE).write_text(
            yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True), encoding="utf-8"
        )
    return get_project(root, project_id)


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
