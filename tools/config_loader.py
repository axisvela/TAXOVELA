"""Backward-compatible shim: delegates to archharness.config."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from archharness.config import *  # noqa: F401,F403
from archharness.config import deep_merge, find_config, find_config_chain, load_config
