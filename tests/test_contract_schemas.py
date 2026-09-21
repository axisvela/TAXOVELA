"""Milestone 1: versioned contract schemas and artifact manifests."""

import pathlib
import sys
import tempfile
import unittest

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from archharness.artifacts import make_manifest, verify_manifest  # noqa: E402
from archharness.schemas import (  # noqa: E402
    SCHEMA_IDS,
    SchemaError,
    load_schema,
    validate,
    validate_final_req,
    validate_final_req_v2,
    validate_manifest,
    validate_validation_result,
)

from archharness.requirements.merger import merge_partial_reqs  # noqa: E402
from archharness.requirements.normalizer import (  # noqa: E402
    Confidence,
    PartialInfra,
    PartialReq,
    PartialSystem,
    fv,
    partial_req_to_yaml,
)


class SchemaRegistryTests(unittest.TestCase):
    def test_known_schema_ids_load(self):
        self.assertEqual(
            set(SCHEMA_IDS),
            {"req/v1", "req/v2", "artifact/v1", "validation/v1", "enforcement/v1"},
        )
        for schema_id in SCHEMA_IDS:
            schema = load_schema(schema_id)
            self.assertEqual(schema["version"], schema_id)

    def test_unknown_schema_rejected(self):
        with self.assertRaises(SchemaError):
            validate({}, "req/v9")

    def test_req_schema_rejects_missing_project(self):
        doc = {"schema_version": "req/v1", "requirements": {"applications": []}}
        with self.assertRaises(SchemaError):
            validate_final_req(doc)

    def test_req_schema_rejects_wrong_version(self):
        doc = {"schema_version": "req/v0", "requirements": {}}
        with self.assertRaises(SchemaError):
            validate_final_req(doc)

    def test_manifest_rejects_bad_hash(self):
        manifest = {
            "schema_version": "artifact/v1",
            "id": "m1",
            "type": "requirements",
            "schema": "req/v1",
            "path": "output/requirements/req.yaml",
            "sha256": "not-a-hash",
        }
        with self.assertRaises(SchemaError):
            validate_manifest(manifest)


def _valid_req_v2() -> dict:
    """Minimal req/v2 document exercising $ref, inline enums and sentinels."""
    return {
        "schema_version": "req/v2",
        "requirements": {
            "project": {"name": "Demo"},
            "infra": [
                {
                    "id": "INF-01",
                    "name": "Azure East US",
                    "node_kind": "region",
                    "infra_type": "public_cloud",
                    "network_type": None,
                }
            ],
            "systems": [{"id": "APP-01", "name": "Demo App", "type": "new"}],
            "components": [
                {
                    "id": "CMP-01",
                    "system_id": "APP-01",
                    "name": "Order API",
                    "kind": "service",
                    "component_role": "backend_service",
                }
            ],
            "deployments": [
                {
                    "id": "DEP-01",
                    "component_id": "CMP-01",
                    "environment": "prod",
                    "deployment_type": "public_cloud",
                    "location_type": "public_cloud_region",
                    "infra_id": "INF-01",
                    "runtime_type": "container",
                }
            ],
            "flows": [
                {
                    "id": "FLOW-01",
                    "source_component_id": "internet",
                    "target_component_id": "CMP-01",
                    "protocol": "HTTPS",
                    "auth_method": "none",
                    "encryption": "TLS1.3",
                    "via": ["INF-01"],
                    "notes": "external user ingress; user auth = AUTH-01",
                }
            ],
            "network_links": [
                {
                    "id": "LNK-01",
                    "source_infra_id": "INF-01",
                    "target_infra_id": "INF-01",
                    "method": "expressroute",
                }
            ],
            "auth": [
                {
                    "id": "AUTH-01",
                    "subject": "user",
                    "protocol": "OIDC",
                    "applies_to": "CMP-01",
                }
            ],
        },
    }


class ReqV2ContractTests(unittest.TestCase):
    def test_valid_doc_passes(self):
        validate_final_req_v2(_valid_req_v2())

    def test_missing_collection_fails(self):
        doc = _valid_req_v2()
        del doc["requirements"]["flows"]
        with self.assertRaises(SchemaError):
            validate_final_req_v2(doc)

    def test_wrong_id_prefix_fails(self):
        doc = _valid_req_v2()
        doc["requirements"]["components"][0]["id"] = "INF-01"
        with self.assertRaises(SchemaError):
            validate_final_req_v2(doc)

    def test_bad_flow_auth_method_fails(self):
        doc = _valid_req_v2()
        doc["requirements"]["flows"][0]["auth_method"] = "LDAP"
        with self.assertRaises(SchemaError):
            validate_final_req_v2(doc)

    def test_missing_flow_auth_method_fails(self):
        doc = _valid_req_v2()
        del doc["requirements"]["flows"][0]["auth_method"]
        with self.assertRaises(SchemaError):
            validate_final_req_v2(doc)

    def test_unexpected_key_fails(self):
        doc = _valid_req_v2()
        doc["requirements"]["infra"][0]["bogus"] = "x"
        with self.assertRaises(SchemaError):
            validate_final_req_v2(doc)

    def test_bad_via_endpoint_fails(self):
        doc = _valid_req_v2()
        doc["requirements"]["flows"][0]["via"] = ["CMP-01"]
        with self.assertRaises(SchemaError):
            validate_final_req_v2(doc)


