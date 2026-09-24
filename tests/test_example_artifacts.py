"""Example governance: shipped workflow state must match the files it records.

A recorded manifest is only a claim about bytes. This test resolves every
example's ``workflow-state.json`` against the example tree so a stale or
mirror-path reference cannot be committed silently.
"""

import contextlib
import io
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from archharness.arch_check import SEVERITY_ERROR, check_architecture  # noqa: E402
from archharness.registry import check_example  # noqa: E402
from archharness.trace_check import check_traceability  # noqa: E402
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

    def test_example_registries_stay_consistent(self):
        """Every example must satisfy the registry's codes-only name policy."""
        checked = 0
        for example in sorted(p for p in EXAMPLES.glob("*") if p.is_dir()):
            if not (example / "input" / "systems-registry.md").is_file():
                continue
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                errors = check_example(example)
            checked += 1
            self.assertEqual(errors, 0, f"{example.name}:\n{output.getvalue()}")
            self.assertIn("OK", output.getvalue(), f"{example.name}: {output.getvalue()}")
        self.assertGreater(checked, 0, "no example registry was checked")

    def test_example_blueprints_still_generate(self):
        """A shipped example must stay renderable by the current generator."""
        import yaml

        from archharness.diagrams.d2_generator import generate_d2
        from archharness.diagrams.generator import generate_drawio

        checked = 0
        for example in sorted(p for p in EXAMPLES.glob("*") if p.is_dir()):
            blueprint = example / "output" / "designs" / "blueprint.yaml"
            if not blueprint.is_file():
                continue
            document = yaml.safe_load(blueprint.read_text(encoding="utf-8"))
            arch = document.get("arch", document)
            checked += 1
            with self.subTest(example=example.name):
                self.assertIn("<mxfile", generate_drawio(arch))
                self.assertIn("direction:", generate_d2(arch))
        self.assertGreater(checked, 0, "no example blueprint was rendered")

    def test_example_blueprints_pass_static_architecture_checks(self):
        """Shipped models clear the deterministic checks before image review."""
        import yaml

        checked = 0
        for example in sorted(p for p in EXAMPLES.glob("*") if p.is_dir()):
            blueprint = example / "output" / "designs" / "blueprint.yaml"
            if not blueprint.is_file():
                continue
            document = yaml.safe_load(blueprint.read_text(encoding="utf-8"))
            arch = document.get("arch", document)
            errors = [
                finding for finding in check_architecture(arch)
                if finding["severity"] == SEVERITY_ERROR
            ]
            checked += 1
            self.assertEqual(errors, [], f"{example.name}: {json.dumps(errors, indent=2)}")
        self.assertGreater(checked, 0, "no example blueprint was checked")

    def test_reqv2_examples_trace_to_their_blueprints(self):
        """Typed nodes (including CN/NA view suffixes) resolve back to req/v2."""
        import yaml

        checked = 0
        for example in sorted(p for p in EXAMPLES.glob("*") if p.is_dir()):
            req_yaml = example / "output" / "requirements" / "req.yaml"
            blueprint = example / "output" / "designs" / "blueprint.yaml"
            if not req_yaml.is_file() or not blueprint.is_file():
                continue
            requirements = yaml.safe_load(req_yaml.read_text(encoding="utf-8"))
            if requirements.get("schema_version") != "req/v2":
                continue
            model = yaml.safe_load(blueprint.read_text(encoding="utf-8"))
            checked += 1
            findings = check_traceability(requirements, model)
            self.assertEqual(findings, [], f"{example.name}: {json.dumps(findings, indent=2)}")
        self.assertGreater(checked, 0, "no req/v2 example trace was checked")

    def test_example_requirements_trace_to_the_blueprint(self):
        """A migrated example must join inventory, blueprint, and deployments."""
        import yaml

        from archharness.trace_check import check_traceability

        checked = 0
        for example in sorted(p for p in EXAMPLES.glob("*") if p.is_dir()):
            requirement = example / "output" / "requirements" / "req.yaml"
            blueprint = example / "output" / "designs" / "blueprint.yaml"
            if not requirement.is_file() or not blueprint.is_file():
                continue
            requirements = yaml.safe_load(requirement.read_text(encoding="utf-8"))
            if requirements.get("schema_version") != "req/v2":
                continue
            arch = yaml.safe_load(blueprint.read_text(encoding="utf-8"))
            checked += 1
            errors = [
                finding for finding in check_traceability(requirements, arch)
                if finding["severity"] == "ERROR"
            ]
            self.assertEqual(errors, [], f"{example.name}: {json.dumps(errors, indent=2)}")
        self.assertGreater(checked, 0, "no req/v2 example was traced")

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
