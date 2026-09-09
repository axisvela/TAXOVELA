"""Run the repository's standalone Python tools through the archharness CLI.

The tools under tools/ remain the canonical implementation and keep working as
standalone scripts (`python tools/arch-diagram-gen/arch_diagram_gen.py …`).
This module loads them from the ArchHarness resource root so users get a single,
discoverable entry point (`archharness diagram`, `archharness req`,
`archharness validate-yaml`) regardless of the current directory.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from .paths import require_archharness_root

TOOLS = {
    "diagram": ("tools/arch-diagram-gen", "arch_diagram_gen.py", "arch_diagram_gen"),
    "req": ("tools/arch-req-readers", "req_reader.py", "req_reader"),
    "validate-yaml": ("tools", "yaml_validate.py", "yaml_validate"),
}


def _load_tool(relative_dir: str, filename: str, module_name: str):
    root = require_archharness_root()
    directory = root / relative_dir
    path = directory / filename
    sys.path.insert(0, str(directory))
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load tool: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
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

    previous_argv = sys.argv
    sys.argv = ["archharness " + name, *tool_args]
    try:
        if name == "validate-yaml" and main is not None:
            # yaml_validate.main(argv) parses its own argument list.
            result = main(tool_args)
            return int(result or 0)
        result = main()
        return int(result or 0)
    except SystemExit as exc:  # tools call sys.exit(code) for failures
        code = exc.code
        return int(code) if isinstance(code, int) else (0 if code is None else 1)
    finally:
        sys.argv = previous_argv
