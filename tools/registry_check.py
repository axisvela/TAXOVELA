#!/usr/bin/env python3
"""Backward-compatible shim: delegates to archharness.registry."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from archharness.registry import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
