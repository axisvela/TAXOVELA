# ArchHarness distribution health checks.
#
# Validates the cross-tool skill pack before shipping:
#   1. every skill has a valid Agent Skills frontmatter (name == directory)
#   2. every OpenCode agent uses the `permission` schema (not `permissions`)
#   3. all YAML in standards/rules/config parses
#   4. no placeholder clone URL or maintainer-local absolute paths leak into docs
#
# Usage:  python scripts/check_repo.py
# Exit code 1 on any failure. Runs locally and in CI.

from __future__ import annotations

import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / ".claude" / "skills"
AGENTS_DIR = ROOT / ".opencode" / "agents"
ERRORS: list[str] = []


def err(message: str) -> None:
    ERRORS.append(message)


def parse_frontmatter(text: str) -> dict | None:
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        parsed = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return None
    return parsed if isinstance(parsed, dict) else None


def check_skills() -> None:
    if not SKILLS_DIR.is_dir():
        err(f"missing skills directory: {SKILLS_DIR}")
        return
    for directory in sorted(SKILLS_DIR.iterdir()):
        if not directory.is_dir():
            continue
        skill_file = directory / "SKILL.md"
        if not skill_file.is_file():
            err(f"{directory.name}: missing SKILL.md")
            continue
        frontmatter = parse_frontmatter(skill_file.read_text(encoding="utf-8"))
        if frontmatter is None:
            err(f"{skill_file}: missing or invalid YAML frontmatter")
            continue
        if frontmatter.get("name") != directory.name:
            err(f"{skill_file}: frontmatter name {frontmatter.get('name')!r} != directory {directory.name!r}")
        if not frontmatter.get("description"):
            err(f"{skill_file}: missing description")


def check_agents() -> None:
    if not AGENTS_DIR.is_dir():
        err(f"missing agents directory: {AGENTS_DIR}")
        return
    for agent_file in sorted(AGENTS_DIR.glob("*.md")):
        frontmatter = parse_frontmatter(agent_file.read_text(encoding="utf-8"))
        if frontmatter is None:
            err(f"{agent_file}: missing or invalid YAML frontmatter")
            continue
        if "permissions" in frontmatter:
            err(f"{agent_file}: uses `permissions:` — schema requires `permission:`")
        if "permission" not in frontmatter:
            err(f"{agent_file}: missing `permission:` block")


def check_yaml_parses() -> None:
    roots = [
        ROOT / "config.yaml",
        ROOT / ".archharness" / "workspace.yaml",
        ROOT / "standards",
        SKILLS_DIR / "arch-validate" / "rules",
    ]
    for root in roots:
        files: list[pathlib.Path] = []
        if root.is_file():
            files = [root]
        elif root.is_dir():
            files = sorted(root.rglob("*.yaml"))
        for path in files:
            try:
                yaml.safe_load(path.read_text(encoding="utf-8"))
            except yaml.YAMLError as exc:
                err(f"{path}: invalid YAML ({exc})")


def check_no_placeholder_or_local_paths() -> None:
    forbidden = ["your-org", r"D:\project\ea-harness", r"D:\profile", "C:\\Users\\"]
    scan_files = [
        ROOT / "README.md",
        ROOT / "AGENTS.md",
        ROOT / "CLAUDE.md",
        ROOT / "ARCHITECTURE.md",
        ROOT / "config.yaml",
    ]
    for path in scan_files:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in forbidden:
            if token in text:
                err(f"{path}: contains forbidden token {token!r}")


def main() -> int:
    check_skills()
    check_agents()
    check_yaml_parses()
    check_no_placeholder_or_local_paths()

    if ERRORS:
        print(f"check_repo: {len(ERRORS)} problem(s) found:", file=sys.stderr)
        for error in ERRORS:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print("check_repo: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
