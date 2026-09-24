"""Schema evolution: a breaking change under an existing contract id is caught."""

import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from archharness.cli import main as cli_main  # noqa: E402
from archharness.schema_check import ADDITIVE, BREAKING, compare_schemas, entities  # noqa: E402

BASELINE = {
    "$defs": {
        "component": {
            "properties": {"id": {"type": "string"}, "name": {"type": "string"},
                           "layer": {"enum": ["fe", "be"]}},
            "required": ["id", "name"],
        }
    },
    "properties": {"issues": {"type": "array", "items": {
        "properties": {"id": {"type": "string"}, "severity": {"enum": ["high", "low"]}},
        "required": ["id"]}}},
}


def kinds(findings: list[dict], kind: str) -> list[str]:
    return [finding["detail"] for finding in findings if finding["kind"] == kind]


class SchemaComparisonTests(unittest.TestCase):
    def test_identical_schemas_have_no_findings(self):
        self.assertEqual(compare_schemas(BASELINE, BASELINE, "demo.json"), [])

    def test_entities_include_array_item_properties(self):
        found = entities(BASELINE)

        self.assertIn("component", found)
        self.assertIn("issues", found)
        self.assertEqual(found["issues"]["required"], {"id"})

    def test_removed_property_is_breaking(self):
        candidate = json.loads(json.dumps(BASELINE))
        del candidate["$defs"]["component"]["properties"]["name"]
        candidate["$defs"]["component"]["required"] = ["id"]

        findings = compare_schemas(BASELINE, candidate, "demo.json")

        self.assertEqual(kinds(findings, BREAKING), ["component.name was removed"])

    def test_new_required_property_is_breaking(self):
        candidate = json.loads(json.dumps(BASELINE))
        candidate["$defs"]["component"]["properties"]["owner"] = {"type": "string"}
        candidate["$defs"]["component"]["required"] = ["id", "name", "owner"]

        findings = compare_schemas(BASELINE, candidate, "demo.json")

        self.assertIn("component.owner was added as required", kinds(findings, BREAKING))

    def test_new_optional_property_is_additive(self):
        candidate = json.loads(json.dumps(BASELINE))
        candidate["$defs"]["component"]["properties"]["notes"] = {"type": "string"}

        findings = compare_schemas(BASELINE, candidate, "demo.json")

        self.assertEqual(kinds(findings, ADDITIVE), ["component.notes was added"])
        self.assertEqual(kinds(findings, BREAKING), [])

    def test_enum_narrowing_is_breaking_and_widening_is_additive(self):
        candidate = json.loads(json.dumps(BASELINE))
        candidate["$defs"]["component"]["properties"]["layer"]["enum"] = ["fe", "be", "ip"]

        widened = compare_schemas(BASELINE, candidate, "demo.json")
        self.assertEqual(kinds(widened, ADDITIVE), ["component.layer accepts 'ip'"])

        narrowed = compare_schemas(candidate, BASELINE, "demo.json")
        self.assertIn("component.layer dropped 'ip'", kinds(narrowed, BREAKING))

    def test_type_change_is_breaking(self):
        candidate = json.loads(json.dumps(BASELINE))
        candidate["$defs"]["component"]["properties"]["id"] = {"type": "integer"}

        findings = compare_schemas(BASELINE, candidate, "demo.json")

        self.assertIn("component.id changed type 'string' → 'integer'",
                      kinds(findings, BREAKING))

    def test_new_definition_is_additive(self):
        candidate = json.loads(json.dumps(BASELINE))
        candidate["$defs"]["stack"] = {"properties": {"id": {"type": "string"}}}

        findings = compare_schemas(BASELINE, candidate, "demo.json")

        self.assertIn("definition added to demo.json", kinds(findings, ADDITIVE))


class SchemaCheckCliTests(unittest.TestCase):
    def _run(self, *argv):
        import contextlib
        import io

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = cli_main(list(argv))
        return code, output.getvalue()

    def test_repository_schemas_are_unchanged_against_head(self):
        code, output = self._run("schema-check", "--baseline", "HEAD")

        self.assertEqual(code, 0, output)
        self.assertIn("no breaking schema change", output)

    def test_additive_change_against_a_directory_is_reported(self):
        """The shipped schema gained a field since the baseline: additive only."""
        with tempfile.TemporaryDirectory() as tmp:
            baseline_dir = pathlib.Path(tmp)
            document = json.loads(
                (ROOT / "schemas" / "req-v2.schema.json").read_text(encoding="utf-8"))
            baseline = json.loads(json.dumps(document))
            del baseline["$defs"]["component"]["properties"]["encryption_at_rest"]
            (baseline_dir / "req-v2.schema.json").write_text(
                json.dumps(baseline), encoding="utf-8")

            code, output = self._run("schema-check", "--baseline", str(baseline_dir),
                                     "--schema", "req-v2")

        self.assertEqual(code, 0, output)
        self.assertIn("component.encryption_at_rest was added", output)
        self.assertIn("no breaking schema change", output)

    def test_strict_mode_rejects_additive_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            baseline_dir = pathlib.Path(tmp)
            document = json.loads(
                (ROOT / "schemas" / "enforcement-v1.schema.json").read_text(encoding="utf-8"))
            candidate = json.loads(json.dumps(document))
            candidate["$defs"] = {"extra": {"properties": {"id": {"type": "string"}}}}
            (baseline_dir / "enforcement-v1.schema.json").write_text(
                json.dumps(candidate), encoding="utf-8")

            code, _output = self._run("schema-check", "--baseline", str(baseline_dir),
                                      "--schema", "enforcement-v1", "--strict")

        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
