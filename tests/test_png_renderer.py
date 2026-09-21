"""Regression test for package-relative PNG renderer imports."""

import pathlib
import tempfile
import unittest


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


if __name__ == "__main__":
    unittest.main()
