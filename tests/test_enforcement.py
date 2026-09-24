"""Deterministic gate: decision table, schema binding, and CLI exit codes."""

import contextlib
import io
import json
import pathlib
import sys
import tempfile
import unittest

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from archharness.cli import main as cli_main  # noqa: E402
from archharness.enforcement import (  # noqa: E402
    PolicyError,
    evaluate_files,
    evaluate_gate,
    load_policy,
)
from archharness.schemas import SchemaError, validate_enforcement_result  # noqa: E402

BOUNDS = {"block_threshold": 6.0, "warn_threshold": 8.0, "must_fix_zero_required": True}

POLICY_YAML = """\
enforcement_bounds:
  block_threshold: 6.0
  warn_threshold: 8.0
  must_fix_zero_required: true
"""


def _validation_doc(score: float, must_fix: int) -> dict:
    return {
        "schema_version": "validation/v1",
        "source": {
            "path": "output/diagrams/demo.png",
            "sha256": "a" * 64,
            "ruleset_digest": "r" * 16,
        },
        "dimensions": {
            "Security_Compliance": {"raw_score": score, "weight": 2.0, "weighted_score": 1.0},
        },
        "issues": [],
        "summary": {"total_score": score, "must_fix": must_fix},
    }


def run_cli(*argv: str) -> tuple[int, str]:
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        code = cli_main(list(argv))
    return code, output.getvalue()


class GateDecisionTests(unittest.TestCase):
    def test_pass(self):
        decision = evaluate_gate(_validation_doc(8.5, 0), BOUNDS)
        self.assertEqual(decision["decision"], "PASS")
        validate_enforcement_result(decision)

    def test_warn(self):
        decision = evaluate_gate(_validation_doc(7.0, 0), BOUNDS)
        self.assertEqual(decision["decision"], "WARN")

    def test_block_on_score(self):
        decision = evaluate_gate(_validation_doc(5.9, 0), BOUNDS)
        self.assertEqual(decision["decision"], "BLOCK")

    def test_block_on_must_fix(self):
        decision = evaluate_gate(_validation_doc(8.5, 1), BOUNDS)
        self.assertEqual(decision["decision"], "BLOCK")

    def test_boundaries(self):
        self.assertEqual(evaluate_gate(_validation_doc(8.0, 0), BOUNDS)["decision"], "PASS")
        self.assertEqual(evaluate_gate(_validation_doc(6.0, 0), BOUNDS)["decision"], "WARN")

    def test_invalid_validation_rejected(self):
        with self.assertRaises(SchemaError):
            evaluate_gate({"schema_version": "validation/v1"}, BOUNDS)

    def test_decision_binds_source_and_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            validation = pathlib.Path(tmp) / "v.json"
            validation.write_text(json.dumps(_validation_doc(7.5, 0)), encoding="utf-8")
            policy = pathlib.Path(tmp) / "policy.yaml"
            policy.write_text(POLICY_YAML, encoding="utf-8")
            decision = evaluate_files(validation, policy)
            self.assertEqual(decision["decision"], "WARN")
            self.assertEqual(decision["validation"]["sha256"], "a" * 64)
            self.assertEqual(len(decision["policy"]["digest"]), 64)
            validate_enforcement_result(decision)

    def test_malformed_policy_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            validation = pathlib.Path(tmp) / "v.json"
            validation.write_text(json.dumps(_validation_doc(9.0, 0)), encoding="utf-8")
            policy = pathlib.Path(tmp) / "policy.yaml"
            policy.write_text("enforcement_bounds: {block_threshold: 8.0}\n", encoding="utf-8")
            with self.assertRaises(PolicyError):
                evaluate_files(validation, policy)