def _valid_validation_result() -> dict:
    return {
        "schema_version": "validation/v1",
        "source": {
            "path": "output/diagrams/payment.png",
            "sha256": "a" * 64,
            "media_type": "image/png",
            "validated_at": "2026-09-13T14:00:00+00:00",
            "validator_version": "arch-validate/1.0",
            "ruleset_digest": "b" * 64,
        },
        "dimensions": {
            "Security_Compliance": {"raw_score": 8.5, "weight": 2.0, "weighted_score": 1.7},
            "Connectivity": {"raw_score": 9.0, "weight": 1.0, "weighted_score": 0.9},
        },
        "issues": [
            {
                "id": "ISS-001",
                "rule_id": "S-001",
                "severity": "high",
                "disposition": "must_fix",
                "dimension": "Security_Compliance",
                "subject": "edge api->db",
                "evidence": "no auth label",
                "confidence": "high",
            }
        ],
        "summary": {"total_score": 7.8, "must_fix": 1, "should_fix": 0, "consider": 2},
    }


class ValidationContractTests(unittest.TestCase):
    def test_valid_result_passes(self):
        validate_validation_result(_valid_validation_result())

    def test_missing_source_digest_fails(self):
        doc = _valid_validation_result()
        del doc["source"]["ruleset_digest"]
        with self.assertRaises(SchemaError):
            validate_validation_result(doc)

    def test_bad_severity_fails(self):
        doc = _valid_validation_result()
        doc["issues"][0]["severity"] = "Critical"
        with self.assertRaises(SchemaError):
            validate_validation_result(doc)

    def test_raw_score_out_of_range_fails(self):
        doc = _valid_validation_result()
        doc["dimensions"]["Connectivity"]["raw_score"] = 11
        with self.assertRaises(SchemaError):
            validate_validation_result(doc)

    def test_empty_dimensions_fails(self):
        doc = _valid_validation_result()
        doc["dimensions"] = {}
        with self.assertRaises(SchemaError):
            validate_validation_result(doc)


class MergerContractTests(unittest.TestCase):
    def test_merged_output_carries_schema_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            req = PartialReq(
                source_tool="test",
                project_name=fv("Demo", Confidence.HIGH, "test"),
            )
            infra = PartialInfra(id="infra-1")
            infra.name = fv("DC A", Confidence.HIGH, "test")
            infra.node_kind = fv("data_center", Confidence.HIGH, "test")
            infra.infra_type = fv("private_cloud", Confidence.HIGH, "test")
            infra.country = fv("CN", Confidence.HIGH, "test")
            req.infra.append(infra)

            system = PartialSystem(id="system-1")
            system.name = fv("Demo App", Confidence.HIGH, "test")
            system.type = fv("new", Confidence.HIGH, "test")
            req.systems.append(system)

            partial = pathlib.Path(tmp) / "partial.yaml"
            partial.write_text(partial_req_to_yaml(req), encoding="utf-8")

            merged_yaml, _, _ = merge_partial_reqs([str(partial)])
            doc = yaml.safe_load(merged_yaml)
            self.assertEqual(doc["schema_version"], "req/v2")
            validate_final_req_v2(doc)


class ArtifactManifestTests(unittest.TestCase):
    def test_manifest_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp) / "req.yaml"
            target.write_text("schema_version: req/v1\n", encoding="utf-8")
            manifest = make_manifest(
                artifact_id="req-demo",
                artifact_type="requirements",
                schema="req/v1",
                path=target,
                project_root=tmp,
                producer="archharness/test",
                input_artifacts=["partial-1"],
            )
            self.assertEqual(manifest["schema_version"], "artifact/v1")
            self.assertEqual(len(manifest["sha256"]), 64)
            self.assertEqual(manifest["path"], "req.yaml")
            self.assertTrue(verify_manifest(manifest, tmp))

            target.write_text("tampered\n", encoding="utf-8")
            self.assertFalse(verify_manifest(manifest, tmp))


if __name__ == "__main__":
    unittest.main()
