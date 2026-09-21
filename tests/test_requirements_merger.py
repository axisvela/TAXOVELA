"""Contract tests for req/v2 partial requirements merging and reference resolution."""

import pathlib
import sys
import tempfile
import unittest

import yaml


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from archharness.requirements.merger import merge_partial_reqs  # noqa: E402
from archharness.requirements.normalizer import (  # noqa: E402
    Confidence,
    PartialAuth,
    PartialComponent,
    PartialDeployment,
    PartialFlow,
    PartialInfra,
    PartialNetworkLink,
    PartialReq,
    PartialSystem,
    fv,
    partial_req_to_yaml,
    v2_json_to_partial,
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
        H = Confidence.HIGH
        req = PartialReq(
            source_tool="test",
            source_file=source,
            project_name=fv("Payments", H, source),
            project_id=fv("payments", H, source),
            project_scope=fv("standalone", H, source),
            department=fv("Finance", H, source),
            credentials=[{"environment": "private_dc", "solution": "JKS"}],
            constraints=["No public database access"],
            open_items=[{"id": "TBD-01", "description": "Confirm DR RTO", "blocking": False}],
        )

        infra_a = PartialInfra(id="i1")
        infra_a.name = fv("DC A", H, source)
        infra_a.node_kind = fv("data_center", H, source)
        infra_a.infra_type = fv("private_cloud", H, source)
        infra_a.country = fv("CN", H, source)
        req.infra.append(infra_a)

        infra_b = PartialInfra(id="i2")
        infra_b.name = fv("DC B", H, source)
        infra_b.node_kind = fv("data_center", H, source)
        infra_b.infra_type = fv("private_cloud", H, source)
        req.infra.append(infra_b)

        system = PartialSystem(id="s1")
        system.name = fv("Payments App", H, source)
        system.type = fv("existing", H, source)
        system.owner = fv("org_it", H, source)
        req.systems.append(system)

        component = PartialComponent(id="c1")
        component.system = fv("Payments App", H, source)
        component.name = fv("Payment API", H, source)
        component.kind = fv("service", H, source)
        component.component_role = fv("backend_service", H, source)
        component.encryption_at_rest = fv("AES-256", H, source)
        req.components.append(component)

        deployment = PartialDeployment(id="d1")
        deployment.component = fv("Payment API", H, source)
        deployment.environment = fv("prod", H, source)
        deployment.deployment_type = fv("private_cloud", H, source)
        deployment.location_type = fv("data_center", H, source)
        deployment.infra = fv("DC A", H, source)
        deployment.runtime_type = fv("container", H, source)
        req.deployments.append(deployment)

        flow = PartialFlow(id="f1")
        flow.source = fv("internet", H, source)
        flow.target = fv("Payment API", H, source)
        flow.protocol = fv("HTTPS", H, source)
        flow.port = fv("443", H, source)
        flow.auth_method = fv("none", H, source)
        flow.encryption = fv("TLS1.3", H, source)
        req.flows.append(flow)

        link = PartialNetworkLink(id="l1")
        link.source_infra = fv("DC A", H, source)
        link.target_infra = fv("DC B", H, source)
        link.method = fv("expressroute", H, source)
        link.redundancy = fv("primary", H, source)
        req.network_links.append(link)

        auth = PartialAuth(id="a1")
        auth.subject = fv("user", H, source)
        auth.applies_to = fv("Payment API", H, source)
        auth.protocol = fv("OIDC", H, source)
        auth.authorization = fv("RBAC", H, source)
        req.auth.append(auth)
        return req

    def test_single_source_emits_req_v2_with_typed_ids(self):
        partial = self._write_partial("partial.yaml", self._complete_partial())

        merged_yaml, gap_report, gaps = merge_partial_reqs([partial])
        doc = yaml.safe_load(merged_yaml)
        requirements = doc["requirements"]

        self.assertEqual(doc["schema_version"], "req/v2")
        self.assertEqual(requirements["project"]["name"], "Payments")

        # Typed IDs assigned per entity kind
        self.assertEqual([i["id"] for i in requirements["infra"]], ["INF-01", "INF-02"])
        self.assertEqual(requirements["systems"][0]["id"], "APP-01")
        self.assertEqual(requirements["components"][0]["id"], "CMP-01")
        self.assertEqual(requirements["deployments"][0]["id"], "DEP-01")
        self.assertEqual(requirements["flows"][0]["id"], "FLOW-01")
        self.assertEqual(requirements["network_links"][0]["id"], "LNK-01")
        self.assertEqual(requirements["auth"][0]["id"], "AUTH-01")

        # Name references resolved to typed IDs
        self.assertEqual(requirements["components"][0]["system_id"], "APP-01")
        self.assertEqual(requirements["deployments"][0]["infra_id"], "INF-01")
        self.assertEqual(requirements["deployments"][0]["component_id"], "CMP-01")
        self.assertEqual(requirements["flows"][0]["source_component_id"], "internet")
        self.assertEqual(requirements["flows"][0]["target_component_id"], "CMP-01")
        self.assertEqual(requirements["network_links"][0]["source_infra_id"], "INF-01")
        self.assertEqual(requirements["network_links"][0]["target_infra_id"], "INF-02")
        self.assertEqual(requirements["auth"][0]["applies_to"], "CMP-01")

        # Field preservation
        self.assertEqual(requirements["components"][0]["encryption_at_rest"], "AES-256")
        self.assertEqual(requirements["credentials"][0]["solution"], "JKS")
        self.assertEqual(requirements["open_items"][0]["id"], "TBD-01")
        self.assertIn("Requirements Gap Report", gap_report)

    def test_multiple_sources_merge_entities_without_duplicates(self):
        first = self._complete_partial("document:first")
        first.components[0].sensitivity = None
        second = self._complete_partial("cmdb:second")
        second.components[0].sensitivity = fv("Company Confidential",
                                              Confidence.MANUAL, "cmdb:second")

        files = [
            self._write_partial("first.yaml", first),
            self._write_partial("second.yaml", second),
        ]
        merged_yaml, _, _ = merge_partial_reqs(files)
        requirements = yaml.safe_load(merged_yaml)["requirements"]

        self.assertEqual(len(requirements["infra"]), 2)
        self.assertEqual(len(requirements["systems"]), 1)
        self.assertEqual(len(requirements["components"]), 1)
        self.assertEqual(len(requirements["flows"]), 1)
        self.assertEqual(requirements["components"][0]["sensitivity"],
                         "Company Confidential")

    def test_unresolved_reference_is_a_critical_gap(self):
        partial_req = self._complete_partial()
        partial_req.flows[0].target = fv("Ghost Service", Confidence.HIGH, "document:test")
        partial = self._write_partial("partial.yaml", partial_req)

        merged_yaml, _, gaps = merge_partial_reqs([partial])
        requirements = yaml.safe_load(merged_yaml)["requirements"]

        self.assertEqual(requirements["flows"], [])
        self.assertTrue(any("Ghost Service" in g for g in gaps["critical"]))

    def test_prod_deployment_without_infra_is_a_critical_gap(self):
        partial_req = self._complete_partial()
        partial_req.deployments[0].infra = fv("Unknown DC", Confidence.HIGH, "document:test")
        partial = self._write_partial("partial.yaml", partial_req)

        merged_yaml, _, gaps = merge_partial_reqs([partial])
        requirements = yaml.safe_load(merged_yaml)["requirements"]

        self.assertNotIn("infra_id", requirements["deployments"][0])
        self.assertTrue(any("infra_id missing for prod" in g for g in gaps["critical"]))

    def test_appliance_label_is_not_a_component(self):
        """A single JSON extraction through the shared mapper classifies appliances."""
        extracted = {
            "project": {"name": "Demo"},
            "infra": [
                {"name": "DC A", "node_kind": "data_center", "infra_type": "private_cloud"},
                {"name": "F5 BigIP", "node_kind": "load_balancer", "parent": "DC A"},
            ],
            "systems": [{"name": "Demo App", "type": "new"}],
            "components": [
                {"system": "Demo App", "name": "Order API", "kind": "service",
                 "component_role": "backend_service"},
            ],
            "flows": [
                {"from": "internet", "to": "Order API", "protocol": "HTTPS",
                 "auth_method": "none", "via": ["F5 BigIP"]},
            ],
        }
        partial = v2_json_to_partial(extracted, "test-reader", "inline.yaml",
                                     Confidence.HIGH, "test")
        self.assertEqual([i.name.value for i in partial.infra], ["DC A", "F5 BigIP"])
        self.assertEqual([c.name.value for c in partial.components], ["Order API"])

        path = self._write_partial("mapped.yaml", partial)
        merged_yaml, _, _ = merge_partial_reqs([path])
        requirements = yaml.safe_load(merged_yaml)["requirements"]
        self.assertEqual([i["node_kind"] for i in requirements["infra"]],
                         ["data_center", "load_balancer"])
        self.assertEqual(requirements["flows"][0]["via"], ["INF-02"])


if __name__ == "__main__":
    unittest.main()
