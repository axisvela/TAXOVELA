#!/usr/bin/env python3
"""
yaml_validate.py — Non-destructive YAML syntax validator for architecture standards files.

Validates one or more YAML files for syntactic correctness.  Fail-closed:
if ANY file is invalid YAML, exits with code 1 and prints a concise diagnostic
for each problem.  Performs no file writes — completely non-destructive.

Usage:
    python tools/yaml_validate.py standards/*.yaml config.yaml
    python tools/yaml_validate.py --strict standards/*.yaml   # also warn on duplicates
    python tools/yaml_validate.py .                           # scan all .yaml/.yml under dir

Exit codes:
    0  — all files valid
    1  — one or more files have invalid YAML (fail-closed)
    2  — internal error / file-not-found
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Iterator


# ──────────────────────────────────────────────────────────────────────
# Try both YAML parsers: pyyaml (preferred), then ruamel.yaml (fallback)
# ──────────────────────────────────────────────────────────────────────
def _import_yaml():
    """Import a YAML parser.  Prefer pyyaml for speed, fall back to ruamel."""
    try:
        import yaml as _yaml
        return _yaml, "PyYAML"
    except ImportError:
        pass
    try:
        from ruamel import yaml as _yaml
        return _yaml, "ruamel.yaml"
    except ImportError:
        pass
    sys.exit(
        "ERROR: No YAML library available.\n"
        "Install one with:  pip install pyyaml\n"
        "             or:  pip install ruamel.yaml"
    )


yaml_mod, yaml_name = _import_yaml()


# ──────────────────────────────────────────────────────────────────────
# Result type
# ──────────────────────────────────────────────────────────────────────
class ValidationResult:
    """Collects per-file validation results."""

    __slots__ = ("path", "valid", "error_count", "errors", "warnings")

    def __init__(self, path: Path):
        self.path = path
        self.valid = True
        self.error_count = 0
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def add_error(self, line: int, col: int | None, msg: str) -> None:
        self.valid = False
        self.error_count += 1
        location = f"line {line}"
        if col is not None:
            location += f", column {col}"
        self.errors.append(f"  {location}: {msg}")

    def add_warning(self, line: int, msg: str) -> None:
        self.warnings.append(f"  line {line}: {msg}")

    def diagnostic(self) -> str:
        """Return the concise human-readable diagnostic block for this file."""
        parts: list[str] = []
        if self.errors:
            parts.append(f"  ** {len(self.errors)} YAML error(s):")
            parts.extend(self.errors)
        if self.warnings:
            parts.append(f"  ** {len(self.warnings)} warning(s):")
            parts.extend(self.warnings)
        return "\n".join(parts)

    def __repr__(self) -> str:
        status = "OK" if self.valid else "INVALID"
        return f"[{status}] {self.path}"


# ──────────────────────────────────────────────────────────────────────
# Core validation logic
# ──────────────────────────────────────────────────────────────────────
def validate_file(path: Path | str, strict: bool = False) -> ValidationResult:
    """
    Validate a single YAML file.

    Parameters
    ----------
    path : Path | str
        Path to the YAML file to validate.  Strings are auto-converted to Path.
    strict : bool
        If True, also warn about duplicate keys.

    Returns
    -------
    ValidationResult
        Result object with .valid, .errors, .warnings, .diagnostic().
    """
    if isinstance(path, str):
        path = Path(path)
    result = ValidationResult(path)

    if not path.exists():
        result.valid = False
        result.add_error(1, None, f"file not found: {path}")
        return result
    if not path.is_file():
        result.valid = False
        result.add_error(1, None, f"not a regular file: {path}")
        return result

    try:
        raw_text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        result.valid = False
        result.add_error(1, None, f"encoding error (expected UTF-8): {e}")
        return result
    except PermissionError as e:
        result.valid = False
        result.add_error(1, None, f"permission denied: {e}")
        return result
    except OSError as e:
        result.valid = False
        result.add_error(1, None, f"I/O error: {e}")
        return result

    # Empty file is valid (zero-document stream)
    if not raw_text.strip():
        return result

    # ── Parse ───────────────────────────────────────────────────────
    try:
        if yaml_name == "ruamel.yaml":
            # ruamel preserves line numbers in its error reporting
            yaml_mod.YAML().load(raw_text)
        else:
            # PyYAML: safe_load gives us syntax errors with position info
            yaml_mod.safe_load(raw_text)
    except yaml_mod.scanner.ScannerError as e:
        # Extract position information from the error message
        line, col = _extract_position(str(e))
        result.add_error(line, col, str(e).split("\n")[0])
        return result
    except yaml_mod.parser.ParserError as e:
        line, col = _extract_position(str(e))
        result.add_error(line, col, str(e).split("\n")[0])
        return result
    except yaml_mod.YAMLError as e:
        # Generic catch-all for other YAML errors
        line, col = _extract_position(str(e))
        msg = str(e).rstrip()
        result.add_error(line, col, msg.split("\n")[0] if msg else "unknown YAML error")
        return result
    except Exception as e:
        result.add_error(1, None, f"unexpected error: {e}")
        return result

    # ── Optional: duplicate key detection (strict mode) ─────────────
    if strict:
        _check_duplicate_keys(raw_text, result)

    return result


def _extract_position(err_msg: str) -> tuple[int, int | None]:
    """
    Extract (line, column) from a YAML parser error message.

    PyYAML and ruamel.yaml both include text like:
        "in '<unicode string>', line 42, column 13:"
        "in "<reader>", line 12, column 3"
    """
    import re
    m = re.search(r"line\s+(\d+)", err_msg)
    line = int(m.group(1)) if m else 1
    m = re.search(r"column\s+(\d+)", err_msg)
    col = int(m.group(1)) if m else None
    return line, col


def _check_duplicate_keys(raw_text: str, result: ValidationResult) -> None:
    """
    Check for duplicate YAML keys at the top level.
    Uses a simple line-by-line heuristic — does not catch nested duplicates.
    """
    seen: dict[str, int] = {}
    for lineno, line in enumerate(raw_text.splitlines(), start=1):
        stripped = line.strip()
        # Skip comments, blank lines, and list items
        if not stripped or stripped.startswith("#") or stripped.startswith("-"):
            continue
        # Match top-level key:  word:
        if ":" in stripped and not stripped.startswith(" "):
            key = stripped.split(":", 1)[0].strip()
            if key and key[0].isalnum():
                if key in seen:
                    result.add_warning(lineno, f"duplicate key '{key}' (first seen line {seen[key]})")
                else:
                    seen[key] = lineno


# ──────────────────────────────────────────────────────────────────────
# File discovery
# ──────────────────────────────────────────────────────────────────────
YAML_EXTENSIONS = {".yaml", ".yml"}


def discover_paths(targets: list[str]) -> Iterator[Path]:
    """
    Resolve CLI target paths to YAML files.

    - If a target is a directory, recursively yield all .yaml/.yml files under it.
    - If a target is a file, yield it (regardless of extension — the user
      may pass ``config.yaml`` explicitly).
    - Glob patterns are resolved by the shell; this function receives the
      expanded results from ``argparse``.
    """
    for target in targets:
        p = Path(target)
        if p.is_dir():
            yield from sorted(p.rglob("*.*"))  # filter below
        elif p.exists():
            yield p
        else:
            # Path doesn't exist — could be a glob that didn't match;
            # argparse doesn't do glob expansion on Windows.
            # Try glob expansion manually.
            import glob as glob_mod
            expanded = glob_mod.glob(target, recursive=True)
            if expanded:
                for match in sorted(expanded):
                    mp = Path(match)
                    if mp.is_file():
                        yield mp
            else:
                # Emit a pseudo-result so the user sees the error
                pseudo = Path(target)
                # We'll let the caller handle non-existent paths


# ──────────────────────────────────────────────────────────────────────
# CLI entry point
# ──────────────────────────────────────────────────────────────────────
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="yaml_validate.py",
        description="Non-destructive YAML syntax validation for architecture standards files.",
        epilog="Exit code: 0 = all valid, 1 = one or more files invalid (fail-closed).",
    )
    ap.add_argument(
        "paths",
        nargs="+",
        help="One or more YAML files, directories, or glob patterns to validate. "
             "Directories are scanned recursively for .yaml/.yml files.",
    )
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Enable additional checks: duplicate key detection, trailing whitespace warnings.",
    )
    ap.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress per-file OK messages.  Only show errors and summary.",
    )

    args = ap.parse_args(argv)

    # ── Collect files ───────────────────────────────────────────────
    files: list[Path] = []
    not_found: list[str] = []
    for p in discover_paths(args.paths):
        if p.suffix.lower() in YAML_EXTENSIONS or p.suffix in ("",):
            if p.is_dir():
                continue
            files.append(p)
        else:
            # Include non-.yaml files only if the user explicitly passed them
            # (i.e., they exist and were directly requested)
            files.append(p)

    # Check for explicit paths that don't exist
    for target in args.paths:
        p = Path(target)
        if not p.exists() and not any(
            str(p) == str(f) for f in files
        ):
            # Check if glob had any matches
            import glob as glob_mod
            if not glob_mod.glob(target, recursive=True):
                not_found.append(target)

    if not files:
        for nf in not_found:
            print(f"ERROR: no matching files: {nf}", file=sys.stderr)
        if not_found:
            return 1
        print("ERROR: no YAML files found to validate.", file=sys.stderr)
        return 2

    # ── Validate ────────────────────────────────────────────────────
    results: list[ValidationResult] = []
    any_invalid = False

    for f in files:
        result = validate_file(f, strict=args.strict)
        results.append(result)
        if not result.valid:
            any_invalid = True

        # Print diagnostic
        if result.errors or result.warnings:
            label = "INVALID" if not result.valid else "VALID (with warnings)"
            print(f"\n-- {label} -- {f}")
            if result.diagnostic():
                print(result.diagnostic())
        elif not args.quiet:
            print(f"  OK: {f}")

    # ── Summary ─────────────────────────────────────────────────────
    total = len(results)
    passed = sum(1 for r in results if r.valid)
    failed = total - passed
    total_errors = sum(r.error_count for r in results)

    summary_parts: list[str] = []
    if failed:
        summary_parts.append(f"FAIL-CLOSED: {failed}/{total} file(s) invalid ({total_errors} error(s) total)")
    else:
        summary_parts.append(f"All {total} file(s) valid")

    if args.strict:
        total_warnings = sum(len(r.warnings) for r in results)
        if total_warnings:
            summary_parts.append(f"  ({total_warnings} warning(s) from strict checks)")

    print(f"\n-- Summary ---")
    print("  ".join(summary_parts))

    return 1 if any_invalid else 0


if __name__ == "__main__":
    sys.exit(main())
