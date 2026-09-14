"""Workflow state machine: artifact gating and enforce decisions."""

import contextlib
import io
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from archharness.artifacts import make_manifest  # noqa: E402
from archharness.cli import main as cli_main  # noqa: E402
from archharness.workflow import (  # noqa: E402
    WorkflowError,
    can_start,
    complete_stage,
    enforce_decision,
    load_spec,
    record_artifact,
)
from archharness.workspace import init_project, init_workspace  # noqa: E402


def run_cli(*argv: str) -> tuple[int, str]:
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        code = cli_main(list(argv))
    return code, output.getvalue()


def _manifest(path: pathlib.Path, root: pathlib.Path) -> dict:
    return make_manifest(
        artifact_id=f"art-{path.stem}",
        artifact_type="requirements",
        schema="req/v1",
        path=path,
        project_root=root,
        producer="archharness/test",
    )


def _decision(decision: str) -> dict:
    return {
        "schema_version": "enforcement/v1",
        "decision": decision,
        "validation": {"path": "d.png", "sha256": "a" * 64, "ruleset_digest": "r" * 16},
        "policy": {
            "path": "arch-gate-policy.yaml",
            "digest": "b" * 64,
            "block_threshold": 6.0,
            "warn_threshold": 8.0,
            "must_fix_zero_required": True,
        },
        "evaluation": {"total_score": 7.0, "must_fix": 0},
        "reasons": ["test"],
    }


class WorkflowEngineTests(unittest.TestCase):
    def test_spec_loads_pipeline_order(self):
        spec = load_spec()
        ids = [stage["id"] for stage in spec["pipeline"]]
        self.assertEqual(ids[0], "requirements")
        self.assertIn("enforce", ids)
        self.assertIn("report", ids)

    def test_requirements_always_ready(self):
        ok, missing, blocked = can_start("requirements", {"artifacts": {}, "stages_completed": []})
        self.assertTrue(ok)
        self.assertEqual(missing, [])
        self.assertIsNone(blocked)

    def test_design_blocked_until_req_recorded(self):
        state = {"artifacts": {}, "stages_completed": []}
        ok, missing, _ = can_start("design", state)
        self.assertFalse(ok)
        self.assertEqual(missing, ["req.yaml"])
        with self.assertRaises(WorkflowError):
            complete_stage("design", state)

    def test_unknown_stage_rejected(self):
        with self.assertRaises(WorkflowError):
            can_start("nope", {"artifacts": {}, "stages_completed": []})

    def test_security_requires_pass_or_warn(self):
        state = {"artifacts": {"validate_result.json": {"kind": "manifest", "data": {}}},
                 "stages_completed": []}
        ok, _, blocked = can_start("security", state)
        self.assertFalse(ok)
        self.assertIn("enforce", blocked)

        state["artifacts"]["enforce_result.json"] = {"kind": "decision", "data": _decision("BLOCK")}
        self.assertEqual(enforce_decision(state), "BLOCK")
        ok, _, blocked = can_start("security", state)
        self.assertFalse(ok)
        self.assertIn("BLOCK", blocked)

        state["artifacts"]["enforce_result.json"] = {"kind": "decision", "data": _decision("WARN")}
        ok, missing, blocked = can_start("security", state)
        self.assertTrue(ok)

    def test_record_verifies_manifest_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp) / "req.yaml"
            target.write_text("x: 1\n", encoding="utf-8")
            state = {"artifacts": {}, "stages_completed": []}
            manifest = _manifest(target, pathlib.Path(tmp))
            record_artifact(state, "req.yaml", manifest, tmp)
            self.assertIn("req.yaml", state["artifacts"])
            target.write_text("tampered\n", encoding="utf-8")
            with self.assertRaises(WorkflowError):
                record_artifact({"artifacts": {}, "stages_completed": []},
                                "req.yaml", manifest, tmp)


class WorkflowCliTests(unittest.TestCase):
    def test_cli_can_and_complete_flow(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            init_workspace(root)
            init_project(root, "demo", make_default=True)
            target = root / "projects" / "demo" / "output" / "requirements" / "req.yaml"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("schema_version: req/v1\n", encoding="utf-8")

            code, out = run_cli("workflow", "can", "design",
                                "--workspace", str(root), "--project", "demo")
            self.assertEqual(code, 1, out)
            self.assertIn("req.yaml", out)

            manifest = _manifest(target, root / "projects" / "demo")
            manifest_file = pathlib.Path(tmp) / "m.json"
            manifest_file.write_text(json.dumps(manifest), encoding="utf-8")
            code, out = run_cli("workflow", "record", "--name", "req.yaml",
                                "--file", str(manifest_file),
                                "--workspace", str(root), "--project", "demo")
            self.assertEqual(code, 0, out)

            code, out = run_cli("workflow", "can", "design",
                                "--workspace", str(root), "--project", "demo")
            self.assertEqual(code, 0, out)

            code, out = run_cli("workflow", "complete", "design",
                                "--workspace", str(root), "--project", "demo")
            self.assertEqual(code, 0, out)

            code, out = run_cli("workflow", "status",
                                "--workspace", str(root), "--project", "demo")
            self.assertEqual(code, 0, out)
            self.assertIn("design", out)


if __name__ == "__main__":
    unittest.main()
