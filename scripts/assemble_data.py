#!/usr/bin/env python3
"""Assemble the self-contained runtime data directory for wheel builds.

Copies the content that skills reference at runtime (tools/, standards/ and the
canonical skills tree) into ``archharness/data/`` so that a ``pip install`` of
this project ships a resource root usable from any working directory.

Usage:
    python scripts/assemble_data.py          # copy into archharness/data/
    python scripts/assemble_data.py --check  # verify data matches sources

The data directory is git-ignored and generated on demand before packaging.
"""

from __future__ import annotations

import argparse
import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "archharness" / "data"

# name -> source (relative to ROOT)
SOURCES = {
    "tools": ROOT / "tools",
    "standards": ROOT / "standards",
    "skills": ROOT / ".claude" / "skills",
    "config.example.yaml": ROOT / "config.yaml",
}


def _copy_tree(source: pathlib.Path, target: pathlib.Path) -> list[pathlib.Path]:
    if target.is_dir():
        shutil.rmtree(target)
    written: list[pathlib.Path] = []
    for path in source.rglob("*"):
        if not path.is_file():
            continue
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        relative = path.relative_to(source)
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
        written.append(relative)
    return written


def assemble(check: bool = False) -> int:
    DATA.mkdir(parents=True, exist_ok=True)
    if check:
        problems: list[str] = []
        for name, source in SOURCES.items():
            if source.is_dir():
                mirror = DATA / name
                if not mirror.is_dir():
                    problems.append(f"missing {mirror}")
                    continue
                source_files = {
                    p.relative_to(source)
                    for p in source.rglob("*")
                    if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
                }
                mirror_files = {
                    p.relative_to(mirror) for p in mirror.rglob("*") if p.is_file()
                }
                if source_files != mirror_files:
                    problems.append(f"drift in {name}/: {len(source_files)} vs {len(mirror_files)} files")
                for rel in source_files & mirror_files:
                    if (source / rel).read_bytes() != (mirror / rel).read_bytes():
                        problems.append(f"content drift: {name}/{rel}")
            else:
                target = DATA / name
                if not target.is_file() or target.read_bytes() != source.read_bytes():
                    problems.append(f"drift in {name}")
        if problems:
            for problem in problems:
                print(f"assemble --check: {problem}", file=sys.stderr)
            print("Run: python scripts/assemble_data.py", file=sys.stderr)
            return 1
        print("assemble --check: archharness/data is up to date")
        return 0

    total = 0
    for name, source in SOURCES.items():
        if source.is_dir():
            files = _copy_tree(source, DATA / name)
            total += len(files)
        else:
            shutil.copy2(source, DATA / name)
            total += 1
    print(f"assemble: {total} file(s) copied to {DATA}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify data directory without writing")
    args = parser.parse_args()
    raise SystemExit(assemble(check=args.check))
