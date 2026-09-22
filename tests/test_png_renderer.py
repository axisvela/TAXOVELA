"""Regression test for package-relative PNG renderer imports."""

import pathlib
import struct
import tempfile
import unittest

import yaml


ROOT = pathlib.Path(__file__).resolve().parents[1]


class PngRendererTests(unittest.TestCase):
    def test_render_png_imports_layout_inside_package(self):
        try:
            from archharness.diagrams.png_renderer import render_png
        except ImportError as exc:
            if "matplotlib" in str(exc):
                self.skipTest("matplotlib is optional")
            raise

        arch = {
            "metadata": {"title": "Smoke"},
            "deployment": [
                {
                    "id": "dc",
                    "name": "DC",
                    "type": "private_dc",
                    "network_zones": [
                        {
                            "id": "app",
                            "name": "App Zone",
                            "components": [
                                {"id": "svc", "name": "Service", "type": "BE"}
                            ],
                        }
                    ],
                }
            ],
            "interactions": [],
        }
        with tempfile.TemporaryDirectory() as directory:
            output = pathlib.Path(directory) / "smoke.png"
            render_png(arch, str(output), dpi=72)
            self.assertTrue(output.is_file())
            self.assertGreater(output.stat().st_size, 0)

    def test_multidc_png_has_a_nontrivial_canvas(self):
        try:
            from archharness.diagrams.png_renderer import render_png
        except ImportError as exc:
            if "matplotlib" in str(exc):
                self.skipTest("matplotlib is optional")
            raise

        arch = {
            "id": "visual-routing-demo",
            "name": "Visual Routing Demo",
            "platform": "private_cloud",
            "deployment": [
                {"id": "dc-a", "name": "DC A", "type": "private_dc",
                 "network_zones": [{"id": "app", "name": "App", "components": [
                     {"id": "api", "name": "API", "type": "BE"},
                 ]}]},
                {"id": "dc-b", "name": "DC B", "type": "private_dc",
                 "network_zones": [{"id": "data", "name": "Data", "components": [
                     {"id": "database", "name": "Database", "type": "DB"},
                 ]}]},
            ],
            "interactions": [
                {"from": "api", "to": "database", "protocol": "JDBC", "auth": "mTLS"},
                {"from": "database", "to": "api", "protocol": "JDBC", "auth": "mTLS"},
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            output = pathlib.Path(directory) / "multidc.png"
            render_png(arch, str(output), dpi=72)
            with output.open("rb") as image:
                self.assertEqual(image.read(8), b"\x89PNG\r\n\x1a\n")
                length = struct.unpack(">I", image.read(4))[0]
                self.assertEqual(image.read(4), b"IHDR")
                width, height = struct.unpack(">II", image.read(length)[:8])
            self.assertGreater(width, 400)
            self.assertGreater(height, 250)

    def test_factory_mes_example_renders_to_png(self):
        """Keep the large multi-DC reference architecture renderable."""
        try:
            from archharness.diagrams.png_renderer import render_png
        except ImportError as exc:
            if "matplotlib" in str(exc):
                self.skipTest("matplotlib is optional")
            raise

        blueprint = ROOT / "examples" / "06-factory-mes-industrial" / "output" / "designs" / "blueprint.yaml"
        with blueprint.open(encoding="utf-8") as source:
            document = yaml.safe_load(source)
        arch = document["arch"]

        with tempfile.TemporaryDirectory() as directory:
            output = pathlib.Path(directory) / "factory-mes.png"
            render_png(arch, str(output), dpi=72)
            self.assertTrue(output.is_file())
            # A raster of this reference must contain the complete multi-DC
            # canvas rather than a degenerate or truncated render.
            self.assertGreater(output.stat().st_size, 30_000)


if __name__ == "__main__":
    unittest.main()