class PolicyProfileTests(unittest.TestCase):
    def _policy_file(self, directory: str, document: str) -> str:
        path = pathlib.Path(directory) / "policy.yaml"
        path.write_text(document, encoding="utf-8")
        return str(path)

    def _validation(self, directory: str, score: float, must_fix: int = 0) -> str:
        doc = _validation_doc(score, must_fix)
        path = pathlib.Path(directory) / "validation.json"
        path.write_text(json.dumps(doc), encoding="utf-8")
        return str(path)

    def test_profile_tightens_the_baseline_and_is_recorded(self):
        policy_doc = (
            "enforcement_bounds:\n"
            "  block_threshold: 6.0\n  warn_threshold: 8.0\n  must_fix_zero_required: true\n"
            "default_profile: baseline\n"
            "profiles:\n"
            "  production:\n"
            "    rationale: stricter\n"
            "    block_threshold: 7.0\n    warn_threshold: 8.5\n    must_fix_zero_required: true\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            policy = self._policy_file(tmp, policy_doc)
            validation = self._validation(tmp, score=6.5)

            baseline = evaluate_files(validation, policy)
            self.assertEqual(baseline["decision"], "WARN")
            self.assertEqual(baseline["policy"]["profile"], "baseline")

            strict = evaluate_files(validation, policy, "production")
            self.assertEqual(strict["decision"], "BLOCK")
            self.assertEqual(strict["policy"]["profile"], "production")

    def test_looser_profile_requires_an_explicit_allowance(self):
        policy_doc = (
            "enforcement_bounds:\n"
            "  block_threshold: 6.0\n  warn_threshold: 8.0\n  must_fix_zero_required: true\n"
            "profiles:\n"
            "  poc:\n"
            "    block_threshold: 4.0\n    warn_threshold: 6.5\n    must_fix_zero_required: true\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            policy = self._policy_file(tmp, policy_doc)
            validation = self._validation(tmp, score=5.0)

            with self.assertRaises(PolicyError) as ctx:
                evaluate_files(validation, policy, "poc")
            self.assertIn("allow_looser", str(ctx.exception))

    def test_declared_looser_profile_applies(self):
        policy_doc = (
            "enforcement_bounds:\n"
            "  block_threshold: 6.0\n  warn_threshold: 8.0\n  must_fix_zero_required: true\n"
            "profiles:\n"
            "  poc:\n"
            "    rationale: time-boxed\n    allow_looser: true\n"
            "    block_threshold: 4.0\n    warn_threshold: 6.5\n    must_fix_zero_required: true\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            policy = self._policy_file(tmp, policy_doc)
            validation = self._validation(tmp, score=5.0)

            decision = evaluate_files(validation, policy, "poc")

            self.assertEqual(decision["decision"], "WARN")
            self.assertEqual(decision["policy"]["profile"], "poc")

    def test_unknown_profile_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            policy = self._policy_file(
                tmp,
                "enforcement_bounds:\n  block_threshold: 6.0\n  warn_threshold: 8.0\n"
                "  must_fix_zero_required: true\n")
            validation = self._validation(tmp, score=9.0)

            with self.assertRaises(PolicyError):
                evaluate_files(validation, policy, "nope")

    def test_shipped_policy_declares_its_profiles(self):
        policy = ROOT / "standards" / "arch-gate-policy.yaml"
        bounds, _digest, profile = load_policy(policy)
        self.assertEqual(profile, "baseline")
        self.assertEqual(bounds["block_threshold"], 6.0)

        strict, _digest, profile = load_policy(policy, "production")
        self.assertEqual(profile, "production")
        self.assertGreater(strict["block_threshold"], bounds["block_threshold"])


class EnforceCliTests(unittest.TestCase):
    def _write_inputs(self, tmp: str, score: float, must_fix: int) -> tuple[str, str]:
        validation = pathlib.Path(tmp) / "validate.json"
        validation.write_text(json.dumps(_validation_doc(score, must_fix)), encoding="utf-8")
        policy = pathlib.Path(tmp) / "policy.yaml"
        policy.write_text(POLICY_YAML, encoding="utf-8")
        return str(validation), str(policy)

    def test_cli_pass_warn_exit_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            validation, policy = self._write_inputs(tmp, 7.5, 0)
            code, output = run_cli("enforce", "--validation", validation, "--policy", policy)
            self.assertEqual(code, 0, output)
            self.assertIn("WARN", output)

    def test_cli_block_exits_one_and_writes_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            validation, policy = self._write_inputs(tmp, 5.0, 0)
            out = str(pathlib.Path(tmp) / "enforce.json")
            code, output = run_cli("enforce", "--validation", validation,
                                   "--policy", policy, "--output", out)
            self.assertEqual(code, 1, output)
            decision = json.loads(pathlib.Path(out).read_text(encoding="utf-8"))
            self.assertEqual(decision["decision"], "BLOCK")
            validate_enforcement_result(decision)

    def test_cli_missing_file_exits_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            policy = pathlib.Path(tmp) / "policy.yaml"
            policy.write_text(POLICY_YAML, encoding="utf-8")
            code, _ = run_cli("enforce", "--validation", str(pathlib.Path(tmp) / "nope.json"),
                              "--policy", str(policy))
            self.assertEqual(code, 2)

    def test_cli_default_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            validation = pathlib.Path(tmp) / "v.json"
            validation.write_text(json.dumps(_validation_doc(9.0, 0)), encoding="utf-8")
            code, output = run_cli("enforce", "--validation", str(validation))
            self.assertEqual(code, 0, output)
            self.assertIn("PASS", output)


if __name__ == "__main__":
    unittest.main()
