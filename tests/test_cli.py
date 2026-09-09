import contextlib
import io
import pathlib
import unittest

from archharness import __version__
from archharness.cli import main


def run_cli(*argv: str) -> tuple[int, str]:
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        code = main(list(argv))
    return code, output.getvalue()


class CliTests(unittest.TestCase):
    def test_version(self):
        self.assertIn(__version__, __import__("archharness").__version__)

    def test_root_prints_repo_root(self):
        code, output = run_cli("root")
        expected = pathlib.Path(__file__).resolve().parents[1]
        self.assertEqual(code, 0)
        self.assertIn(str(expected), output)

    def test_doctor_passes_in_repo(self):
        code, output = run_cli("doctor")
        self.assertEqual(code, 0, output)
        self.assertIn("doctor: OK", output)

    def test_validate_yaml_passthrough(self):
        config = pathlib.Path(__file__).resolve().parents[1] / "config.yaml"
        code, output = run_cli("validate-yaml", str(config))
        self.assertEqual(code, 0, output)
        self.assertIn("All 1 file(s) valid", output)


if __name__ == "__main__":
    unittest.main()
