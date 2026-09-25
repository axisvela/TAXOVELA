"""Governance metrics: aggregation, discovery, and the privacy guarantee."""

import io
import json
import pathlib
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from archharness import cli, metrics  # noqa: E402
from archharness.schemas import SchemaError, load_schema, validate_metrics  # noqa: E402

STAMP = datetime(2026, 9, 25, 12, 0, 0, tzinfo=timezone.utc)

# Distinctive tokens that must never surface in a roll-up.
SECRET_SUBJECT = "AcmeOrderDatabase-primary"
SECRET_EVIDENCE = "password leaked in cleartext at 10.1.2.3"
SECRET_PATH = "output/diagrams/SecretPaymentsArch.png"


def _validation(**overrides) -> dict:
    doc = {
        "schema_version": "validation/v1",
        "source": {
            "path": SECRET_PATH,
            "sha256": "a" * 64,
            "media_type": "image/png",
            "validated_at": "2026-09-25T10:00:00+00:00",
            "validator_version": "arch-validate/1.0",
            "ruleset_digest": "b" * 64,
        },
        "dimensions": {
            "Security_Compliance": {"raw_score": 8.0, "weight": 2.0, "weighted_score": 1.6},
            "Connectivity": {"raw_score": 9.0, "weight": 1.0, "weighted_score": 0.9},
        },
        "issues": [
            {
                "id": "ISS-001",
                "rule_id": "S-001",
                "severity": "high",
                "disposition": "must_fix",
                "dimension": "Security_Compliance",
                "subject": SECRET_SUBJECT,
                "evidence": SECRET_EVIDENCE,
                "confidence": "high",
            },
            {
                "id": "ISS-002",
                "rule_id": "E-GCP-002",
                "severity": "medium",
                "disposition": "should_fix",
                "dimension": "Cloud_Network_Completeness",
                "subject": "edge",
                "evidence": "no label",
                "confidence": "medium",
            },
            {
                "id": "ISS-003",
                "rule_id": "V-001",
                "severity": "low",
                "disposition": "consider",
                "dimension": "Terminology_Expression",
                "subject": "legend",
                "evidence": "missing code",
                "confidence": "low",
            },
        ],
        "summary": {"total_score": 7.8, "must_fix": 1, "should_fix": 1, "consider": 1},
    }
    doc.update(overrides)
    return doc


def _enforcement(decision="WARN") -> dict:
    return {
        "schema_version": "enforcement/v1",
        "decision": decision,
        "validation": {"path": SECRET_PATH, "sha256": "a" * 64, "ruleset_digest": "b" * 64},
        "policy": {"digest": "c" * 64, "block_threshold": 6.0, "warn_threshold": 8.0,
                   "must_fix_zero_required": True},
        "evaluation": {"total_score": 7.8, "must_fix": 1, "should_fix": 1, "consider": 1},
        "reasons": [f"score 7.8 below warn threshold; {SECRET_SUBJECT} blocks"],
        "producer": "archharness/0.0.0",
        "produced_at": "2026-09-25T10:05:00+00:00",
    }


def _routing() -> dict:
    return {
        "schema_version": "routing-diagnostics/v1",
        "diagram": {"id": "d1", "name": SECRET_SUBJECT},
        "summary": {"routes": 4, "fallbacks": 1, "total_duration_ns": 4_000_000},
        "routes": [
            {"source": SECRET_SUBJECT, "target": "CMP-02", "lane": "east-west",
             "strategy": "manhattan", "fallback": False, "waypoint_count": 2,
             "duration_ns": 1_000_000},
            {"source": "CMP-02", "target": "CMP-03", "lane": "vertical",
             "strategy": "manhattan", "fallback": False, "waypoint_count": 4,
             "duration_ns": 1_000_000},
            {"source": "CMP-03", "target": "CMP-04", "lane": "vertical",
             "strategy": "manhattan", "fallback": False, "waypoint_count": 7,
             "duration_ns": 1_000_000},
            {"source": "CMP-04", "target": "CMP-05", "lane": "cross",
             "strategy": "fallback", "fallback": True, "waypoint_count": 1,
             "duration_ns": 1_000_000},
        ],
    }


class SchemaRegistrationTests(unittest.TestCase):
    def test_metrics_schema_is_registered(self):
        self.assertEqual(load_schema("metrics/v1")["version"], "metrics/v1")

    def test_bad_roll_up_is_rejected(self):
        with self.assertRaises(SchemaError):
            validate_metrics({"schema_version": "metrics/v1"})


class ValidationAggregationTests(unittest.TestCase):
    def test_findings_grouped_by_severity_disposition_and_rule_family(self):
        doc = metrics.summarize(validations=[_validation()], generated_at=STAMP)
        block = doc["validation"]

        self.assertEqual(block["reports"], 1)
        self.assertEqual(block["findings_total"], 3)
        self.assertEqual(block["by_severity"]["high"], 1)
        self.assertEqual(block["by_severity"]["medium"], 1)
        self.assertEqual(block["by_rule_family"], {"S": 1, "E": 1, "V": 1})
        self.assertEqual(block["by_dimension"]["Security_Compliance"], 1)
        self.assertEqual(block["scores"]["must_fix"], 1)
        self.assertEqual(block["scores"]["samples"], 1)
        self.assertEqual(block["scores"]["mean_total_score"], 7.8)

    def test_score_range_across_reports(self):
        second = _validation()
        second["summary"] = {"total_score": 9.2, "must_fix": 0}
        doc = metrics.summarize(validations=[_validation(), second], generated_at=STAMP)
        scores = doc["validation"]["scores"]
        self.assertEqual(scores["samples"], 2)
        self.assertEqual(scores["min_total_score"], 7.8)
        self.assertEqual(scores["max_total_score"], 9.2)


