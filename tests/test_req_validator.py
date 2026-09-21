"""Cross-field validation tests for req/v2 requirements documents (rules V1-V7)."""

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

from archharness.requirements.validator import (  # noqa: E402
    Finding,
    main as validator_main,
    validate_requirements,
)


def _doc() -> dict:
    return {
        "schema_version": "req/v2",
        "requirements": {
            "project": {"name": "Demo"},
            "infra": [
                {"id": "INF-01", "name": "Region", "node_kind": "region",
                 "infra_type": "private_cloud"},
                {"id": "INF-02", "name": "DC A", "node_kind": "data_center",
                 "infra_type": "private_cloud", "parent_id": "INF-01"},
                {"id": "INF-03", "name": "App Zone", "node_kind": "network_zone",
                 "network_type": "prod_network", "parent_id": "INF-02"},
                {"id": "INF-04", "name": "KMS", "node_kind": "key_management",
                 "parent_id": "INF-03"},
                {"id": "INF-05", "name": "F5 BigIP", "node_kind": "load_balancer",
                 "parent_id": "INF-03"},
                {"id": "INF-06", "name": "ADFS", "node_kind": "identity_provider",
                 "parent_id": "INF-03"},
            ],
            "systems": [{"id": "APP-01", "name": "Demo App", "type": "new"}],
            "components": [
                {"id": "CMP-01", "system_id": "APP-01", "name": "API", "kind": "service",
                 "component_role": "backend_service", "key_management": "INF-04"},
                {"id": "CMP-02", "system_id": "APP-01", "name": "DB", "kind": "component",
                 "component_role": "database"},
            ],
            "deployments": [
                {"id": "DEP-01", "component_id": "CMP-01", "environment": "prod",
                 "deployment_type": "private_cloud", "location_type": "data_center",
                 "infra_id": "INF-03", "runtime_type": "container"},
            ],
            "flows": [
                {"id": "FLOW-01", "source_component_id": "internet",
                 "target_component_id": "CMP-01", "protocol": "HTTPS",
                 "auth_method": "none", "encryption": "TLS1.3", "via": ["INF-05"]},
                {"id": "FLOW-02", "source_component_id": "CMP-01",
                 "target_component_id": "CMP-02", "protocol": "JDBC",
                 "auth_method": "UserPassword"},
            ],
            "network_links": [
                {"id": "LNK-01", "source_infra_id": "INF-02",
                 "target_infra_id": "INF-01", "method": "mpls"},
            ],
            "auth": [
                {"id": "AUTH-01", "subject": "user", "protocol": "OIDC",
                 "applies_to": "CMP-01", "auth_server": "INF-06"},
            ],
            "ecosystem_relations": [
                {"id": "ECO-01", "source_system_id": "APP-01",
                 "target_system_id": "APP-01", "relation_type": "downstream"},
            ],
        },
    }


def _rules(findings: list[Finding]) -> set[str]:
    return {f.rule_id for f in findings}


class ReqValidatorTests(unittest.TestCase):
    def test_valid_document_has_no_findings(self):
        self.assertEqual(validate_requirements(_doc()), [])

    def test_schema_error_is_reported(self):
        doc = _doc()
        del doc["requirements"]["project"]["name"]
        findings = validate_requirements(doc)
        self.assertEqual(_rules(findings), {"SCHEMA"})

    def test_duplicate_id_is_v1(self):
        doc = _doc()
        doc["requirements"]["components"][1]["id"] = "CMP-01"
        self.assertIn("V1", _rules(validate_requirements(doc)))

    def test_unresolved_infra_reference_is_v2(self):
        doc = _doc()
        doc["requirements"]["deployments"][0]["infra_id"] = "INF-99"
        self.assertIn("V2", _rules(validate_requirements(doc)))

    def test_unresolved_ecosystem_system_is_v2(self):
        doc = _doc()
        doc["requirements"]["ecosystem_relations"][0]["source_system_id"] = "APP-99"
        self.assertIn("V2", _rules(validate_requirements(doc)))

    def test_bad_infra_containment_is_v3(self):
        doc = _doc()
        doc["requirements"]["infra"][2]["parent_id"] = "INF-01"  # zone under region
        self.assertIn("V3", _rules(validate_requirements(doc)))

    def test_region_with_parent_is_v3(self):
        doc = _doc()
        doc["requirements"]["infra"][0]["parent_id"] = "INF-02"
        self.assertIn("V3", _rules(validate_requirements(doc)))

    def test_key_management_wrong_kind_is_v4(self):
        doc = _doc()
        doc["requirements"]["components"][0]["key_management"] = "INF-02"  # a DC
        self.assertIn("V4", _rules(validate_requirements(doc)))

    def test_unresolved_flow_endpoint_is_v5(self):
        doc = _doc()
        doc["requirements"]["flows"][1]["target_component_id"] = "CMP-99"
        self.assertIn("V5", _rules(validate_requirements(doc)))

    def test_unresolved_network_link_endpoint_is_v5(self):
        doc = _doc()
        doc["requirements"]["network_links"][0]["target_infra_id"] = "INF-99"
        self.assertIn("V5", _rules(validate_requirements(doc)))

    def test_prod_deployment_without_infra_is_v6(self):
        doc = _doc()
        del doc["requirements"]["deployments"][0]["infra_id"]
        self.assertIn("V6", _rules(validate_requirements(doc)))

    def test_external_flow_without_auth_is_v7(self):
        doc = _doc()
        doc["requirements"]["auth"] = []
        self.assertIn("V7", _rules(validate_requirements(doc)))

    def test_cli_exit_codes_and_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            good = pathlib.Path(tmp) / "good.yaml"
            good.write_text(yaml.safe_dump(_doc()), encoding="utf-8")
            self.assertEqual(validator_main([str(good)]), 0)

            bad = pathlib.Path(tmp) / "bad.yaml"
            broken = _doc()
            del broken["requirements"]["deployments"][0]["infra_id"]
            bad.write_text(yaml.safe_dump(broken), encoding="utf-8")

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = validator_main([str(bad), "--json"])
            self.assertEqual(code, 1)
            payload = json.loads(output.getvalue())
            self.assertGreaterEqual(payload["errors"], 1)
            self.assertIn("V6", {f["rule_id"] for f in payload["findings"]})


if __name__ == "__main__":
    unittest.main()
