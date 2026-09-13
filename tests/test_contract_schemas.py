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
    validate_manifest,
)

READERS_DIR = ROOT / "tools" / "arch-req-readers"
sys.path.insert(0, str(READERS_DIR))

from merger import merge_partial_reqs  # noqa: E402
from normalizer import (  # noqa: E402
    Confidence,
    PartialApplication,
    PartialReq,
    fv,
    partial_req_to_yaml,
)


class SchemaRegistryTests(unittest.TestCase):
    def test_known_schema_ids_load(self):
        self.assertEqual(set(SCHEMA_IDS), {"req/v1", "artifact/v1"})
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


class MergerContractTests(unittest.TestCase):
    def test_merged_output_carries_schema_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            req = PartialReq(
                source_tool="test",
                project_name=fv("Demo", Confidence.HIGH, "test"),
            )
            app = PartialApplication(id="app-1")
            app.name = fv("Demo App", Confidence.HIGH, "test")
            app.dc_or_region = fv("DC A", Confidence.HIGH, "test")
            app.country = fv("CN", Confidence.HIGH, "test")
            app.platform = fv("private_dc", Confidence.HIGH, "test")
            req.applications.append(app)
            partial = pathlib.Path(tmp) / "partial.yaml"
            partial.write_text(partial_req_to_yaml(req), encoding="utf-8")

            merged_yaml, _, _ = merge_partial_reqs([str(partial)])
            doc = yaml.safe_load(merged_yaml)
            self.assertEqual(doc["schema_version"], "req/v1")
            validate_final_req(doc)


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
