"""Dispatch CLI passthrough commands to their in-package implementations.

The ``tools/`` scripts remain as thin backward-compatible shims, but the
canonical implementation lives in this package and is imported normally —
no file-location loading, no ``sys.path`` mutation, no ``sys.argv`` juggling.
"""

from __future__ import annotations

from .diagrams import command as diagram_command
from .requirements import command as req_command
from . import arch_check as arch_check_module
from . import backlog as backlog_module
from . import migrate_status as migrate_status_module
from . import schema_check as schema_check_module
from . import trace_check as trace_check_module
from . import validate_check as validate_check_module
from . import yaml_validate as yaml_validate_module

_COMMANDS = {
    "arch-check": arch_check_module.main,
    "backlog": backlog_module.main,
    "diagram": diagram_command.main,
    "migrate-status": migrate_status_module.main,
    "req": req_command.main,
    "schema-check": schema_check_module.main,
    "trace-check": trace_check_module.main,
    "validate-check": validate_check_module.main,
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
