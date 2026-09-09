#!/usr/bin/env python3
"""Assemble the Claude Code plugin skill tree.

Mirrors the canonical skills (.claude/skills) into plugins/archharness/skills so
the marketplace plugin stays in sync with one content source.

Usage:
    python scripts/sync_plugin.py          # write mirror
    python scripts/sync_plugin.py --check  # fail if mirror is stale
"""

from __future__ import annotations

import argparse
import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / ".claude" / "skills"
DEST = ROOT / "plugins" / "archharness" / "skills"


def _relative_files(directory: pathlib.Path) -> list[pathlib.Path]:
    return sorted(p.relative_to(directory) for p in directory.rglob("*") if p.is_file())


def sync(check: bool = False) -> int:
    if not SOURCE.is_dir():
        print(f"sync: source not found: {SOURCE}", file=sys.stderr)
        return 1
    source_files = _relative_files(SOURCE)
    if check:
        if not DEST.is_dir():
            print("sync --check: plugin skills mirror missing (run sync first)", file=sys.stderr)
            return 1
        dest_files = _relative_files(DEST)
        problems = []
        if source_files != dest_files:
            missing = [str(f) for f in source_files if f not in dest_files]
            extra = [str(f) for f in dest_files if f not in source_files]
            if missing:
                problems.append("missing from plugin: " + ", ".join(missing))
            if extra:
                problems.append("extra in plugin: " + ", ".join(extra))
        else:
            for rel in source_files:
                if (SOURCE / rel).read_bytes() != (DEST / rel).read_bytes():
                    problems.append(f"content drift: {rel}")
        if problems:
            for problem in problems:
                print(f"sync --check: {problem}", file=sys.stderr)
            print("Run: python scripts/sync_plugin.py", file=sys.stderr)
            return 1
        print("sync --check: plugins/archharness/skills is up to date")
        return 0

    DEST.mkdir(parents=True, exist_ok=True)
    for rel in source_files:
        target = DEST / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SOURCE / rel, target)
    for stale in _relative_files(DEST):
        if stale not in source_files:
            (DEST / stale).unlink()
    print(f"sync: {len(source_files)} file(s) mirrored to {DEST}")
    return 0


if __name__ == "__main__":
    import sys
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify mirror without writing")
    args = parser.parse_args()
    raise SystemExit(sync(check=args.check))
