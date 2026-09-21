#!/usr/bin/env python3
"""registry.py — verify systems-registry <-> docs consistency for one example.

The reference diagram image is intentionally NOT scrubbed; every other file
must reference entities only by typed codes from input/systems-registry.md.

Since req/v2 the registry is **one markdown table per entity kind**
(infra / systems / components / deployments / flows / network_links / auth),
each with a typed ID prefix (`INF-`, `APP-`, `CMP-`, `DEP-`, `FLOW-`, `LNK-`,
`AUTH-`, `STK-`). The legacy single-table `SYS-nn` format is still accepted so
existing examples keep working until they are rebuilt.

Checks:
  1. Unknown codes cited in docs (ERROR) — a code with no registry row.
  2. Inventory rows never cited in any doc (WARN) — possibly dead entries.
     Inventory = infra / systems / components / subsystems; relationship rows
     (deployments, flows, network_links, auth) are exempt.
  3. Distinctive "doc-name" literals in docs outside the registry (ERROR).
     Plain single-word names (Kafka, Redis, S3, …) are skipped here and printed
     separately for manual review.
  4. IPv4 addresses/CIDRs in textual example files (ERROR).
  5. Scope guard (WARN): an in-scope inventory row not referenced by
     `input/prompt.md`. Mark a row `OUT-OF-SCOPE` in its 备注/Notes column to
     exempt it.
  6. Malformed rows (ERROR/WARN): unknown prefix, or a column count that does
     not match the table header.

Usage:
    python tools/registry_check.py examples/01-ecommerce-azure
    python tools/registry_check.py examples/01-ecommerce-azure examples/02-ai-agent-hybrid ...

Exit code: 0 = no errors (warnings allowed), 1 = errors found.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REGISTRY_NAME = "systems-registry.md"

# Typed ID prefixes. Loaded from the packaged model spec, with a static
# fallback so the checker still works if the spec cannot be read.
_FALLBACK_PREFIXES = {
    "INF": "infra", "APP": "systems", "CMP": "components", "SUB": "subsystems",
    "STK": "stacks", "DEP": "deployments", "FLOW": "flows",
    "LNK": "network_links", "AUTH": "auth",
}
LEGACY_PREFIX = "SYS"
LEGACY_ENTITY = "legacy"

# Only inventory entities are checked against the one-shot prompt. Relationship
# rows (deployments, flows, network_links, auth, ecosystem_relations) are
# consequences of the inventory, not items the prompt must enumerate.
SCOPE_GUARD_ENTITIES = {"infra", "systems", "components", "subsystems", "legacy"}


def _load_prefixes() -> dict[str, str]:
    """Return {prefix: entity} from standards/requirements-model-v2.yaml."""
    try:
        import yaml
        from .paths import require_archharness_root
        spec = require_archharness_root() / "standards" / "requirements-model-v2.yaml"
        data = yaml.safe_load(spec.read_text(encoding="utf-8")) or {}
        entities = data.get("entities") or {}
        prefixes = {
            info["id_prefix"]: name
            for name, info in entities.items()
            if isinstance(info, dict) and info.get("id_prefix")
        }
        if prefixes:
            return prefixes
    except Exception:
        pass
    return dict(_FALLBACK_PREFIXES)


PREFIXES = _load_prefixes()
PREFIXES.setdefault("SUB", "subsystems")
CODE_PREFIXES = tuple(PREFIXES) + (LEGACY_PREFIX,)

# A typed code: 2-5 uppercase letters, dash, digits.
CODE_PATTERN = re.compile(r"\b([A-Z]{2,5})-(\d{1,4})\b")
CODE_TOKEN = re.compile(r"^([A-Z]{2,5})-(\d{1,4})$")
# Range citations like "INF-06-INF-13", "SYS-02..SYS-04" or "APP-07 through APP-23".
RANGE_PATTERN = re.compile(
    r"\b([A-Z]{2,5})-(\d+)\s*(?:[–—-]|\.\.|through)\s*([A-Z]{2,5})-(\d+)\b",
    re.IGNORECASE,
)
IPV4_PATTERN = re.compile(
    r"(?<!\d)(?:25[0-5]|2[0-4]\d|1?\d?\d)"
    r"(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){3}(?:/\d{1,2})?(?!\d)"
)

# Header aliases (Chinese registry headers + tolerant English forms).
_HEADER_CODE = {"编号", "序号", "code"}
_HEADER_DOCNAME = {"文档用名", "doc name", "doc-name", "document name", "名称"}
_HEADER_NOTES = {"备注", "notes", "note", "remark"}
_HEADER_SOURCE = {"参考图原名", "source name", "original name", "原名"}
_HEADER_ARTIFACT = {"参考图原名", "source name"}

ALWAYS_SKIP = {"etc.", "etc"}
OUT_OF_SCOPE_PATTERN = re.compile(r"out[- ]?of[- ]?scope", re.IGNORECASE)
_SEPARATOR_CELL = re.compile(r"^:?-{2,}:?$")


# ── Markdown table parsing ────────────────────────────────────────────────────

def _split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _is_separator(cells: list[str]) -> bool:
    return bool(cells) and all(_SEPARATOR_CELL.match(c) or not c for c in cells)


def _iter_tables(text: str):
    """Yield (header, rows) for every markdown table in ``text``."""
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if line.startswith("|") and index + 1 < len(lines) and lines[index + 1].strip().startswith("|"):
            header = _split_row(line)
            separator = _split_row(lines[index + 1])
            if _is_separator(separator):
                rows = []
                cursor = index + 2
                while cursor < len(lines) and lines[cursor].strip().startswith("|"):
                    rows.append(_split_row(lines[cursor]))
                    cursor += 1
                yield header, rows
                index = cursor
                continue
        index += 1


def _column_index(header: list[str], aliases: set[str]) -> int | None:
    for position, name in enumerate(header):
        if name.strip().lower() in aliases:
            return position
    return None


def parse_registry(path: Path) -> dict[str, dict]:
    """Parse the registry into {code: {entity, doc_name, notes, in_scope, table}}.

    Table kind is decided per row by the code's prefix, so a registry may hold
    several typed tables (and legacy ``SYS-nn`` tables) in one file.
    """
    rows: dict[str, dict] = {}
    for header, raw_rows in _iter_tables(path.read_text(encoding="utf-8")):
        code_col = _column_index(header, _HEADER_CODE)
        name_col = _column_index(header, _HEADER_DOCNAME)
        notes_col = _column_index(header, _HEADER_NOTES)
        # A registry table is identified by its code column (编号). Derived
        # tables (flows, links, auth) have no doc-name column; other markdown
        # tables without a 编号 column are ignored.
        if code_col is None:
            continue
        width = len(header)

        for cells in raw_rows:
            if _is_separator(cells) or not cells:
                continue
            if code_col >= len(cells):
                continue
            token = cells[code_col]
            match = CODE_TOKEN.match(token)
            if not match:
                continue
            prefix = match.group(1).upper()
            # An unrecognised prefix in a registry table is an authoring error;
            # keep the row so check_example can report it.
            code = f"{prefix}-{int(match.group(2)):02d}"

            doc_name = cells[name_col] if name_col is not None and name_col < len(cells) else ""
            notes = cells[notes_col] if notes_col is not None and notes_col < len(cells) else ""
            entity = LEGACY_ENTITY if prefix == LEGACY_PREFIX else PREFIXES.get(prefix, "unknown")

            rows[code] = {
                "prefix": prefix,
                "entity": entity,
                "doc_name": doc_name,
                "notes": notes,
                "in_scope": not OUT_OF_SCOPE_PATTERN.search(notes),
                "table": tuple(header),
                "width": width,
                "actual_width": len(cells),
                "table_name": f"{entity}: {header[0] if header else '?'}…",
            }
    return rows


def parse_registry_rows(path: Path) -> dict[str, dict]:
    """Backward-compatible alias returning the parsed row records."""
    return parse_registry(path)


# ── Text helpers ──────────────────────────────────────────────────────────────

def read_doc_text(doc: Path) -> str:
    """Read a doc, dropping the functional `platforms:` block of config.yaml."""
    try:
        text = doc.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return ""
    if doc.name != "config.yaml":
        return text
    kept: list[str] = []
    in_platforms = False
    for line in text.splitlines():
        if re.match(r"^platforms:", line):
            in_platforms = True
            continue
        if in_platforms and re.match(r"^[A-Za-z#]", line):
            in_platforms = False
        if not in_platforms:
            kept.append(line)
    return "\n".join(kept)


def collect_docs(root: Path) -> list[Path]:
    """All text files under the example dir except the registry itself."""
    skip_dirs = {".git", "output"}
    skip_names = {REGISTRY_NAME, ".gitkeep"}
    skip_suffixes = {".png", ".jpg", ".jpeg", ".drawio", ".bak"}
    docs = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name in skip_names or path.suffix.lower() in skip_suffixes:
            continue
        if any(part in skip_dirs for part in path.parts):
            continue
        docs.append(path)
    return docs


def _codes_in(text: str) -> set[str]:
    codes = set()
    for match in CODE_PATTERN.finditer(text):
        prefix = match.group(1).upper()
        if prefix in CODE_PREFIXES:
            codes.add(f"{prefix}-{int(match.group(2)):02d}")
    for match in RANGE_PATTERN.finditer(text):
        p_lo, lo, p_hi, hi = match.group(1).upper(), int(match.group(2)), \
            match.group(3).upper(), int(match.group(4))
        if p_lo != p_hi or p_lo not in CODE_PREFIXES:
            continue
        if lo > hi:
            lo, hi = hi, lo
        codes.update(f"{p_lo}-{n:02d}" for n in range(lo, hi + 1))
    return codes


# ── Checks ────────────────────────────────────────────────────────────────────

def check_example(root: Path) -> int:
    registry_path = root / "input" / REGISTRY_NAME
    if not registry_path.is_file():
        print(f"{root}: SKIP (no {REGISTRY_NAME})")
        return 0
    rows = parse_registry(registry_path)
    if not rows:
        print(f"{root}: ERROR: registry has no parseable rows")
        return 1

    docs = collect_docs(root)
    errors = 0

    # 0. Malformed rows: bad width, or unknown entity prefix.
    for code, row in sorted(rows.items()):
        if row["actual_width"] != row["width"]:
            print(f"{root}: WARN: {code}: {row['actual_width']} columns vs "
                  f"{row['width']} in header ({row['entity']} table)")
        if row["entity"] == "unknown":
            print(f"{root}: ERROR: {code}: unknown entity prefix")
            errors += 1

    # 1. Unknown codes cited in docs.
    cited: dict[str, list[str]] = {}
    for doc in docs:
        if doc == registry_path:
            continue
        text = read_doc_text(doc)
        for code in _codes_in(text):
            cited.setdefault(code, []).append(str(doc.relative_to(root)))
    for code, files in sorted(cited.items()):
        if code not in rows:
            print(f"{root}: ERROR: {code} cited but not in registry: {sorted(set(files))}")
            errors += 1

    # 2. Registry rows never cited (out-of-scope rows are exempt).
    def _sort_key(code: str) -> tuple[str, int]:
        prefix, number = code.split("-")
        return prefix, int(number)

    for code in sorted(rows, key=_sort_key):
        if (code not in cited and rows[code]["in_scope"]
                and rows[code]["entity"] in SCOPE_GUARD_ENTITIES):
            print(f"{root}: WARN: {code} ({rows[code]['doc_name']}) never cited in docs")

    # 3. Distinctive doc-name literals outside the registry.
    distinctive = {
        code: row["doc_name"] for code, row in rows.items()
        if row["doc_name"] and re.search(r"[^A-Za-z0-9]", row["doc_name"])
        and row["doc_name"] not in ALWAYS_SKIP
    }
    for doc in docs:
        if doc == registry_path:
            continue
        text = read_doc_text(doc)
        for code, name in distinctive.items():
            if name in text:
                print(f"{root}: ERROR: literal doc-name '{name}' ({code}) "
                      f"in {doc.relative_to(root)} — use the code")
                errors += 1

    # 4. Path A scope guard: every in-scope row must be referenced by prompt.md.
    prompt_path = root / "input" / "prompt.md"
    if prompt_path.is_file():
        prompt_codes = _codes_in(read_doc_text(prompt_path))
        for code in sorted(rows, key=_sort_key):
            if (code not in prompt_codes and rows[code]["in_scope"]
                    and rows[code]["entity"] in SCOPE_GUARD_ENTITIES):
                print(f"{root}: WARN: {code} ({rows[code]['doc_name']}) is in the "
                      f"registry but not referenced by input/prompt.md (mark the "
                      f"row OUT-OF-SCOPE if that is deliberate)")
    else:
        print(f"{root}: WARN: no input/prompt.md — Path A scope cannot be checked")

    single_word = sorted({row["doc_name"] for row in rows.values()
                          if row["doc_name"] and not re.search(r"[^A-Za-z0-9]", row["doc_name"])})
    if single_word:
        print(f"{root}: INFO: single-word names skipped from literal check "
              f"(review manually): {', '.join(single_word)}")

    # 5. IP addresses are forbidden in all textual inputs/config/docs.
    for doc in docs:
        text = read_doc_text(doc)
        matches = sorted(set(IPV4_PATTERN.findall(text)))
        if matches:
            print(f"{root}: ERROR: IP address/CIDR in "
                  f"{doc.relative_to(root)}: {', '.join(matches)}")
            errors += 1

    if not errors:
        counts: dict[str, int] = {}
        for row in rows.values():
            counts[row["entity"]] = counts.get(row["entity"], 0) + 1
        breakdown = ", ".join(f"{count} {entity}" for entity, count in sorted(counts.items()))
        print(f"{root}: OK ({len(rows)} registry rows [{breakdown}], "
              f"{len(cited)} codes cited)")
    return 1 if errors else 0


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    failed = False
    for target in argv[1:]:
        if check_example(Path(target)):
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
