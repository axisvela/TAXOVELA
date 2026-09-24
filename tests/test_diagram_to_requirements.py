"""Reading an architecture YAML back into req/v2 requirements.

The diagram reader must emit entities the merger can resolve, otherwise a
complete model yields an empty requirements document.
"""

import contextlib
import copy
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
        "deployment": [
            {
                "id": "dc-a", "type": "private_dc", "name": "DC A",
                "location": "Primary DC, City A [CN]", "owner": "InfraSec",
                "role": "production",
                "network_zones": [
                    {
                        "id": "app", "type": "app_zone", "name": "App Zone",
                        "components": [
                            {"id": "api", "name": "api | Gateway", "type": "IP",
                             "component_role": "api_gateway",
                             "sensitivity": "Acme Confidential",
                             "runtime": "Internal K8s Platform"},
                            {"id": "db", "name": "db | PostgreSQL", "type": "DB",
                             "component_role": "database", "encryption_at_rest": "AES-256"},
                            {"id": "idp", "name": "idp | Directory", "type": "SEC"},
                        ],
                    },
                    {"id": "intra", "type": "intranet", "name": "Intranet", "components": []},
                ],
            },
            {
                "id": "dc-b", "type": "private_dc", "name": "DC B",
                "location": "Secondary DC, City B [CN]",
                "network_zones": [
                    {"id": "intra-b", "type": "intranet", "name": "Intranet", "components": []},
                ],
            },
        ],
        "interactions": [
            {"from": "internet", "to": "api", "protocol": "HTTPS", "auth": "OAuth2.0"},
            {"from": "api", "to": "db", "protocol": "PostgreSQL", "auth": "UserPassword"},
            {"from": "dc-a", "to": "dc-b", "protocol": "MPLS with IPsec"},
        ],
        "security": {
            "key_management": {"private_dc": "Enterprise vault", "partner_keys": "Short-lived SSH"},
            "user_auth_internal": {"server": "idp | Directory", "protocol": "SAML 2.0"},
            "user_auth_external": {"server": "api | Gateway",
                                   "protocol": "OIDC / OAuth2.0 Authorization Code"},
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
        self.assertEqual(labels, {"api | Gateway", "db | PostgreSQL", "idp | Directory"})
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

    def test_deployments_are_extracted_per_component(self):
        partial = self._read(ARCH)

        self.assertEqual(len(partial.deployments), 3)
        gateway = partial.deployments[0]
        self.assertEqual(gateway.component.value, "api | Gateway")
        self.assertEqual(gateway.environment.value, "production")
        self.assertEqual(gateway.deployment_type.value, "private_cloud")
        self.assertEqual(gateway.infra.value, "App Zone")
        self.assertEqual(gateway.runtime_type.value, "container")

        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "partial.yaml"
            path.write_text(partial_req_to_yaml(partial), encoding="utf-8")
            merged_yaml, _report, _gaps = merge_partial_reqs([str(path)])

        deployments = yaml.safe_load(merged_yaml)["requirements"]["deployments"]
        self.assertEqual(len(deployments), 3)
        self.assertEqual(deployments[0]["component_id"], "CMP-01")
        self.assertEqual(deployments[0]["infra_id"], "INF-02")
        self.assertEqual(deployments[0]["environment"], "prod")

    def test_repeated_zone_labels_are_disambiguated(self):
        partial = self._read(ARCH)
        names = [infra.name.value for infra in partial.infra]

        self.assertIn("Intranet (dc-a)", names)
        self.assertIn("Intranet (dc-b)", names)
        self.assertEqual(len(names), len(set(names)), "infra names must be unique")

        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "partial.yaml"
            path.write_text(partial_req_to_yaml(partial), encoding="utf-8")
            merged_yaml, _report, _gaps = merge_partial_reqs([str(path)])

        infra = yaml.safe_load(merged_yaml)["requirements"]["infra"]
        # Every zone resolves to its own DC rather than being displaced.
        zones = {row["name"]: row.get("parent_id") for row in infra
                 if row.get("node_kind") == "network_zone"}
        self.assertEqual(zones["Intranet (dc-a)"], "INF-01")
        self.assertEqual(zones["Intranet (dc-b)"], "INF-04")
        self.assertEqual(len(infra), 5)

    def test_container_interactions_become_network_links(self):
        partial = self._read(ARCH)

        self.assertEqual(len(partial.network_links), 1)
        link = partial.network_links[0]
        self.assertEqual(link.source_infra.value, "Primary DC, City A [CN]")
        self.assertEqual(link.target_infra.value, "Secondary DC, City B [CN]")
        self.assertEqual(link.method.value, "mpls")
        # A link is not a component flow.
        self.assertEqual(len(partial.flows), 2)

        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "partial.yaml"
            path.write_text(partial_req_to_yaml(partial), encoding="utf-8")
            merged_yaml, _report, _gaps = merge_partial_reqs([str(path)])

        links = yaml.safe_load(merged_yaml)["requirements"]["network_links"]
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0]["source_infra_id"], "INF-01")
        self.assertEqual(links[0]["target_infra_id"], "INF-04")
        self.assertEqual(links[0]["method"], "mpls")

    def test_user_and_office_sources_normalise_to_internet(self):
        arch = copy.deepcopy(ARCH)
        arch["arch"]["interactions"] = [
            {"from": "user", "to": "api", "protocol": "HTTPS", "auth": "OIDC"},
            {"from": "office-network", "to": "api", "protocol": "HTTPS", "auth": "OIDC"},
        ]

        partial = self._read(arch)

        self.assertEqual([flow.source.value for flow in partial.flows], ["internet", "internet"])

    def test_auth_declarations_anchor_to_the_ingress_component(self):
        partial = self._read(ARCH)

        self.assertEqual(len(partial.auth), 2)
        protocols = {row.protocol.value for row in partial.auth}
        self.assertEqual(protocols, {"SAML2", "OIDC"})
        for row in partial.auth:
            self.assertEqual(row.applies_to.value, "api | Gateway")

        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "partial.yaml"
            path.write_text(partial_req_to_yaml(partial), encoding="utf-8")
            merged_yaml, _report, _gaps = merge_partial_reqs([str(path)])

        auth = yaml.safe_load(merged_yaml)["requirements"]["auth"]
        # Two providers on one entry point are two declarations, not a conflict.
        self.assertEqual(len(auth), 2)
        self.assertEqual({row["applies_to"] for row in auth}, {"CMP-01"})
        self.assertEqual({row["auth_server"] for row in auth}, {"CMP-01", "CMP-03"})

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