class RoutingAggregationTests(unittest.TestCase):
    def test_fallback_and_readability_are_counted(self):
        doc = metrics.summarize(routings=[_routing()], generated_at=STAMP)
        block = doc["routing"]

        self.assertEqual(block["edges_total"], 4)
        self.assertEqual(block["fallback_edges"], 1)
        self.assertEqual(block["fallback_ratio"], 0.25)
        self.assertEqual(block["waypoint_buckets"], {"<=2": 2, "3-5": 1, ">=6": 1})
        # one fallback + one >=6-waypoint edge
        self.assertEqual(block["readability_defects"], 2)
        self.assertEqual(block["total_planning_ms"], 4.0)


class WorkflowAndTurnaroundTests(unittest.TestCase):
    def _state(self) -> dict:
        return {
            "artifacts": {
                "req.yaml": {"kind": "manifest", "data": {
                    "schema_version": "artifact/v1", "id": "req", "type": "requirements",
                    "schema": "req/v1", "path": "req.yaml", "sha256": "d" * 64,
                    "produced_at": "2026-09-25T09:00:00+00:00"}},
                "blueprint.yaml": {"kind": "manifest", "data": {
                    "schema_version": "artifact/v1", "id": "design", "type": "design",
                    "schema": "req/v1", "path": "blueprint.yaml", "sha256": "e" * 64,
                    "produced_at": "2026-09-25T09:30:00+00:00"}},
                "enforce_result.json": {"kind": "decision", "data": _enforcement()},
            },
            "stages_completed": ["requirements", "design"],
        }

    def _spec(self) -> dict:
        return {"pipeline": [
            {"id": "requirements", "produces": ["req.yaml"]},
            {"id": "design", "requires": ["req.yaml"], "produces": ["blueprint.yaml"]},
            {"id": "draw", "requires": ["blueprint.yaml"], "produces": ["diagram.png"]},
            {"id": "validate", "requires": ["diagram.png"], "produces": ["validate_result.json"]},
            {"id": "enforce", "requires": ["validate_result.json"],
             "produces": ["enforce_result.json"]},
        ]}

    def test_completion_and_enforce_decision(self):
        doc = metrics.summarize(state=self._state(), spec=self._spec(), generated_at=STAMP)
        workflow = doc["workflow"]
        self.assertEqual(workflow["stages_total"], 5)
        self.assertEqual(workflow["stages_completed"], 2)
        self.assertEqual(workflow["completion_ratio"], 0.4)
        self.assertEqual(workflow["enforce_decision"], "WARN")
        self.assertEqual(workflow["artifacts_recorded"], 3)

    def test_turnaround_uses_manifest_and_decision_timestamps(self):
        doc = metrics.summarize(
            validations=[_validation()],
            enforcements=[_enforcement()],
            state=self._state(),
            spec=self._spec(),
            generated_at=STAMP,
        )
        transitions = doc["turnaround"]["transitions"]
        self.assertEqual(transitions["requirements->design"]["median_seconds"], 1800.0)
        # validated 10:00 -> produced 10:05
        self.assertEqual(transitions["validate->enforce"]["median_seconds"], 300.0)


class PrivacyTests(unittest.TestCase):
    def test_roll_up_contains_no_payload_text(self):
        document = metrics.summarize(
            validations=[_validation()],
            enforcements=[_enforcement()],
            routings=[_routing()],
            generated_at=STAMP,
        )
        rendered = json.dumps(document)
        for secret in (SECRET_SUBJECT, SECRET_EVIDENCE, SECRET_PATH, "SecretPaymentsArch"):
            self.assertNotIn(secret, rendered)
        self.assertEqual(document["privacy"]["payload_fields"], "excluded")

    def test_markdown_contains_no_payload_text(self):
        document = metrics.summarize(validations=[_validation()], generated_at=STAMP)
        rendered = metrics.render_markdown(document)
        self.assertNotIn(SECRET_SUBJECT, rendered)
        self.assertNotIn(SECRET_PATH, rendered)


class DiscoveryTests(unittest.TestCase):
    def test_documents_are_classified_by_schema_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "validation").mkdir()
            (root / "validation" / "validate_result.json").write_text(
                json.dumps(_validation()), encoding="utf-8")
            (root / "validation" / "enforce_result.json").write_text(
                json.dumps(_enforcement()), encoding="utf-8")
            (root / "routes.json").write_text(json.dumps(_routing()), encoding="utf-8")
            (root / "notes.json").write_text('{"hello": "world"}', encoding="utf-8")

            found = metrics.discover_documents(root)
            self.assertEqual(len(found["validation"]), 1)
            self.assertEqual(len(found["enforcement"]), 1)
            self.assertEqual(len(found["routing"]), 1)
            self.assertEqual(found["manifests"], [])


class CliTests(unittest.TestCase):
    def test_json_roll_up_from_explicit_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            vpath = pathlib.Path(tmp) / "validate_result.json"
            vpath.write_text(json.dumps(_validation()), encoding="utf-8")
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                code = cli.main(["metrics", "--validation", str(vpath), "--json"])
            self.assertEqual(code, 0)
            document = json.loads(buffer.getvalue())
            validate_metrics(document)
            self.assertEqual(document["validation"]["findings_total"], 3)
            self.assertNotIn(SECRET_SUBJECT, buffer.getvalue())

    def test_no_artifacts_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            empty = pathlib.Path(tmp) / "empty.json"
            empty.write_text("{}", encoding="utf-8")
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                code = cli.main(["metrics", "--validation", str(empty)])
            self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
