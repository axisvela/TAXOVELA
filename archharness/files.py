"""Atomic file writes for governed artifacts.

Every artifact write goes through :func:`atomic_write_text`: content lands
in a temporary sibling file first and is moved over the target only after
the write completes. A failed render therefore never leaves a truncated
file behind, and the last good output stays intact (last-good semantics).
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


def atomic_write_text(path: str | Path, content: str) -> None:
    """Write text atomically. Raises OSError with context on failure."""
    target = Path(path)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise OSError(f"cannot create directory for {target}: {exc}") from exc
    try:
        fd, tmp_name = tempfile.mkstemp(
            dir=str(target.parent), prefix=target.name + ".", suffix=".tmp"
        )
    except OSError as exc:
        raise OSError(f"cannot stage write for {target}: {exc}") from exc
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.replace(tmp_name, target)
    except BaseException as exc:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise OSError(f"cannot write {target}: {exc}") from exc
