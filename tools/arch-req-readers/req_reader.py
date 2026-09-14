#!/usr/bin/env python3
"""Backward-compatible shim: delegates to archharness.requirements.command.

Prefer `archharness req ...` or `archharness.api.run_requirements(...)`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from archharness.requirements.command import main

if __name__ == "__main__":
    raise SystemExit(main())
