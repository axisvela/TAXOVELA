"""Reading an architecture YAML back into req/v2 requirements.

The diagram reader must emit entities the merger can resolve, otherwise a
complete model yields an empty requirements document.
"""

import contextlib
import io
import pathlib
import sys
import tempfile
import unittest

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from archharness.requirements.command import main as req_main  # noqa: E402
from archharness.requirements.merger import merge_partial_reqs  # noqa: E402
from archharness.requirements.normalizer import partial_req_to_yaml  # noqa: E402
from archharness.schemas import validate_final_req_v2  # noqa: E402

ARCH = {
    "arch": {
        "id": "demo-v1", "name": "Demo Platform", "platform": "private_cloud",
        "deployment": [{
            "id": "dc-a", "type": "private_dc", "name": "DC A",
            "location": "Primary DC, City A [CN]", "owner": "InfraSec",
            "network_zones": [{
                "id": "app", "type": "app_zone", "name": "App Zone",
                "components": [
                    {"id": "api", "name": "api | Gateway", "type": "IP",
                     "component_role": "api_gateway", "sensitivity": "Acme Confidential"},
                    {"id": "db", "name": "db | PostgreSQL", "type": "DB",
                     "component_role": "database", "encryption_at_rest": "AES-256"},
                ],
            }],
        }],
        "interactions": [
            {"from": "internet", "to": "api", "protocol": "HTTPS", "auth": "OAuth2.0"},
            {"from": "api", "to": "db", "protocol": "PostgreSQL", "auth": "UserPassword"},
        ],
        "security": {
            "key_management": {"private_dc": "Enterprise vault", "partner_keys": "Short-lived SSH"},
            "user_auth_internal": {"server": "ADFS", "protocol": "SAML 2.0"},
        },
    },
}


class DiagramToRequirementsTests(unittest.TestCase):
    def _read(self, document: dict) -> dict:
        from archharness.requirements.from_diagram import parse_arch_yaml

        return parse_arch_yaml(document, "arch.yaml")

    def test_flow_endpoints_use_the_emitted_component_labels(self):
        partial = self._read(ARCH)

        labels = {component.name.value for component in partial.components}
        self.assertEqual(labels, {"api | Gateway", "db | PostgreSQL"})
        endpoints = {flow.source.value for flow in partial.flows}
        endpoints |= {flow.target.value for flow in partial.flows}
        self.assertIn("api | Gateway", endpoints)
        self.assertIn("internet", endpoints)   # virtual nodes pass through

    def test_merge_keeps_every_flow(self):
        partial = self._read(ARCH)
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "partial.yaml"
            path.write_text(partial_req_to_yaml(partial), encoding="utf-8")

            merged_yaml, _report, _gaps = merge_partial_reqs([str(path)])

        doc = yaml.safe_load(merged_yaml)
        validate_final_req_v2(doc)
        flows = doc["requirements"]["flows"]
        self.assertEqual(len(flows), 2)
        self.assertEqual(
            {(flow["source_component_id"], flow["target_component_id"]) for flow in flows},
            {("internet", "CMP-01"), ("CMP-01", "CMP-02")},
        )

    def test_key_store_labels_are_normalised_to_the_contract(self):
        partial = self._read(ARCH)
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "partial.yaml"
            path.write_text(partial_req_to_yaml(partial), encoding="utf-8")
            merged_yaml, _report, gaps = merge_partial_reqs([str(path)])

        credentials = yaml.safe_load(merged_yaml)["requirements"]["credentials"]
        environments = {row["environment"] for row in credentials}
        self.assertEqual(environments, {"private_dc", "other"})
        self.assertNotIn("_source", credentials[0])
        self.assertTrue(
            any("partner_keys" in gap for gap in gaps["critical"]),
            "an unmapped key store must be reported, not silently renamed",
        )

    def test_cli_reads_a_blueprint_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = pathlib.Path(tmp) / "blueprint.yaml"
            source.write_text(yaml.safe_dump(ARCH), encoding="utf-8")
            output = pathlib.Path(tmp) / "req.yaml"
            report = pathlib.Path(tmp) / "gaps.md"

            with contextlib.redirect_stdout(io.StringIO()):
                code = req_main(["--diagram", str(source), "-o", str(output),
                                 "--report", str(report)])

            self.assertEqual(code, 0)
            doc = yaml.safe_load(output.read_text(encoding="utf-8"))
            validate_final_req_v2(doc)
            self.assertEqual(len(doc["requirements"]["flows"]), 2)


if __name__ == "__main__":
    unittest.main()
