"""Viewpoints and atomic delivery (last-good semantics)."""

import contextlib
import io
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from archharness import api  # noqa: E402
from archharness.cli import main as cli_main  # noqa: E402
from archharness.diagrams.viewpoints import (  # noqa: E402
    SUPPORTED_VIEWS,
    recommend,
    require_supported,
)
from archharness.files import atomic_write_text  # noqa: E402


def run_cli(*argv: str) -> tuple[int, str]:
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        code = cli_main(list(argv))
    return code, output.getvalue()


class ViewpointTests(unittest.TestCase):
    def test_recommend_deployment(self):
        result = recommend("where is the payment service deployed?")
        self.assertEqual(result["viewpoint"], "technical-deployment")
        self.assertTrue(result["supported"])

    def test_recommend_auth(self):
        result = recommend("how do users login with SSO tokens?")
        self.assertEqual(result["viewpoint"], "authentication-authorization")
        self.assertFalse(result["supported"])

    def test_empty_defaults_supported(self):
        result = recommend("")
        self.assertIn(result["viewpoint"], SUPPORTED_VIEWS)

    def test_require_supported(self):
        require_supported("technical-deployment")
        with self.assertRaises(ValueError):
            require_supported("data-flow")
        with self.assertRaises(ValueError):
            require_supported("nope")

    def test_view_cli(self):
        code, out = run_cli("view", "where does customer data flow?")
        self.assertEqual(code, 0)
        self.assertIn("viewpoint:", out)

    def test_sketch_rejects_unsupported_view(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _ = run_cli("sketch", "A -> B", "--view", "data-flow",
                              "-o", str(pathlib.Path(tmp) / "x.drawio"))
            self.assertEqual(code, 1)
            self.assertFalse((pathlib.Path(tmp) / "x.drawio").exists())


class AtomicWriteTests(unittest.TestCase):
    def test_replace_and_last_good(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp) / "out.drawio"
            atomic_write_text(target, "good")
            self.assertEqual(target.read_text(encoding="utf-8"), "good")
            atomic_write_text(target, "better")
            self.assertEqual(target.read_text(encoding="utf-8"), "better")

    def test_failure_preserves_last_good(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp) / "out.drawio"
            atomic_write_text(target, "good")
            with self.assertRaises(OSError):
                atomic_write_text(pathlib.Path(tmp), "boom")
            self.assertEqual(target.read_text(encoding="utf-8"), "good")
            leftovers = [p for p in pathlib.Path(tmp).iterdir() if p.suffix == ".tmp"]
            self.assertEqual(leftovers, [])

    def test_sketch_failure_preserves_last_good(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = str(pathlib.Path(tmp) / "s.drawio")
            self.assertEqual(api.run_sketch("A -> B", output=out), 0)
            before = pathlib.Path(out).read_text(encoding="utf-8")
            self.assertEqual(api.run_sketch("A -> ", output=out), 1)
            self.assertEqual(pathlib.Path(out).read_text(encoding="utf-8"), before)


if __name__ == "__main__":
    unittest.main()
