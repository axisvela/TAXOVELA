"""Shape coverage: the same standard shapes must render in every output format.

standards/diagram-style.yaml lists the component shapes. Adding one to the
draw.io catalogue alone would silently drop it from the PNG and D2 renderers,
so this test keeps the three formats aligned.
"""

import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from archharness.diagrams import styles  # noqa: E402
from archharness.diagrams.d2_generator import generate_d2  # noqa: E402
from archharness.diagrams.generator import generate_drawio  # noqa: E402
from archharness.diagrams.png_renderer import PNG_STANDARD_SHAPES  # noqa: E402

# Shapes the standard defines but that need no special draw.io style, so they
# are absent from styles.STANDARD_SHAPES by design.
TYPE_HANDLED_SHAPES = {"hexagon", "trapezoid", "parallelogram", "message_queue", "cylinder", "circle", "bastion"}


def _arch(shapes: list[str]) -> dict:
    return {
        "id": "shape-coverage",
        "name": "Shape Coverage",
        "deployment": [{
            "id": "dc", "type": "private_dc", "name": "DC",
            "network_zones": [{
                "id": "app", "name": "App",
                "components": [
                    {"id": f"c{index}", "name": f"Component {index}", "type": "BE", "shape": shape}
                    for index, shape in enumerate(shapes)
                ],
            }],
        }],
        "interactions": [],
    }


class ShapeCoverageTests(unittest.TestCase):
    def test_every_drawio_standard_shape_has_a_png_renderer(self):
        missing = sorted(set(styles.STANDARD_SHAPES) - set(PNG_STANDARD_SHAPES))
        self.assertEqual(missing, [], f"PNG renderer lacks a drawer for {missing}")

    def test_standard_shapes_render_in_all_text_formats(self):
        shapes = sorted(set(styles.STANDARD_SHAPES) | TYPE_HANDLED_SHAPES)
        arch = _arch(shapes)

        drawio = generate_drawio(arch)
        d2 = generate_d2(arch)

        self.assertIn("shape=pentagon", drawio)
        self.assertIn("shape=trapezoid;perimeter=trapezoidPerimeter", drawio)
        self.assertIn("shape=hexagon;perimeter=hexagonPerimeter2", drawio)
        # D2 keeps firewalls hexagonal and load balancers rectangular.
        self.assertIn("shape: hexagon", d2)

    def test_png_renders_standard_shapes(self):
        try:
            from archharness.diagrams.png_renderer import render_png
        except ImportError as exc:
            if "matplotlib" in str(exc):
                self.skipTest("matplotlib is optional")
            raise

        arch = _arch(sorted(set(styles.STANDARD_SHAPES) | TYPE_HANDLED_SHAPES))
        with tempfile.TemporaryDirectory() as directory:
            output = pathlib.Path(directory) / "shapes.png"
            render_png(arch, str(output), dpi=72)
            self.assertTrue(output.is_file())
            self.assertGreater(output.stat().st_size, 1000)


if __name__ == "__main__":
    unittest.main()
