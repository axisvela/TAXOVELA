"""Platform patterns: a new hosting kind must be specified, renderable, and tested.

The roadmap allows a pattern only when the standard can state physical
placement, network zones, protocol, identity, secret handling, and data
classification — so each new platform is checked for those sections, for a
validation rule set, and for a renderer palette.
"""

import pathlib
import sys
import tempfile
import unittest

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from archharness.diagrams import styles, topology  # noqa: E402
from archharness.diagrams.d2_generator import generate_d2  # noqa: E402
from archharness.diagrams.generator import generate_drawio  # noqa: E402
from archharness.diagrams.plantuml_generator import REGION_COLORS  # noqa: E402

STANDARDS = {"gcp-standard.yaml": "gcp_vpc",
             "aliyun-standard.yaml": "aliyun_vpc",
             "microsoft-saas-standard.yaml": "m365_tenant"}

#: Sections the roadmap requires before a pattern may be added.
REQUIRED_SECTIONS = ("topology", "identity", "secrets", "data")


def _arch(region_type: str) -> dict:
    return {
        "id": f"{region_type}-demo", "name": f"{region_type} demo",
        "deployment": [{
            "id": f"{region_type}-region", "type": region_type, "name": "Region",
            "location": "Example region [US]",
            "subnets": [{
                "id": "zone-a", "type": "private", "name": "Zone A",
                "components": [{"id": "CMP-01", "name": "CMP-01 | Service", "type": "BE"}],
            }],
        }],
        "interactions": [{"from": "internet", "to": "CMP-01",
                          "protocol": "HTTPS", "auth": "OIDC"}],
    }


class PlatformStandardTests(unittest.TestCase):
    def test_each_new_platform_standard_covers_the_required_sections(self):
        for filename, _region_type in STANDARDS.items():
            with self.subTest(standard=filename):
                document = yaml.safe_load(
                    (ROOT / "standards" / filename).read_text(encoding="utf-8"))
                for section in REQUIRED_SECTIONS:
                    self.assertIn(section, document, f"{filename} has no {section!r}")
                self.assertTrue(document["standard"]["applies_to"])

    def test_each_new_platform_has_validation_rules(self):
        rules = yaml.safe_load(
            (ROOT / ".claude" / "skills" / "arch-validate" / "rules"
             / "platform-rules.yaml").read_text(encoding="utf-8"))
        expected = {"gcp_rules": "E-GCP-", "aliyun_rules": "E-ALI-",
                    "microsoft_saas_rules": "E-MS-"}
        contract = {"id", "dimension", "name", "severity", "issue_type",
                    "priority", "description", "check_target", "validation_logic",
                    "impact", "suggestion"}
        for section, prefix in expected.items():
            with self.subTest(section=section):
                self.assertIn(section, rules)
                self.assertGreaterEqual(len(rules[section]), 3)
                for rule in rules[section]:
                    self.assertTrue(rule["id"].startswith(prefix))
                    self.assertEqual(contract, set(rule), "rule contract drifted")

    def test_every_platform_region_type_declares_its_zones(self):
        for _filename, region_type in STANDARDS.items():
            with self.subTest(region=region_type):
                region = {"id": "r", "type": region_type,
                          "subnets": [{"id": "z", "components": []}]}
                self.assertEqual(topology.region_zones_key(region), "subnets")
                self.assertEqual(len(topology.region_zones(region)), 1)

    def test_each_new_platform_has_a_renderer_palette(self):
        for _filename, region_type in STANDARDS.items():
            with self.subTest(region=region_type):
                self.assertIn(region_type, styles.REGION_CONTAINERS)
                self.assertIn(region_type, REGION_COLORS)
                self.assertIn(region_type, generate_drawio(_arch(region_type)))

    def test_new_platform_containers_carry_their_palette(self):
        for region_type, expected in (("gcp_vpc", "#1A73E8"), ("aliyun_vpc", "#FF6A00"),
                                      ("m365_tenant", "#D83B01"),
                                      ("power_platform", "#742774"),
                                      ("dynamics365", "#002050")):
            with self.subTest(region=region_type):
                xml = generate_drawio(_arch(region_type))
                self.assertIn(f"strokeColor={expected}", xml)

        saas = generate_d2(_arch("m365_tenant"))
        self.assertIn('stroke: "#D83B01"', saas)
        self.assertIn("stroke-dash: 6", saas)   # a SaaS tenant is a logical boundary

    def test_all_formats_render_the_new_platforms(self):
        try:
            from archharness.diagrams.png_renderer import render_png
        except ImportError as exc:
            if "matplotlib" in str(exc):
                self.skipTest("matplotlib is optional")
            raise

        for _filename, region_type in STANDARDS.items():
            with self.subTest(region=region_type):
                arch = _arch(region_type)
                self.assertIn("<mxfile", generate_drawio(arch))
                self.assertIn("direction:", generate_d2(arch))
                with tempfile.TemporaryDirectory() as tmp:
                    output = pathlib.Path(tmp) / "region.png"
                    render_png(arch, str(output), dpi=72)
                    self.assertGreater(output.stat().st_size, 1000)


if __name__ == "__main__":
    unittest.main()
