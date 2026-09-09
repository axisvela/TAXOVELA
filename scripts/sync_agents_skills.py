# Sync the canonical skills (.claude/skills) into the Codex discovery
# directory (.agents/skills). Keeps one content source; the mirror exists so
# Codex (and newer Cursor/Copilot builds) discover the skills automatically.
#
# Usage:
#   python scripts/sync_agents_skills.py          # write mirror
#   python scripts/sync_agents_skills.py --check   # fail if mirror is stale

from __future__ import annotations

import argparse
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / ".claude" / "skills"
MIRROR = ROOT / ".agents" / "skills"


def _relative_files(directory: pathlib.Path) -> list[pathlib.Path]:
    return sorted(p.relative_to(directory) for p in directory.rglob("*") if p.is_file())


def sync(check: bool = False) -> int:
    if not SOURCE.is_dir():
        print(f"sync: source not found: {SOURCE}", file=sys.stderr)
        return 1

    source_files = _relative_files(SOURCE)
    if check:
        if not MIRROR.is_dir():
            print("sync --check: .agents/skills mirror missing (run sync first)", file=sys.stderr)
            return 1
        mirror_files = _relative_files(MIRROR)
        problems: list[str] = []
        if source_files != mirror_files:
            missing = [str(f) for f in source_files if f not in mirror_files]
            extra = [str(f) for f in mirror_files if f not in source_files]
            if missing:
                problems.append("missing from mirror: " + ", ".join(missing))
            if extra:
                problems.append("extra in mirror: " + ", ".join(extra))
        else:
            for rel in source_files:
                if (SOURCE / rel).read_bytes() != (MIRROR / rel).read_bytes():
                    problems.append(f"content drift: {rel}")
        if problems:
            for problem in problems:
                print(f"sync --check: {problem}", file=sys.stderr)
            print("Run: python scripts/sync_agents_skills.py", file=sys.stderr)
            return 1
        print("sync --check: .agents/skills is up to date")
        return 0

    # Write mode: mirror every file, prune anything no longer in the source.
    MIRROR.mkdir(parents=True, exist_ok=True)
    for rel in source_files:
        target = MIRROR / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SOURCE / rel, target)
    for stale in _relative_files(MIRROR):
        if stale not in source_files:
            (MIRROR / stale).unlink()
    print(f"sync: {len(source_files)} file(s) mirrored to {MIRROR}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify mirror without writing")
    args = parser.parse_args()
    raise SystemExit(sync(check=args.check))
