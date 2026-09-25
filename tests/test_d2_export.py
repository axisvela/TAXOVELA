"""D2 CLI PNG export: scale/timeout plumbing and fail-closed behaviour.

A very large diagram makes the d2 raster backend exit non-zero at its default
size, so ``--d2-scale`` exists to render it reliably. These tests pin the
command construction without needing the d2 binary.
"""

import pathlib
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from archharness.diagrams import command  # noqa: E402


class _Completed:
    def __init__(self, returncode: int = 0):
        self.returncode = returncode


class D2ExportTests(unittest.TestCase):
    def _fake_run(self, calls, *, returncode=0, write_output=True):
        def run(argv, **kwargs):
            calls.append((argv, kwargs))
            if write_output and returncode == 0:
                pathlib.Path(argv[-1]).write_bytes(b"\x89PNG")
            return _Completed(returncode)
        return run

    def test_scale_is_forwarded_to_d2(self):
        calls = []
        with tempfile.TemporaryDirectory() as tmp:
            out = str(pathlib.Path(tmp) / "out.png")
            with mock.patch("subprocess.run", self._fake_run(calls)):
                ok = command._export_png_via_d2_cli("in.d2", out, scale=0.25)
        self.assertTrue(ok)
        argv = calls[0][0]
        self.assertIn("--layout", argv)
        self.assertIn("--scale", argv)
        self.assertEqual(argv[argv.index("--scale") + 1], "0.25")
        self.assertEqual(argv[-1], out)

    def test_scale_is_omitted_by_default(self):
        calls = []
        with tempfile.TemporaryDirectory() as tmp:
            out = str(pathlib.Path(tmp) / "out.png")
            with mock.patch("subprocess.run", self._fake_run(calls)):
                self.assertTrue(command._export_png_via_d2_cli("in.d2", out))
        self.assertNotIn("--scale", calls[0][0])

    def test_timeout_is_forwarded(self):
        calls = []
        with tempfile.TemporaryDirectory() as tmp:
            out = str(pathlib.Path(tmp) / "out.png")
            with mock.patch("subprocess.run", self._fake_run(calls)):
                command._export_png_via_d2_cli("in.d2", out, timeout=42)
        self.assertEqual(calls[0][1]["timeout"], 42)

    def test_missing_cli_returns_false(self):
        def boom(_argv, **_kwargs):
            raise FileNotFoundError("d2")

        with mock.patch("subprocess.run", boom):
            self.assertFalse(command._export_png_via_d2_cli("in.d2", "out.png"))

    def test_nonzero_exit_returns_false(self):
        calls = []
        with mock.patch("subprocess.run",
                        self._fake_run(calls, returncode=1, write_output=False)):
            self.assertFalse(command._export_png_via_d2_cli("in.d2", "out.png"))
        # Every candidate was tried before giving up.
        self.assertGreater(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
