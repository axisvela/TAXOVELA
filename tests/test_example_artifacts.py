"""Example governance: shipped workflow state must match the files it records.

A recorded manifest is only a claim about bytes. This test resolves every
example's ``workflow-state.json`` against the example tree so a stale or
mirror-path reference cannot be committed silently.
"""

import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from archharness.workflow import check_state_integrity  # noqa: E402

EXAMPLES = ROOT / "examples"


class ExampleArtifactIntegrityTests(unittest.TestCase):
    def test_example_workflow_manifests_match_disk(self):
        checked = 0
        for example in sorted(p for p in EXAMPLES.glob("*") if p.is_dir()):
            state_path = example / "workflow-state.json"
            if not state_path.is_file():
                continue
            state = json.loads(state_path.read_text(encoding="utf-8"))
            findings = check_state_integrity(state, example)
            checked += 1
            self.assertEqual(
                findings, [],
                f"{example.name}: {json.dumps(findings, indent=2)}",
            )
        self.assertGreater(checked, 0, "no example workflow state was verified")

    def test_example_manifests_use_project_relative_paths(self):
        for example in sorted(p for p in EXAMPLES.glob("*") if p.is_dir()):
            state_path = example / "workflow-state.json"
            if not state_path.is_file():
                continue
            state = json.loads(state_path.read_text(encoding="utf-8"))
            for name, entry in (state.get("artifacts") or {}).items():
                if entry.get("kind") != "manifest":
                    continue
                stored = pathlib.Path(entry["data"]["path"])
                # Portable examples must never embed a machine-specific root.
                self.assertFalse(
                    stored.is_absolute(),
                    f"{example.name}: {name} stores an absolute path",
                )
                self.assertFalse(
                    str(stored).startswith(".."),
                    f"{example.name}: {name} escapes the project root",
                )


if __name__ == "__main__":
    unittest.main()
