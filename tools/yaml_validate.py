#!/usr/bin/env python3
"""Backward-compatible shim: delegates to archharness.yaml_validate."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from archharness.yaml_validate import main

if __name__ == "__main__":
    raise SystemExit(main())
