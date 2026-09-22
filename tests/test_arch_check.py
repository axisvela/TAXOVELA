"""Deterministic architecture model checks (archharness arch-check)."""

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

from archharness.arch_check import check_architecture  # noqa: E402
from archharness.cli import main as cli_main  # noqa: E402


def run_cli(*argv: str) -> tuple[int, str]:
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        code = cli_main(list(argv))
    return code, output.getvalue()


def _arch(**overrides) -> dict:
    arch = {
        "id": "demo", "name": "Demo", "platform": "private_cloud",
        "deployment": [{"id": "dc", "type": "private_dc", "name": "DC",
                        "network_zones": [{"id": "app", "name": "App", "components": [
                            {"id": "api", "name": "API", "type": "BE"},
                            {"id": "db", "name": "DB", "type": "DB"},
                        ]}]}],
        "interactions": [{"from": "api", "to": "db", "protocol": "JDBC", "auth": "mTLS"}],
    }
    arch.update(overrides)
    return arch


def rules(findings: list[dict]) -> list[str]:
    return [finding["rule"] for finding in findings]


class ArchitectureCheckTests(unittest.TestCase):
    def test_clean_model_has_no_findings(self):
        self.assertEqual(check_architecture(_arch()), [])

    def test_duplicate_ids_are_reported(self):
        arch = _arch()
        arch["deployment"][0]["network_zones"][0]["components"].append(
            {"id": "api", "name": "API again", "type": "BE"})
        findings = check_architecture(arch)
        self.assertIn("A-01", rules(findings))
        self.assertEqual(findings[0]["evidence"]["id"], "api")

    def test_undeclared_endpoint_is_reported(self):
        arch = _arch(interactions=[{"from": "api", "to": "ghost",
                                    "protocol": "HTTPS", "auth": "mTLS"}])
        self.assertIn("A-02", rules(check_architecture(arch)))

    def test_container_endpoints_are_legitimate(self):
        arch = _arch(interactions=[{"from": "api", "to": "app",
                                    "protocol": "HTTPS", "auth": "mTLS"}])
        self.assertEqual(check_architecture(arch), [])

    def test_required_edge_labels_are_enforced(self):
        arch = _arch(interactions=[{"from": "api", "to": "db"}])
        self.assertEqual(rules(check_architecture(arch)), ["A-03", "A-04"])

        # An explicit "TBD" is a value; only an absent label is a finding.
        arch = _arch(interactions=[{"from": "api", "to": "db",
                                    "protocol": "TBD", "auth": "Not applicable"}])
        self.assertEqual(check_architecture(arch), [])

    def test_self_reference_warns(self):
        arch = _arch(interactions=[{"from": "api", "to": "api",
                                    "protocol": "loopback", "auth": "mTLS"}])
        findings = check_architecture(arch)
        self.assertEqual(rules(findings), ["A-05"])
        self.assertEqual(findings[0]["severity"], "WARN")

    def test_unknown_lifecycle_status_warns(self):
        arch = _arch()
        arch["deployment"][0]["network_zones"][0]["components"][0]["status"] = "third_party"
        findings = check_architecture(arch)
        self.assertEqual(rules(findings), ["A-06"])
        self.assertEqual(findings[0]["severity"], "WARN")

    def test_standard_statuses_are_accepted(self):
        arch = _arch()
        components = arch["deployment"][0]["network_zones"][0]["components"]
        components[0]["status"] = "in_plan"
        components[1]["status"] = "unchanged"
        self.assertEqual(check_architecture(arch), [])


class ArchCheckCliTests(unittest.TestCase):
    def _write(self, directory: str, arch: dict) -> str:
        path = pathlib.Path(directory) / "arch.yaml"
        path.write_text(yaml.safe_dump({"arch": arch}), encoding="utf-8")
        return str(path)

    def test_cli_reports_and_exits_zero_when_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out = run_cli("arch-check", "-i", self._write(tmp, _arch()))
            self.assertEqual(code, 0, out)
            self.assertIn("OK", out)

    def test_cli_exits_one_on_errors_and_emits_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            arch = _arch(interactions=[{"from": "api", "to": "db"}])
            path = self._write(tmp, arch)

            code, out = run_cli("arch-check", "-i", path)
            self.assertEqual(code, 1)
            self.assertIn("A-03", out)

            code, out = run_cli("arch-check", "-i", path, "--json")
            self.assertEqual(code, 1)
            payload = json.loads(out)
            self.assertEqual(payload["schema_version"], "arch-check/v1")
            self.assertEqual(payload["errors"], 2)

    def test_cli_rejects_missing_input(self):
        code, _ = run_cli("arch-check", "-i", "does-not-exist.yaml")
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
