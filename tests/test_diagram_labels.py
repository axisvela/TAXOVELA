"""Label coding (protocol / auth), status colours and zone-boundary semantics."""

import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from archharness.diagrams import labels, topology  # noqa: E402
from archharness.diagrams.generator import generate_drawio  # noqa: E402


class StatusTests(unittest.TestCase):
    def test_status_markers_are_dropped_from_text(self):
        self.assertEqual(labels.clean_protocol("HTTPS/TLS 1.3 [STATUS: TBD]"),
                         "HTTPS/TLS 1.3")
        self.assertEqual(labels.clean_protocol("Kafka/TLS [STATUS: NEW]"),
                         "Kafka/TLS")

    def test_parse_status_prefers_explicit_field(self):
        self.assertEqual(labels.parse_status({"status": "new"}), "NEW")
        self.assertEqual(
            labels.parse_status({"protocol": "Kafka/TLS [STATUS: existing]"}),
            "EXISTING")
        self.assertIsNone(labels.parse_status({"protocol": "HTTPS"}))

    def test_status_colors(self):
        self.assertEqual(labels.status_color("EXISTING"), "#1565C0")   # blue
        self.assertEqual(labels.status_color("NEW"), "#C62828")        # red
        self.assertEqual(labels.status_color("CHANGE"), "#C62828")     # red
        self.assertEqual(labels.status_color("REMOVE"), "#9E9E9E")     # grey
        self.assertEqual(labels.status_color("TBD"), "#78909C")        # blue-grey
        self.assertEqual(labels.status_color(None), labels.DEFAULT_EDGE_COLOR)


class ProtocolCodeTests(unittest.TestCase):
    def test_protocol_codes(self):
        cases = {
            "HTTPS/TLS 1.3": "P-HTTPS",
            "HTTPS/SAML 2.0": "P-HTTPS",
            "Kafka/TLS": "P-KAFKA",          # TLS alone must not imply HTTPS
            "Kafka/SASL_SSL": "P-KAFKA",
            "JDBC/PostgreSQL": "P-JDBC",
            "RFC/TLS": "P-RFC",
            "IDOC/TLS": "P-IDOC",
            "TCP/RFC": "P-RFC+P-TCP",
            "HTTPS or Kafka/TLS": "P-HTTPS+P-KAFKA",
        }
        for raw, expected in cases.items():
            self.assertEqual(labels.protocol_code(raw), expected, raw)

    def test_expanded_protocol_vocabulary_is_loaded(self):
        # Sourced from standards/diagram-codes.yaml, not hard-coded per renderer.
        cases = {
            "OPC-UA/TCP": "P-OPCUA+P-TCP",
            "Modbus/TCP": "P-MODBUS+P-TCP",
            "MQTT/TLS": "P-MQTT",
            "SFTP": "P-SFTP",
            "gRPC/TLS": "P-gRPC",
            "AMQP 1.0": "P-AMQP",
        }
        for raw, expected in cases.items():
            self.assertEqual(labels.protocol_code(raw), expected, raw)

    def test_protocol_legend(self):
        lines = labels.protocol_legend([
            {"protocol": "HTTPS [STATUS: TBD]"},
            {"protocol": "Kafka/TLS"},
            {"protocol": "HTTPS/TLS 1.3"},
        ])
        self.assertEqual(lines, ["P-HTTPS HTTPS", "P-KAFKA Kafka"])


