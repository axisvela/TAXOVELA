#!/usr/bin/env python3
"""registry_check.py — verify systems-registry <-> docs consistency for one example.

The reference diagram image is intentionally NOT scrubbed; every other file
must reference systems only by SYS-nn codes from input/systems-registry.md.

Checks:
  1. Unknown SYS-nn codes cited in docs (ERROR) — a code with no registry row.
  2. Registry rows never cited in any doc (WARN) — possibly dead entries.
  3. Distinctive "doc-name" literals in docs outside the registry (ERROR).
     `input/prompt.md` is the human-maintained naming source and is excluded
     from this literal-name check. "Distinctive" = contains a
     non-alphanumeric character (space, '-', '/',
     parentheses, ...). Plain single-word names (Kafka, Redis, S3, ECC, ...)
     are ALSO generic technology words, so they are skipped here and printed
     separately for manual review.
  4. IPv4 addresses/CIDRs in textual example files (ERROR).

Usage:
    python tools/registry_check.py examples/03-order-query-aws-hybrid
    python tools/registry_check.py examples/01-ecommerce-azure examples/02-ai-agent-hybrid ...

Exit code: 0 = no errors (warnings allowed), 1 = errors found.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REGISTRY_NAME = "systems-registry.md"
CODE_PATTERN = re.compile(r"SYS-(\d+)")
IPV4_PATTERN = re.compile(
    r"(?<!\d)(?:25[0-5]|2[0-4]\d|1?\d?\d)"
    r"(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){3}(?:/\d{1,2})?(?!\d)"
)
# Range citations like "SYS-06–SYS-13", "SYS-02..SYS-04" or
# "SYS-07 through SYS-23" cite every code in between.
RANGE_PATTERN = re.compile(
    r"SYS-(\d+)\s*(?:[–—-]|\.\.|through)\s*SYS-(\d+)", re.IGNORECASE)
ROW_PATTERN = re.compile(
    r"^\|\s*(SYS-\d+)\s*\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|"
)

# Doc-names that are ordinary prose even though they look distinctive.
ALWAYS_SKIP = {"etc.", "etc"}


def parse_registry(path: Path) -> dict[str, str]:
    """Return {code: doc-name} from the registry table."""
    entries: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = ROW_PATTERN.match(line.strip())
        if match:
            entries[match.group(1)] = match.group(5).strip()
    return entries


def read_doc_text(doc: Path) -> str:
    """Read a doc, dropping the functional `platforms:` block of config.yaml.

    Platform identifiers (api_gateway, auth_external, integration_platforms,
    ...) are consumed by rules/tools and must stay literal — a registry
    doc-name that coincides with one (e.g. SYS-02 "Enterprise ID") is not
    drift. Only prose/notes are checked.
    """
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
    # Generated output materializes the registry's document names by design;
    # it is not a numbered source document and must not be treated as drift.
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


def check_example(root: Path) -> int:
    registry_path = root / "input" / REGISTRY_NAME
    if not registry_path.is_file():
        print(f"{root}: SKIP (no {REGISTRY_NAME})")
        return 0
    entries = parse_registry(registry_path)
    if not entries:
        print(f"{root}: ERROR: registry has no parseable rows")
        return 1

    docs = collect_docs(root)
    errors = 0

    # 1. Unknown codes cited in docs.
    cited: dict[str, list[str]] = {}
    for doc in docs:
        if doc == registry_path:
            continue
        text = read_doc_text(doc)
        for match in CODE_PATTERN.finditer(text):
            cited.setdefault(f"SYS-{match.group(1)}", []).append(
                str(doc.relative_to(root)))
        for match in RANGE_PATTERN.finditer(text):
            lo, hi = int(match.group(1)), int(match.group(2))
            if lo > hi:
                lo, hi = hi, lo
            for n in range(lo, hi + 1):
                cited.setdefault(f"SYS-{n:02d}", []).append(
                    str(doc.relative_to(root)) + " (range)")
    unknown = {c: sorted(set(v)) for c, v in cited.items() if c not in entries}
    for code, files in sorted(unknown.items()):
        print(f"{root}: ERROR: {code} cited but not in registry: {files}")
        errors += 1

    # 2. Registry rows never cited.
    for code in sorted(entries, key=lambda c: int(c.split("-")[1])):
        if code not in cited:
            print(f"{root}: WARN: {code} ({entries[code]}) never cited in docs")

    # 3. Distinctive doc-name literals outside the registry and the
    # human-maintained source prompt.
    distinctive = {
        code: name for code, name in entries.items()
        if re.search(r"[^A-Za-z0-9]", name) and name not in ALWAYS_SKIP
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

    # 4. Path A scope guard: every registry code must be referenced by
    # input/prompt.md, otherwise the one-shot prompt yields a diagram that
    # silently omits systems the registry declares.
    prompt_path = root / "input" / "prompt.md"
    if prompt_path.is_file():
        prompt_codes: set[str] = set()
        prompt_text = read_doc_text(prompt_path)
        for match in CODE_PATTERN.finditer(prompt_text):
            prompt_codes.add(f"SYS-{match.group(1)}")
        for match in RANGE_PATTERN.finditer(prompt_text):
            lo, hi = int(match.group(1)), int(match.group(2))
            if lo > hi:
                lo, hi = hi, lo
            prompt_codes.update(f"SYS-{n:02d}" for n in range(lo, hi + 1))
        for code in sorted(entries, key=lambda c: int(c.split("-")[1])):
            if code not in prompt_codes:
                print(f"{root}: WARN: {code} ({entries[code]}) is in the registry "
                      f"but not referenced by input/prompt.md")
    else:
        print(f"{root}: WARN: no input/prompt.md — Path A scope cannot be checked")

    single_word = sorted({n for n in entries.values()
                          if not re.search(r"[^A-Za-z0-9]", n)})
    if single_word:
        print(f"{root}: INFO: single-word names skipped from literal check "
              f"(review manually): {', '.join(single_word)}")

    # 4. IP addresses are forbidden in all textual inputs/config/docs.
    for doc in docs:
        text = read_doc_text(doc)
        matches = sorted(set(IPV4_PATTERN.findall(text)))
        if matches:
            print(f"{root}: ERROR: IP address/CIDR in "
                  f"{doc.relative_to(root)}: {', '.join(matches)}")
            errors += 1

    if not errors:
        print(f"{root}: OK ({len(entries)} registry rows, "
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
