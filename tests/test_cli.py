import contextlib
import io
import pathlib
import sys
import tempfile
import unittest

from archharness import __version__
from archharness.cli import governance_checks, main

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


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

    def test_doctor_reports_governance_inputs(self):
        code, output = run_cli("doctor")
        self.assertEqual(code, 0, output)
        self.assertIn("governance:", output)
        self.assertIn("gate policy (profiles:", output)
        self.assertIn("workflow spec", output)

    def test_governance_checks_pass_in_the_repo(self):
        problems = [problem for _label, problem in governance_checks(ROOT) if problem]

        self.assertEqual(problems, [])

    def test_governance_checks_report_a_broken_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / "standards").mkdir()
            (root / "standards" / "arch-gate-policy.yaml").write_text(
                "enforcement_bounds:\n  block_threshold: 9.0\n  warn_threshold: 6.0\n"
                "  must_fix_zero_required: true\n", encoding="utf-8")

            labels = dict(governance_checks(root))

        self.assertIn("gate policy", labels)
        self.assertIn("block_threshold <= warn_threshold", labels["gate policy"])

    def test_validate_yaml_passthrough(self):
        config = pathlib.Path(__file__).resolve().parents[1] / "config.yaml"
        code, output = run_cli("validate-yaml", str(config))
        self.assertEqual(code, 0, output)
        self.assertIn("All 1 file(s) valid", output)


if __name__ == "__main__":
    unittest.main()
