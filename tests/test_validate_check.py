"""Evidence checks: a validation finding must be joinable to the model."""

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from archharness.validate_check import check_findings, model_ids  # noqa: E402

REQUIREMENTS = {
    "schema_version": "req/v2",
    "requirements": {
        "infra": [{"id": "INF-01"}, {"id": "INF-02"}],
        "components": [{"id": "CMP-01"}],
        "deployments": [{"id": "DEP-01", "component_id": "CMP-01", "infra_id": "INF-02"}],
    },
}
BLUEPRINT = {
    "deployment": [{
        "id": "dc-a",
        "type": "private_dc",
        "network_zones": [{
            "id": "zone-a",
            "components": [{"id": "CMP-01"}, {"id": "INF-03"}],
        }],
    }],
}


def _validation(*issues: dict) -> dict:
    return {"schema_version": "validation/v1", "issues": list(issues)}


def _issue(issue_id: str, subject: str, evidence: str) -> dict:
    return {"id": issue_id, "severity": "high", "disposition": "must_fix",
            "subject": subject, "evidence": evidence}


def rules(findings: list[dict]) -> list[str]:
    return [finding["rule"] for finding in findings]


class EvidenceCheckTests(unittest.TestCase):
    def test_model_ids_include_inventory_containers_and_nodes(self):
        ids = model_ids(REQUIREMENTS, BLUEPRINT)

        self.assertIn("CMP-01", ids)
        self.assertIn("DEP-01", ids)
        self.assertIn("INF-03", ids)   # a node that only the blueprint declares
        self.assertIn("zone-a", ids)   # a container the finding may name

    def test_finding_citing_a_known_code_passes(self):
        validation = _validation(_issue("VAL-001", "CMP-01 ingress", "CMP-01 has no WAF in front"))

        self.assertEqual(check_findings(validation, REQUIREMENTS, BLUEPRINT), [])

    def test_finding_citing_an_unknown_code_is_an_error(self):
        validation = _validation(_issue("VAL-002", "CMP-99 missing", "CMP-99 is not deployed"))

        findings = check_findings(validation, REQUIREMENTS, BLUEPRINT)

        self.assertEqual(rules(findings), ["V-01"])
        self.assertEqual(findings[0]["severity"], "ERROR")
        self.assertEqual(findings[0]["evidence"]["unknown_codes"], ["CMP-99"])

    def test_unanchored_finding_warns(self):
        validation = _validation(_issue("VAL-003", "legend missing", "The diagram has no legend"))

        findings = check_findings(validation, REQUIREMENTS, BLUEPRINT)

        self.assertEqual(rules(findings), ["V-02"])
        self.assertEqual(findings[0]["severity"], "WARN")

    def test_legacy_id_space_warns(self):
        validation = _validation(_issue("VAL-004", "SYS-05 mediation", "SYS-05 must mediate"))

        findings = check_findings(validation, REQUIREMENTS, BLUEPRINT)

        self.assertEqual(rules(findings), ["V-03"])
        self.assertEqual(findings[0]["evidence"]["legacy_codes"], ["SYS-05"])

    def test_wrong_document_version_is_rejected(self):
        findings = check_findings({"schema_version": "requirements/v1"})

        self.assertEqual(rules(findings), ["V-00"])


if __name__ == "__main__":
    unittest.main()
