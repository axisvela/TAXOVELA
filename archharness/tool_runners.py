"""Run the repository's standalone Python tools through the archharness CLI.

The tools under tools/ remain the canonical implementation and keep working as
standalone scripts (`python tools/arch-diagram-gen/arch_diagram_gen.py …`).
This module loads them from the ArchHarness resource root so users get a single,
discoverable entry point (`archharness diagram`, `archharness req`,
`archharness validate-yaml`) regardless of the current directory.

Transitional note: tool modules are loaded by file location because they live
outside the importable package (both in checkouts and in wheel data). All
tool mains accept an explicit ``argv`` list and return integer exit codes, so
this loader never touches ``sys.argv`` and never calls ``sys.exit`` itself.
Long term, tool logic moves into the package and this loader becomes plain
imports (see ``archharness.api`` for the stable programmatic contract).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from .paths import require_archharness_root

TOOLS = {
    "diagram": ("tools/arch-diagram-gen", "arch_diagram_gen.py", "archharness_tool_diagram"),
    "req": ("tools/arch-req-readers", "req_reader.py", "archharness_tool_req"),
    "validate-yaml": ("tools", "yaml_validate.py", "archharness_tool_yaml_validate"),
}


def _load_tool(relative_dir: str, filename: str, module_name: str):
    root = require_archharness_root()
    directory = root / relative_dir
    path = directory / filename
    if not path.is_file():
        raise ImportError(f"cannot load tool: {path}")
    # Tool entry points use deferred sibling imports (e.g. `from merger
    # import ...` inside function bodies), so their directory must stay
    # importable. Insert idempotently: at most one entry per tool directory,
    # never unbounded growth from repeated calls.
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))
    if module_name in sys.modules:
        return sys.modules[module_name]
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load tool: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    return module


def run_tool(name: str, tool_args: list[str]) -> int:
    """Execute one of the passthrough tools and return its exit code."""
    if name not in TOOLS:
        raise ValueError(f"unknown tool: {name}")
    relative_dir, filename, module_name = TOOLS[name]
    module = _load_tool(relative_dir, filename, module_name)
    main = getattr(module, "main", None)
    if main is None:
        raise RuntimeError(f"{filename} has no main()")
    try:
        # Every tool main takes an explicit argv list and returns an int.
        result = main(tool_args)
        return int(result or 0)
    except SystemExit as exc:  # defensive: tools should not raise SystemExit
        code = exc.code
        return int(code) if isinstance(code, int) else (0 if code is None else 1)