class AuthCodeTests(unittest.TestCase):
    def test_single_method_codes_are_au_prefixed(self):
        cases = {
            "OAuth2_ClientCredentials": "AU-T1",
            "SAML 2.0 signed assertion": "AU-T3",
            "UserPassword": "AU-P1",
            "mTLS": "AU-C1",
            "SASL/SCRAM-SHA-512": "AU-S1",
            "Kerberos": "AU-K1",
            "none": "AU-N0",
            "—": "AU-N0",
        }
        for raw, expected in cases.items():
            self.assertEqual(labels.auth_code(raw), expected, raw)

    def test_composite_methods_join_with_plus(self):
        self.assertEqual(labels.auth_code("mTLS + OAuth 2.0 client credentials"),
                         "AU-T1+C1")
        self.assertEqual(
            labels.auth_code("mTLS + SASL/SCRAM-SHA-512 + topic ACL"),
            "AU-C1+S1+Z1")

    def test_expanded_auth_vocabulary_is_loaded(self):
        cases = {
            "JWT bearer token": "AU-T5",
            "SSH public key": "AU-C2",
            "SASL/PLAIN": "AU-S2",
            "SASL/OAUTHBEARER": "AU-S4",
            "NTLM Windows integrated": "AU-K2",
            "LDAP bind": "AU-P5",
            "RADIUS": "AU-P6",
            "managed identity": "AU-I2",
            "MFA / TOTP": "AU-M1",
            "FIDO2 passkey": "AU-M2",
            "RBAC": "AU-Z2",
            "IP allowlist": "AU-X3",
        }
        for raw, expected in cases.items():
            self.assertEqual(labels.auth_code(raw), expected, raw)

    def test_via_reference_is_extracted(self):
        self.assertEqual(labels.auth_via("SAML 2.0 via INF-14"), "INF-14")
        self.assertIsNone(labels.auth_via("mTLS"))

    def test_auth_legend_lists_codes_used(self):
        lines = labels.auth_legend([
            {"auth": "SAML 2.0 via INF-14"},
            {"auth": "OAuth2_ClientCredentials"},
        ])
        self.assertEqual(lines[0],
                         "T3 [Token / federation] SAML 2.0 assertion via INF-14")
        self.assertEqual(lines[1],
                         "T1 [Token / federation] OAuth2 client credentials")

    def test_edge_label_uses_codes_only(self):
        self.assertEqual(
            labels.edge_label({"protocol": "HTTPS [STATUS: TBD]",
                               "auth": "OAuth2_ClientCredentials"}),
            "P-HTTPS\n(AU-T1)")
        self.assertEqual(labels.edge_label({"protocol": "HTTPS", "auth": "—"}),
                         "P-HTTPS")


class TopologyTests(unittest.TestCase):
    def _arch(self, region_type: str) -> dict:
        return {
            "deployment": [
                {
                    "id": "dc1", "type": region_type, "location": "DC",
                    "network_zones": [
                        {
                            "id": "z1", "type": "app_zone", "name": "App",
                            "components": [
                                {"id": "INF-15", "name": "Boundary Firewall",
                                 "type": "LB"},
                                {"id": "CMP-01", "name": "API", "type": "BE"},
                            ],
                        },
                        {
                            "id": "z2", "type": "db_zone", "name": "DB",
                            "components": [{"id": "CMP-19", "name": "DB",
                                            "type": "DB"}],
                        },
                    ],
                }
            ],
        }

    def test_private_cloud_firewall_is_a_boundary(self):
        arch = self._arch("private_dc")
        self.assertEqual(topology.zone_boundary_ids(arch), {"INF-15"})
        self.assertEqual(topology.boundary_zones(arch), {"z1"})

    def test_public_cloud_firewall_is_an_ordinary_node(self):
        arch = self._arch("azure_vnet")
        self.assertEqual(topology.zone_boundary_ids(arch), set())

    def _group_arch(self) -> dict:
        """Four identical services + one with an extra edge, all under one zone."""
        services = [
            {"id": f"CMP-{i:02d}", "name": f"service-{i}", "type": "BE",
             "language": "Java (version TBD)", "runtime": "Internal K8s Platform"}
            for i in range(5, 10)
        ]
        gateway = {"id": "CMP-04", "name": "gateway", "type": "IP",
                   "shape": "parallelogram"}
        return {
            "deployment": [
                {
                    "id": "dc1", "type": "private_dc", "location": "DC",
                    "network_zones": [
                        {"id": "z1", "type": "app_zone", "name": "App",
                         "components": [gateway, *services]},
                        {"id": "z2", "type": "db_zone", "name": "DB", "components": [
                            {"id": "CMP-19", "name": "DB", "type": "DB"}]},
                    ],
                }
            ],
            "interactions": [
                *[{"from": "CMP-04", "to": s["id"], "protocol": "HTTPS",
                   "auth": "mTLS"} for s in services],
                *[{"from": s["id"], "to": "CMP-19", "protocol": "JDBC",
                   "auth": "UserPassword"} for s in services],
                # An extra relation makes CMP-09 non-interchangeable.
                {"from": "CMP-09", "to": "CMP-19", "protocol": "Kafka",
                 "auth": "SASL/SCRAM"},
            ],
        }

    def test_identical_services_collapse_into_one_group(self):
        arch, groups = topology.collapse_groups(self._group_arch())
        self.assertEqual(len(groups), 1)
        (gid, members), = groups.items()
        self.assertEqual(len(members), 4)            # CMP-09 excluded
        self.assertNotIn("CMP-09", members)

        zone = arch["deployment"][0]["network_zones"][0]
        ids = [c["id"] for c in zone["components"]]
        self.assertIn(gid, ids)
        self.assertNotIn("CMP-05", ids)
        self.assertIn("CMP-09", ids)                 # stays standalone

        # edges are rewired onto the group, so the fan-out collapses to one each
        edges = {(e["from"], e["to"]) for e in arch["interactions"]}
        self.assertIn(("CMP-04", gid), edges)
        self.assertIn((gid, "CMP-19"), edges)
        self.assertEqual(len([e for e in arch["interactions"]
                              if e["from"] == "CMP-04" and e["to"] == gid]), 1)
        self.assertEqual(len([e for e in arch["interactions"]
                              if e["from"] == gid and e["to"] == "CMP-19"]), 1)

    def test_group_needs_a_minimum_size(self):
        arch, groups = topology.collapse_groups(self._group_arch(), min_size=5)
        self.assertEqual(groups, {})

    def test_boundary_edges_are_dropped_not_reconnected(self):
        # A zone firewall is not a hub: pairing A->FW against every FW->B would
        # fabricate a complete bipartite graph, so the edges are dropped and the
        # flow must be declared directly (rule R-INF-4).
        interactions = [
            {"from": "CMP-01", "to": "INF-15", "protocol": "HTTPS"},
            {"from": "INF-15", "to": "CMP-19", "protocol": "JDBC"},
            {"from": "INF-15", "to": "CMP-20", "protocol": "JDBC"},
            {"from": "CMP-19", "to": "CMP-20", "protocol": "JDBC"},
        ]
        contracted = topology.contract(interactions, {"INF-15"})
        self.assertEqual(contracted,
                         [{"from": "CMP-19", "to": "CMP-20", "protocol": "JDBC"}])


