"""Milestone 0 cleanup: tmp handling, doctor args, strict validation."""

import contextlib
import io
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from archharness.yaml_validate import validate_file  # noqa: E402
from archharness.cli import main as cli_main  # noqa: E402
from archharness.workspace import init_project, init_workspace  # noqa: E402


def run_cli(*argv: str) -> tuple[int, str, str]:
    stdout, stderr = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = cli_main(list(argv))
    return code, stdout.getvalue(), stderr.getvalue()


class YamlStrictTests(unittest.TestCase):
    def test_strict_reports_trailing_whitespace(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "sample.yaml"
            path.write_text("name: demo   \nowner: it\n", encoding="utf-8")
            result = validate_file(path, strict=True)
            self.assertTrue(result.valid)
            self.assertTrue(any("trailing whitespace" in w for w in result.warnings))

    def test_strict_reports_top_level_duplicate(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "dup.yaml"
            path.write_text("name: a\nname: b\n", encoding="utf-8")
            result = validate_file(path, strict=True)
            self.assertTrue(any("duplicate key" in w for w in result.warnings))

    def test_non_strict_ignores_whitespace(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "plain.yaml"
            path.write_text("name: demo   \n", encoding="utf-8")
            result = validate_file(path, strict=False)
            self.assertEqual(result.warnings, [])


class DoctorArgsTests(unittest.TestCase):
    def test_doctor_reports_explicit_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            init_workspace(root)
            init_project(root, "alpha", name="Alpha")
            code, output, _ = run_cli("doctor", "--workspace", str(root), "--project", "alpha")
            self.assertEqual(code, 0, output)
            self.assertIn("alpha", output)

    def test_doctor_fails_for_missing_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            init_workspace(root)
            init_project(root, "alpha", name="Alpha")
            code, output, _ = run_cli("doctor", "--workspace", str(root), "--project", "missing")
            self.assertNotEqual(code, 0)


class DoctorLayoutTests(unittest.TestCase):
    def _make_root(self, base: pathlib.Path, *, repo: bool) -> pathlib.Path:
        import shutil

        root = base / ("repo" if repo else "pkg")
        (root / "tools" / "arch-diagram-gen").mkdir(parents=True)
        (root / "tools" / "arch-req-readers").mkdir(parents=True)
        # A real checkout or wheel ships the standards and schemas, and doctor
        # now loads them rather than only checking that the directories exist.
        for directory in ("standards", "schemas"):
            shutil.copytree(ROOT / directory, root / directory)
        (root / "config.yaml").write_text("company: {}\n", encoding="utf-8")
        if repo:
            (root / ".claude" / "skills").mkdir(parents=True)
            (root / ".opencode" / "agents").mkdir(parents=True)
            (root / ".agents" / "skills").mkdir(parents=True)
        else:
            (root / "skills").mkdir(parents=True)
        return root

    def test_package_layout_is_not_repo(self):
        import os

        with tempfile.TemporaryDirectory() as tmp:
            home = self._make_root(pathlib.Path(tmp), repo=False)
            previous = os.environ.get("ARCHHARNESS_HOME")
            os.environ["ARCHHARNESS_HOME"] = str(home)
            try:
                with tempfile.TemporaryDirectory() as work:
                    old_cwd = pathlib.Path.cwd()
                    os.chdir(work)
                    try:
                        code, out, _ = run_cli("doctor")
                    finally:
                        os.chdir(old_cwd)
            finally:
                if previous is None:
                    os.environ.pop("ARCHHARNESS_HOME", None)
                else:
                    os.environ["ARCHHARNESS_HOME"] = previous
            self.assertEqual(code, 0, out)
            self.assertIn("installed package data", out)


class ReqReaderHygieneTests(unittest.TestCase):
    def test_no_unbounded_mkdtemp_leak(self):
        reader = pathlib.Path(__file__).resolve().parents[1] / "archharness" / "requirements" / "command.py"
        source = reader.read_text(encoding="utf-8")
        self.assertNotIn("tempfile.mkdtemp()", source)
        self.assertIn("TemporaryDirectory", source)


if __name__ == "__main__":
    unittest.main()
