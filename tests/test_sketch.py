"""One-shot sketches: DSL parsing, model compilation, CLI/API delivery."""

import contextlib
import io
import pathlib
import sys
import tempfile
import unittest

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from archharness import api  # noqa: E402
from archharness.cli import main as cli_main  # noqa: E402
from archharness.diagrams.generator import validate_architecture_refs  # noqa: E402
from archharness.diagrams.sketch import (  # noqa: E402
    SketchError,
    compile_sketch,
    parse_sketch,
)


def run_cli(*argv: str) -> tuple[int, str]:
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        code = cli_main(list(argv))
    return code, output.getvalue()


class SketchParserTests(unittest.TestCase):
    def test_chain_expansion(self):
        nodes, edges = parse_sketch("Browser -> API -> DB")
        self.assertEqual(nodes, ["Browser", "API", "DB"])
        self.assertEqual(edges, [("Browser", "API", ""), ("API", "DB", "")])

    def test_edge_labels(self):
        _, edges = parse_sketch("API -> DB [JDBC fallback]")
        self.assertEqual(edges, [("API", "DB", "JDBC fallback")])

    def test_comments_and_blank_lines(self):
        nodes, edges = parse_sketch("# comment\n\nA -> B  # trailing\n")
        self.assertEqual(nodes, ["A", "B"])
        self.assertEqual(len(edges), 1)

    def test_dedupes_nodes(self):
        nodes, edges = parse_sketch("A -> B\nB -> C")
        self.assertEqual(nodes, ["A", "B", "C"])
        self.assertEqual(len(edges), 2)

    def test_empty_rejected(self):
        with self.assertRaises(SketchError):
            parse_sketch("   \n# nothing\n")

    def test_dangling_arrow_rejected(self):
        with self.assertRaises(SketchError):
            parse_sketch("A -> ")

    def test_first_node_label_rejected(self):
        with self.assertRaises(SketchError):
            parse_sketch("A [x] -> B")

    def test_conflicting_labels_rejected(self):
        with self.assertRaises(SketchError):
            parse_sketch("A -> B [x]\nA -> B [y]")


class SketchCompileTests(unittest.TestCase):
    def test_model_passes_reference_validation(self):
        arch = compile_sketch("Browser -> API [HTTPS] -> DB [JDBC]", title="Shop")
        validate_architecture_refs(arch)
        self.assertEqual(arch["name"], "Shop")
        by_name = {c["name"]: c for c in arch["deployment"][0]["network_zones"][0]["components"]}
        self.assertEqual(set(by_name), {"Browser", "API", "DB"})
        protos = {(i["from"], i["to"]): i["protocol"] for i in arch["interactions"]}
        self.assertEqual(protos[(by_name["Browser"]["id"], by_name["API"]["id"])], "HTTPS")


class SketchDeliveryTests(unittest.TestCase):
    def test_cli_and_api(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = str(pathlib.Path(tmp) / "shop.drawio")
            model = str(pathlib.Path(tmp) / "shop.yaml")
            code, _ = run_cli("sketch", "Browser -> API -> DB", "-o", out, "--yaml", model)
            self.assertEqual(code, 0)
            self.assertTrue(pathlib.Path(out).is_file())
            arch = yaml.safe_load(pathlib.Path(model).read_text(encoding="utf-8"))
            validate_architecture_refs(arch)

            out2 = str(pathlib.Path(tmp) / "shop2.drawio")
            self.assertEqual(api.run_sketch("A -> B", output=out2), 0)
            self.assertTrue(pathlib.Path(out2).is_file())

    def test_cli_bad_sketch_exits_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _ = run_cli("sketch", "oops no arrows here",
                              "-o", str(pathlib.Path(tmp) / "x.drawio"))
            self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