class DrawioRenderTests(unittest.TestCase):
    def _arch(self) -> dict:
        return {
            "arch": {"id": "T-1", "name": "Label Test"},
            "deployment": [
                {
                    "id": "dc1", "type": "private_dc", "location": "DC One",
                    "network_zones": [
                        {
                            "id": "z1", "type": "app_zone", "name": "App",
                            "components": [
                                {"id": "INF-15", "name": "Boundary Firewall",
                                 "type": "LB", "runtime": "Network Appliance"},
                                {"id": "CMP-01", "name": "Order API", "type": "BE",
                                 "language": "Java (version TBD)",
                                 "framework": "Spring (version TBD)",
                                 "runtime": "Internal K8s Platform"},
                            ],
                        },
                        {
                            "id": "z2", "type": "db_zone", "name": "DB",
                            "components": [
                                {"id": "CMP-19", "name": "Order DB", "type": "DB"},
                                {"id": "CMP-20", "name": "Order DB Replica",
                                 "type": "DB"},
                            ],
                        },
                    ],
                }
            ],
            "interactions": [
                # Through the zone firewall -> contracted to CMP-01 -> CMP-19.
                {"from": "CMP-01", "to": "INF-15",
                 "protocol": "JDBC/PostgreSQL [STATUS: EXISTING]",
                 "auth": "UserPassword"},
                {"from": "INF-15", "to": "CMP-19",
                 "protocol": "JDBC/PostgreSQL [STATUS: TBD]",
                 "auth": "UserPassword"},
                # Direct in-zone edge keeps its EXISTING status.
                {"from": "CMP-19", "to": "CMP-20",
                 "protocol": "JDBC/PostgreSQL [STATUS: EXISTING]",
                 "auth": "UserPassword"},
                # Direct component-to-component flow with TBD status (blue-grey).
                {"from": "CMP-01", "to": "CMP-19",
                 "protocol": "JDBC/PostgreSQL [STATUS: TBD]",
                 "auth": "UserPassword"},
            ],
        }

    def test_zone_boundary_firewall_is_not_drawn(self):
        xml = generate_drawio(self._arch())
        visible = " ".join(re.findall(r'value="([^"]*)"', xml))
        self.assertNotIn("Boundary Firewall", visible)
        self.assertIn("App  · FW", visible)          # zone marked instead

    def test_boundary_is_contracted_out_of_the_edges(self):
        xml = generate_drawio(self._arch())
        visible = " ".join(re.findall(r'value="([^"]*)"', xml))
        self.assertIn("P-JDBC", visible)             # CMP-01 -> CMP-19 direct
        self.assertNotIn("[STATUS", visible)
        self.assertNotIn("TBD", visible)
        self.assertIn("java, spring · K8s", visible)

    def test_edge_colors_follow_status(self):
        xml = generate_drawio(self._arch())
        self.assertIn("strokeColor=#1565C0", xml)   # EXISTING blue
        self.assertIn("strokeColor=#78909C", xml)   # TBD blue-grey

    def test_legends_and_font_hierarchy(self):
        xml = generate_drawio(self._arch())
        self.assertIn("Auth codes", xml)
        self.assertIn("P1 [Password / credential] User ID / password", xml)
        self.assertIn("fontSize=14", xml)   # component labels
        self.assertIn("fontSize=9", xml)    # edge labels


if __name__ == "__main__":
    unittest.main()
