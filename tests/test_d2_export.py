"""D2 CLI PNG export: scale/timeout plumbing and fail-closed behaviour.

A very large diagram makes the d2 raster backend exit non-zero at its default
size, so ``--d2-scale`` exists to render it reliably. These tests pin the
command construction without needing the d2 binary.
"""

import contextlib
import io
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from archharness.diagrams import command  # noqa: E402

MINIMAL_ARCH = {
    "id": "demo",
    "name": "Demo",
    "deployment": [{
        "id": "dc-a",
        "type": "private_dc",
        "name": "DC",
        "network_zones": [{
            "id": "z1",
            "name": "App",
            "components": [{"id": "api", "name": "API", "type": "BE"}],
        }],
    }],
    "interactions": [],
}


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


class D2SourceResolutionTests(unittest.TestCase):
    """_export_png_via_d2 uses an explicit .d2 or compiles one on the fly."""

    def test_explicit_d2_file_is_used(self):
        captured = {}

        def fake_cli(d2_path, png_path, **_kwargs):
            captured["d2"] = d2_path
            return True

        with tempfile.TemporaryDirectory() as tmp:
            given = pathlib.Path(tmp) / "given.d2"
            given.write_text("x -> y", encoding="utf-8")
            with mock.patch.object(command, "_export_png_via_d2_cli", fake_cli):
                ok = command._export_png_via_d2(
                    MINIMAL_ARCH, str(pathlib.Path(tmp) / "o.png"), str(given))
        self.assertTrue(ok)
        self.assertEqual(captured["d2"], str(given))

    def test_compiles_a_temp_d2_when_none_is_given(self):
        captured = {}

        def fake_cli(d2_path, png_path, **_kwargs):
            captured["exists"] = pathlib.Path(d2_path).is_file()
            captured["text"] = pathlib.Path(d2_path).read_text(encoding="utf-8")
            return True

        with mock.patch.object(command, "_export_png_via_d2_cli", fake_cli):
            ok = command._export_png_via_d2(MINIMAL_ARCH, "out.png")
        self.assertTrue(ok)
        self.assertTrue(captured["exists"], "a temporary .d2 must be compiled")
        self.assertIn("direction:", captured["text"])

    def test_compile_failure_returns_false(self):
        with mock.patch("archharness.diagrams.d2_generator.generate_d2",
                        side_effect=ValueError("bad model")):
            self.assertFalse(command._export_png_via_d2(MINIMAL_ARCH, "out.png"))


class PngEngineDefaultTests(unittest.TestCase):
    """draw.io is no longer the default PNG renderer."""

    def _run(self, extra):
        calls = []

        def recorder(name):
            def record(*_args, **_kwargs):
                calls.append(name)
                return True
            return record

        with tempfile.TemporaryDirectory() as tmp:
            arch = pathlib.Path(tmp) / "arch.yaml"
            arch.write_text(yaml.safe_dump(MINIMAL_ARCH), encoding="utf-8")
            argv = ["-i", str(arch), "-o", str(pathlib.Path(tmp) / "d.drawio"),
                    "--png", str(pathlib.Path(tmp) / "d.png"), *extra]
            with mock.patch.object(command, "_export_png_via_drawio_cli", recorder("drawio")), \
                    mock.patch.object(command, "_export_png_via_d2", recorder("d2")), \
                    mock.patch.object(command, "_export_png_via_matplotlib", recorder("matplotlib")):
                with contextlib.redirect_stdout(io.StringIO()):
                    code = command.main(argv)
        return code, calls

    def test_auto_prefers_d2_and_never_drawio(self):
        code, calls = self._run([])
        self.assertEqual(code, 0)
        self.assertIn("d2", calls)
        self.assertNotIn("drawio", calls)

    def test_drawio_engine_is_still_an_explicit_opt_in(self):
        code, calls = self._run(["--png-engine", "drawio"])
        self.assertEqual(code, 0)
        self.assertIn("drawio", calls)
        self.assertNotIn("d2", calls)


if __name__ == "__main__":
    unittest.main()
