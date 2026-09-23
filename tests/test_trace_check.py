"""req/v2 to blueprint traceability checks."""

import contextlib
import io
import json
import pathlib
import sys
import tempfile
import unittest

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from archharness.cli import main as cli_main  # noqa: E402
from archharness.trace_check import check_traceability  # noqa: E402


def requirements() -> dict:
    return {
        "schema_version": "req/v2",
        "requirements": {
            "infra": [
                {"id": "INF-01", "country": "CN"},
                {"id": "INF-02", "country": "US"},
            ],
            "components": [{"id": "CMP-01"}],
            "deployments": [
                {"id": "DEP-01", "component_id": "CMP-01", "infra_id": "INF-01"},
                {"id": "DEP-02", "component_id": "CMP-01", "infra_id": "INF-02"},
            ],
        },
    }


def blueprint(*nodes: str) -> dict:
    return {
        "arch": {
            "deployment": [{"id": "dc", "type": "private_dc", "network_zones": [{
                "id": "app", "components": [
                    {"id": node, "name": node, "type": "BE"} for node in nodes
                ],
            }]}],
        },
    }


class TraceCheckTests(unittest.TestCase):
    def test_bare_and_site_qualified_ids_resolve(self):
        self.assertEqual(check_traceability(requirements(), blueprint("INF-01", "CMP-01-CN", "CMP-01-NA")), [])

    def test_unknown_typed_node_is_an_error(self):
        findings = check_traceability(requirements(), blueprint("CMP-99"))
        self.assertEqual(findings[0]["rule"], "T-01")

    def test_site_suffix_requires_a_matching_deployment_country(self):
        findings = check_traceability(requirements(), blueprint("CMP-01-DE"))
        self.assertEqual(findings[0]["rule"], "T-02")

    def test_non_reqv2_input_is_an_error(self):
        self.assertEqual(check_traceability({"schema_version": "req/v1"}, blueprint("CMP-01"))[0]["rule"], "T-00")


class TraceCheckCliTests(unittest.TestCase):
    def test_cli_json_and_exit_codes(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = pathlib.Path(directory)
            req_path, bp_path = directory / "req.yaml", directory / "bp.yaml"
            req_path.write_text(yaml.safe_dump(requirements()), encoding="utf-8")
            bp_path.write_text(yaml.safe_dump(blueprint("CMP-99")), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = cli_main(["trace-check", "-r", str(req_path), "-b", str(bp_path), "--json"])
            self.assertEqual(code, 1)
            self.assertEqual(json.loads(output.getvalue())["findings"][0]["rule"], "T-01")


if __name__ == "__main__":
    unittest.main()
