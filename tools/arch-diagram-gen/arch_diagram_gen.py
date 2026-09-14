#!/usr/bin/env python3
"""Backward-compatible shim: delegates to archharness.diagrams.command.

Prefer `archharness diagram ...` or `archharness.api.run_diagram(...)`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from archharness.diagrams.command import main

if __name__ == "__main__":
    raise SystemExit(main())
