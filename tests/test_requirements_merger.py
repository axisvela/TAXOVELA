"""Contract tests for partial requirements finalization and field preservation."""

import pathlib
import sys
import tempfile
import unittest

import yaml


READERS_DIR = pathlib.Path(__file__).resolve().parents[1] / "tools" / "arch-req-readers"
sys.path.insert(0, str(READERS_DIR))

from merger import merge_partial_reqs  # noqa: E402
from normalizer import (  # noqa: E402
    Confidence,
    PartialApplication,
    PartialComponent,
    PartialInteraction,
    PartialReq,
    PartialUserAuth,
    fv,
    partial_req_to_yaml,
)


class RequirementsMergerTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = pathlib.Path(self._tmp.name)

    def _write_partial(self, name: str, req: PartialReq) -> str:
        path = self.root / name
        path.write_text(partial_req_to_yaml(req), encoding="utf-8")
        return str(path)

    def _complete_partial(self, source: str = "document:test") -> PartialReq:
        req = PartialReq(
            source_tool="test",
            source_file=source,
            project_name=fv("Payments", Confidence.HIGH, source),
            project_id=fv("payments", Confidence.HIGH, source),
            project_scope=fv("standalone", Confidence.HIGH, source),
            department=fv("Finance", Confidence.HIGH, source),
            credentials=[{"component": "api", "solution": "JKS"}],
            data_encryption=[{"data": "customer", "at_rest": "AES-256"}],
            network_connections=[{
                "from": "dc-a", "to": "azure", "type": "ExpressRoute"
            }],
            constraints=["No public database access"],
            open_items=[{"question": "Confirm DR RTO"}],
        )

        app = PartialApplication(id="app-1")
        app.name = fv("Payments App", Confidence.HIGH, source)
        app.type = fv("existing", Confidence.HIGH, source)
        app.owner = fv("org_it", Confidence.HIGH, source)
        app.vendor = fv("Internal", Confidence.HIGH, source)
        app.dc_or_region = fv("DC A", Confidence.HIGH, source)
        app.country = fv("CN", Confidence.HIGH, source)
        app.platform = fv("private_dc", Confidence.HIGH, source)
        app.zone_subnet = fv("App Zone", Confidence.HIGH, source)
        app.infra_owner = fv("InfraSec", Confidence.HIGH, source)
        req.applications.append(app)

        component = PartialComponent(id="api", app_id="app-1")
        component.name = fv("Payment API", Confidence.HIGH, source)
        component.comp_type = fv("BE", Confidence.HIGH, source)
        component.runtime = fv("Kubernetes", Confidence.HIGH, source)
        req.components.append(component)

        interaction = PartialInteraction(id="int-1")
        interaction.from_component = fv("portal", Confidence.HIGH, source)
        interaction.to_component = fv("api", Confidence.HIGH, source)
        interaction.protocol = fv("HTTPS", Confidence.HIGH, source)
        interaction.port = fv("443", Confidence.HIGH, source)
        interaction.auth_method = fv("OAuth2", Confidence.HIGH, source)
        interaction.notes = fv("Customer payment request", Confidence.HIGH, source)
        req.interactions.append(interaction)

        user_auth = PartialUserAuth(entry_point="portal")
        user_auth.user_roles = fv(["customer"], Confidence.HIGH, source)
        user_auth.auth_server = fv("Enterprise ID", Confidence.HIGH, source)
        user_auth.auth_protocol = fv("OIDC", Confidence.HIGH, source)
        user_auth.authorization = fv("RBAC", Confidence.HIGH, source)
        user_auth.auth_platform = fv("AuthZ", Confidence.HIGH, source)
        req.user_auth.append(user_auth)
        return req

    def test_single_source_uses_final_schema_and_preserves_fields(self):
        partial = self._write_partial("partial.yaml", self._complete_partial())

        merged_yaml, gap_report, gaps = merge_partial_reqs([partial])
        requirements = yaml.safe_load(merged_yaml)["requirements"]

        self.assertEqual(requirements["project"]["name"], "Payments")
        self.assertEqual(requirements["applications"][0]["vendor"], "Internal")
        self.assertEqual(
            requirements["interactions"][0]["notes"],
            "Customer payment request",
        )
        self.assertEqual(requirements["user_auth"][0]["auth_platform"], "AuthZ")
        self.assertEqual(
            requirements["network_connections"][0]["type"],
            "ExpressRoute",
        )
        self.assertEqual(
            requirements["open_items"],
            [{"question": "Confirm DR RTO"}],
        )
        self.assertNotIn("User authentication not defined", "\n".join(gaps["critical"]))
        self.assertIn("Requirements Gap Report", gap_report)

    def test_multiple_sources_merge_user_auth_fields_without_duplicates(self):
        first = self._complete_partial("document:first")
        first.user_auth[0].auth_platform = None
        second = self._complete_partial("cmdb:second")
        second.user_auth[0].auth_platform = fv(
            "Enterprise AuthZ", Confidence.MANUAL, "cmdb:second"
        )

        files = [
            self._write_partial("first.yaml", first),
            self._write_partial("second.yaml", second),
        ]
        merged_yaml, _, _ = merge_partial_reqs(files)
        requirements = yaml.safe_load(merged_yaml)["requirements"]

        self.assertEqual(len(requirements["user_auth"]), 1)
        self.assertEqual(
            requirements["user_auth"][0]["auth_platform"],
            "Enterprise AuthZ",
        )
        self.assertEqual(len(requirements["network_connections"]), 1)


if __name__ == "__main__":
    unittest.main()
