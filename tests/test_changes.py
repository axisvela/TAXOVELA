"""Change sets: semantic diff, verifiable apply, model CLI."""

import contextlib
import io
import pathlib
import sys
import tempfile
import unittest

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from archharness.changes import (  # noqa: E402
    ChangeError,
    apply_changeset,
    diff_arch,
    summarize,
)
from archharness.cli import main as cli_main  # noqa: E402
from archharness.diagrams.sketch import compile_sketch  # noqa: E402


def run_cli(*argv: str) -> tuple[int, str]:
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        code = cli_main(list(argv))
    return code, output.getvalue()


class ChangeSetTests(unittest.TestCase):
    def test_diff_detects_all_kinds(self):
        before = compile_sketch("A -> B -> C")
        after = compile_sketch("A -> B -> D")
        changeset = diff_arch(before, after)
        kinds = sorted(op["op"] for op in changeset["ops"])
        self.assertIn("add_node", kinds)
        self.assertIn("remove_node", kinds)
        lines = summarize(changeset)
        self.assertTrue(any("D" in line and line.startswith("+") for line in lines))
        self.assertTrue(any("C" in line and line.startswith("-") for line in lines))

    def test_diff_empty_for_identical(self):
        arch = compile_sketch("A -> B")
        self.assertEqual(diff_arch(arch, arch), {"ops": []})
        self.assertEqual(summarize({"ops": []}), [])

    def test_apply_round_trip(self):
        before = compile_sketch("A -> B")
        after = compile_sketch("A -> B -> C")
        result = apply_changeset(before, diff_arch(before, after))
        self.assertEqual(diff_arch(result, after), {"ops": []})

    def test_apply_is_pure(self):
        before = compile_sketch("A -> B")
        snapshot = yaml.safe_dump(before, sort_keys=True)
        apply_changeset(before, {"ops": [{"op": "add_node", "node": {"id": "x", "name": "X"}}]})
        self.assertEqual(yaml.safe_dump(before, sort_keys=True), snapshot)

    def test_apply_rejects_dangling_edge(self):
        before = compile_sketch("A -> B")
        with self.assertRaises(ChangeError):
            apply_changeset(before, {"ops": [
                {"op": "add_edge", "edge": {"from": "a", "to": "ghost"}},
            ]})

    def test_apply_rejects_unknown_op(self):
        with self.assertRaises(ChangeError):
            apply_changeset(compile_sketch("A -> B"), {"ops": [{"op": "teleport"}]})

    def test_update_node(self):
        before = compile_sketch("A -> B")
        result = apply_changeset(before, {"ops": [
            {"op": "update_node", "id": "a", "fields": {"name": "Alpha"}},
        ]})
        names = [c["name"] for z in result["deployment"][0]["network_zones"]
                 for c in z["components"]]
        self.assertIn("Alpha", names)


class ModelCliTests(unittest.TestCase):
    def test_model_diff(self):
        with tempfile.TemporaryDirectory() as tmp:
            before = pathlib.Path(tmp) / "a.yaml"
            after = pathlib.Path(tmp) / "b.yaml"
            before.write_text(yaml.safe_dump(compile_sketch("A -> B")), encoding="utf-8")
            after.write_text(yaml.safe_dump(compile_sketch("A -> C")), encoding="utf-8")
            code, out = run_cli("model", "diff", str(before), str(after))
            self.assertEqual(code, 0, out)
            self.assertIn("+ edge", out)
            self.assertIn("- edge", out)

    def test_model_diff_missing_file(self):
        code, _ = run_cli("model", "diff", "nope.yaml", "nope2.yaml")
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
