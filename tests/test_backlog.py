"""Remediation backlog: findings grouped by the element they cite."""

import contextlib
import io
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from archharness.backlog import build_backlog, render_markdown  # noqa: E402
from archharness.cli import main as cli_main  # noqa: E402

REQUIREMENTS = {
    "schema_version": "req/v2",
    "requirements": {
        "infra": [{"id": "INF-01", "name": "Primary DC"}],
        "components": [{"id": "CMP-01", "name": "Order API", "system_id": "APP-01"},
                       {"id": "CMP-02", "name": "Order DB", "system_id": "APP-01"}],
    },
}
BLUEPRINT = {"deployment": []}
SOURCE = {"path": "output/diagrams/diagram.png", "sha256": "a" * 64, "ruleset_digest": "r" * 16}


def _issue(issue_id, subject, evidence, severity="high", disposition="must_fix"):
    return {"id": issue_id, "severity": severity, "disposition": disposition,
            "rule_id": "S-001", "dimension": "Security_Compliance",
            "subject": subject, "evidence": evidence, "confidence": "high"}


def _validation(*issues):
    return {"schema_version": "validation/v1", "source": SOURCE, "issues": list(issues)}


class BacklogTests(unittest.TestCase):
    def test_findings_group_by_the_element_they_cite(self):
        backlog = build_backlog(_validation(
            _issue("VAL-001", "CMP-01 ingress", "CMP-01 has no WAF"),
            _issue("VAL-002", "CMP-01 and CMP-02 order", "CMP-01 and CMP-02 share credentials"),
        ), REQUIREMENTS, BLUEPRINT)

        self.assertEqual(backlog["schema_version"], "backlog/v1")
        self.assertEqual(backlog["groups"]["CMP-01"], ["BL-001", "BL-002"])
        self.assertEqual(backlog["items"][0]["anchor"]["name"], "Order API")
        self.assertEqual(backlog["items"][0]["anchor"]["kind"], "component")

    def test_field_qualifier_narrows_the_anchor(self):
        backlog = build_backlog(_validation(_issue(
            "VAL-001", "CMP-02 encryption", "CMP-02.encryption_at_rest is missing")),
            REQUIREMENTS, BLUEPRINT)

        anchor = backlog["items"][0]["anchor"]
        self.assertEqual(anchor["id"], "CMP-02")
        self.assertEqual(anchor["field"], "encryption_at_rest")
        self.assertEqual(backlog["groups"]["CMP-02"], ["BL-001"])

    def test_items_are_ordered_by_severity_then_disposition(self):
        backlog = build_backlog(_validation(
            _issue("VAL-001", "CMP-02 low", "CMP-02 note", severity="low", disposition="consider"),
            _issue("VAL-002", "CMP-01 critical", "CMP-01 critical", severity="critical"),
            _issue("VAL-003", "CMP-01 should", "CMP-01 should fix", disposition="should_fix"),
        ), REQUIREMENTS, BLUEPRINT)

        self.assertEqual([item["issue_id"] for item in backlog["items"]],
                         ["VAL-002", "VAL-003", "VAL-001"])
        self.assertEqual([item["priority"] for item in backlog["items"]], [1, 2, 3])

    def test_unanchored_and_unknown_citations_are_marked(self):
        backlog = build_backlog(_validation(
            _issue("VAL-001", "legend missing", "The diagram has no legend"),
            _issue("VAL-002", "CMP-99 ghost", "CMP-99 is missing"),
        ), REQUIREMENTS, BLUEPRINT)

        unanchored, unknown = backlog["items"]
        self.assertEqual(unanchored["anchor"]["kind"], "unanchored")
        self.assertIn("no model element", unanchored["join_warning"])
        # An unknown citation is unanchored too, but it says why.
        self.assertEqual(unknown["unverified_codes"], ["CMP-99"])
        self.assertIn("does not declare", unknown["join_warning"])
        self.assertEqual(backlog["summary"]["unanchored"], 2)
        self.assertEqual(backlog["summary"]["unverified"], 1)

    def test_markdown_lists_the_anchor_and_join_warnings(self):
        backlog = build_backlog(_validation(
            _issue("VAL-001", "CMP-01 ingress", "CMP-01 has no WAF"),
            _issue("VAL-002", "legend missing", "The diagram has no legend"),
        ), REQUIREMENTS, BLUEPRINT)

        markdown = render_markdown(backlog)

        self.assertIn("CMP-01 (Order API)", markdown)
        self.assertIn("join:", markdown)
        self.assertIn("VAL-001", markdown)

    def test_cli_writes_json_and_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            validation = pathlib.Path(tmp) / "validate_result.json"
            validation.write_text(json.dumps(_validation(
                _issue("VAL-001", "CMP-01 ingress", "CMP-01 has no WAF"))), encoding="utf-8")
            requirements = pathlib.Path(tmp) / "req.yaml"
            import yaml

            requirements.write_text(yaml.safe_dump(REQUIREMENTS), encoding="utf-8")

            json_out = pathlib.Path(tmp) / "backlog.json"
            md_out = pathlib.Path(tmp) / "backlog.md"
            for target in (json_out, md_out):
                with contextlib.redirect_stdout(io.StringIO()):
                    code = cli_main(["backlog", "-v", str(validation), "-r", str(requirements),
                                     "-o", str(target)])
                self.assertEqual(code, 0)

            self.assertEqual(json.loads(json_out.read_text(encoding="utf-8"))["summary"]["items"], 1)
            self.assertIn("CMP-01", md_out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
