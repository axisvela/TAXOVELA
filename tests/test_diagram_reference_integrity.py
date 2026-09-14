"""Milestone 0: diagram reference integrity must fail closed."""

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from archharness.diagrams.generator import generate_drawio  # noqa: E402
from archharness.diagrams.d2_generator import generate_d2  # noqa: E402
from archharness.diagrams.plantuml_generator import generate_plantuml  # noqa: E402


def _valid_arch():
    return {
        "id": "demo",
        "name": "Demo",
        "platform": "private_cloud",
        "deployment": [
            {
                "id": "dc-a",
                "type": "private_dc",
                "name": "DC A",
                "network_zones": [
                    {
                        "id": "zone-app",
                        "type": "app_zone",
                        "name": "App Zone",
                        "components": [
                            {"id": "api", "name": "API", "type": "BE"},
                            {"id": "web", "name": "Web", "type": "BE"},
                        ],
                    }
                ],
            },
            {
                "id": "dc-b",
                "type": "private_dc",
                "name": "DC B",
                "network_zones": [
                    {
                        "id": "zone-db",
                        "type": "db_zone",
                        "name": "DB Zone",
                        "components": [
                            {"id": "db", "name": "DB", "type": "DB"},
                        ],
                    }
                ],
            },
        ],
        "interactions": [
            {"from": "web", "to": "api", "protocol": "HTTPS", "auth": "OAuth2"},
            {"from": "api", "to": "db", "protocol": "JDBC", "auth": "mTLS"},
        ],
    }


class DiagramReferenceIntegrityTests(unittest.TestCase):
    def test_valid_arch_renders_all_backends(self):
        arch = _valid_arch()
        self.assertIn("API", generate_drawio(arch))
        self.assertIn("DB", generate_drawio(arch))
        self.assertIn("HTTPS", generate_drawio(arch))
        self.assertIn("api", generate_d2(arch))
        self.assertIn("API", generate_plantuml(arch))

    def test_two_private_dcs_do_not_infer_mpls(self):
        arch = _valid_arch()
        xml = generate_drawio(arch)
        self.assertNotIn("MPLS", xml)

    def test_unresolved_interaction_fails_closed(self):
        arch = _valid_arch()
        arch["interactions"].append({"from": "api", "to": "missing-svc", "protocol": "HTTPS"})
        with self.assertRaises(ValueError):
            generate_drawio(arch)
        with self.assertRaises(ValueError):
            generate_d2(arch)
        with self.assertRaises(ValueError):
            generate_plantuml(arch)

    def test_duplicate_ids_fail_closed(self):
        arch = _valid_arch()
        arch["deployment"][1]["network_zones"][0]["components"].append(
            {"id": "api", "name": "Duplicate API", "type": "BE"}
        )
        with self.assertRaises(ValueError):
            generate_drawio(arch)
        with self.assertRaises(ValueError):
            generate_d2(arch)
        with self.assertRaises(ValueError):
            generate_plantuml(arch)


class AssembleDataContractTests(unittest.TestCase):
    def test_wheel_includes_runtime_config(self):
        scripts_dir = pathlib.Path(__file__).resolve().parents[1] / "scripts"
        sys.path.insert(0, str(scripts_dir))
        import assemble_data

        self.assertIn("config.yaml", assemble_data.SOURCES)
        self.assertIn("config.example.yaml", assemble_data.SOURCES)
        self.assertEqual(
            assemble_data.SOURCES["config.yaml"],
            assemble_data.ROOT / "config.yaml",
        )


if __name__ == "__main__":
    unittest.main()
