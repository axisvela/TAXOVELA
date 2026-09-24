"""Design templates must be renderable, catalogued, and consistent with the model.

A template that cannot render is worse than no template: the shipped
Microsoft 365 template held its components directly under a SaaS region, which
the generator cannot place, so every interaction reference failed. These tests
keep the catalog and the generator in agreement.
"""

import pathlib
import sys
import unittest

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from archharness.arch_check import SEVERITY_ERROR, check_architecture  # noqa: E402
from archharness.diagrams import styles, topology  # noqa: E402
from archharness.diagrams.d2_generator import generate_d2  # noqa: E402
from archharness.diagrams.generator import generate_drawio  # noqa: E402
from archharness.diagrams.plantuml_generator import generate_plantuml  # noqa: E402

TEMPLATE_DIR = ROOT / "tools" / "arch-diagram-gen" / "templates"


def templates() -> list[pathlib.Path]:
    return sorted(p for p in TEMPLATE_DIR.glob("*.yaml") if p.name != "CATALOG.yaml")


def load(path: pathlib.Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


class TemplateTests(unittest.TestCase):
    def test_catalog_lists_every_template(self):
        catalog = load(TEMPLATE_DIR / "CATALOG.yaml")
        listed = sorted(pathlib.Path(entry["file"]).name for entry in catalog["templates"])

        self.assertEqual(listed, [path.name for path in templates()])

    def test_every_template_renders_in_every_format(self):
        for path in templates():
            with self.subTest(template=path.name):
                arch = load(path)["arch"]
                self.assertIn("<mxfile", generate_drawio(arch))
                self.assertIn("direction:", generate_d2(arch))
                self.assertIn("@startuml", generate_plantuml(arch))

    def test_every_template_passes_the_static_model_checks(self):
        for path in templates():
            with self.subTest(template=path.name):
                errors = [finding for finding in check_architecture(load(path)["arch"])
                          if finding["severity"] == SEVERITY_ERROR]
                self.assertEqual(errors, [], f"{path.name}: {errors}")

    def test_template_components_live_inside_a_zone(self):
        """Components directly under a region are dropped by the layout."""
        for path in templates():
            arch = load(path)["arch"]
            for region in topology.deployment_of(arch):
                with self.subTest(template=path.name, region=region.get("id")):
                    self.assertFalse(
                        region.get("components"),
                        f"{path.name}: region {region.get('id')!r} holds components "
                        "outside a zone")

    def test_every_region_kind_used_has_a_palette(self):
        for path in templates():
            arch = load(path)["arch"]
            for region in topology.deployment_of(arch):
                with self.subTest(template=path.name, region=region.get("id")):
                    region_type = region.get("type", "private_dc")
                    self.assertIn(region_type, styles.REGION_CONTAINERS,
                                  f"{region_type!r} has no renderer palette")

    def test_templates_declare_their_standard_and_use_when(self):
        for path in templates():
            document = load(path)
            with self.subTest(template=path.name):
                self.assertIn("_template", document)
                self.assertTrue(document["_template"].get("use_when"))
                self.assertTrue(document["_template"].get("typical_stack"))


if __name__ == "__main__":
    unittest.main()
