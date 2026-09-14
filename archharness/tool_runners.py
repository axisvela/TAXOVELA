"""Dispatch CLI passthrough commands to their in-package implementations.

The ``tools/`` scripts remain as thin backward-compatible shims, but the
canonical implementation lives in this package and is imported normally —
no file-location loading, no ``sys.path`` mutation, no ``sys.argv`` juggling.
"""

from __future__ import annotations

from .diagrams import command as diagram_command
from .requirements import command as req_command
from . import yaml_validate as yaml_validate_module

_COMMANDS = {
    "diagram": diagram_command.main,
    "req": req_command.main,
    "validate-yaml": yaml_validate_module.main,
}


def run_tool(name: str, tool_args: list[str]) -> int:
    """Execute one of the passthrough tools and return its exit code."""
    if name not in _COMMANDS:
        raise ValueError(f"unknown tool: {name}")
    try:
        result = _COMMANDS[name](tool_args)
        return int(result or 0)
    except SystemExit as exc:  # defensive: tools should not raise SystemExit
        code = exc.code
        return int(code) if isinstance(code, int) else (0 if code is None else 1)
