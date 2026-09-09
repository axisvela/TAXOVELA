"""ArchHarness resource-root discovery.

The Python tools and standard files shipped in this repository are referenced
by skills via repo-relative paths (`tools/…`, `standards/…`). These helpers let
code and prompts locate the install root without depending on the current
working directory:

    ARCHHARNESS_HOME=/path/to/ea-harness   # explicit override (recommended)
    …or walk up from this package until a config.yaml + tools/ pair is found.
"""

from __future__ import annotations

import os
from pathlib import Path


def find_archharness_root(start: Path | None = None) -> Path | None:
    """Return the ArchHarness resource root (config.yaml + tools/), or None."""
    override = os.environ.get("ARCHHARNESS_HOME")
    if override:
        candidate = Path(override).resolve()
        if (candidate / "config.yaml").is_file() and (candidate / "tools").is_dir():
            return candidate

    probe = (start or Path(__file__).resolve().parent).resolve()
    for directory in (probe, *probe.parents):
        if (directory / "config.yaml").is_file() and (directory / "tools").is_dir():
            return directory
    return None


def require_archharness_root() -> Path:
    root = find_archharness_root()
    if root is None:
        raise FileNotFoundError(
            "ArchHarness resource root not found. Run from the checkout, or set "
            "ARCHHARNESS_HOME to the directory containing config.yaml and tools/."
        )
    return root
