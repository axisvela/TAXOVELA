"""The declared req/v2 migration state must match the measured state."""

import contextlib
import io
import pathlib
import re
import shutil
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from archharness.migrate_status import (  # noqa: E402
    REQV1,
    REQV2_COMPLETE,
    REQV2_PARTIAL,
    SCAFFOLD,
    example_status,
    main,
)

EXAMPLES = ROOT / "examples"
EXAMPLE_NAME = re.compile(r"^\d{2}-[a-z0-9-]+$")
STATUS_TOKEN = re.compile(r"^`([a-z0-9-]+)`")


def declared_statuses() -> dict[str, str]:
    """Read the migration token from each row of the example matrix."""
    declared = {}
    for line in (EXAMPLES / "README.md").read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 5:
            continue
        name = cells[1].strip("`")
        token = STATUS_TOKEN.match(cells[4])
        if EXAMPLE_NAME.match(name) and token:
            declared[name] = token.group(1)
    return declared


class MigrationStatusTests(unittest.TestCase):
    def test_readme_matrix_matches_measured_status(self):
        declared = declared_statuses()
        self.assertTrue(declared, "example matrix did not parse")

        measured = {
            path.name: example_status(path)["status"]
            for path in sorted(p for p in EXAMPLES.iterdir() if p.is_dir())
        }
        self.assertEqual(measured, declared)

    def test_legacy_example_is_reqv1(self):
        with tempfile.TemporaryDirectory() as tmp:
            example = pathlib.Path(tmp) / "legacy"
            (example / "input").mkdir(parents=True)
            (example / "input" / "systems-registry.md").write_text(
                "| 编号 | 参考图原名 | 文档用名 |\n|---|---|---|\n| SYS-01 | F5 | F5 |\n",
                encoding="utf-8")
            self.assertEqual(example_status(example)["status"], REQV1)

    def test_migrated_example_is_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            example = pathlib.Path(tmp) / "migrated"
            (example / "input").mkdir(parents=True)
            (example / "output" / "designs").mkdir(parents=True)
            (example / "output" / "requirements").mkdir(parents=True)
            (example / "input" / "systems-registry.md").write_text(
                "| 编号 | 参考图原名 | 文档用名 |\n|---|---|---|\n| CMP-01 | F5 | edge |\n",
                encoding="utf-8")
            (example / "input" / "prompt.md").write_text("CMP-01 only.\n", encoding="utf-8")
            (example / "output" / "designs" / "blueprint.yaml").write_text(
                "arch:\n  deployment: []\n", encoding="utf-8")
            (example / "output" / "requirements" / "req.yaml").write_text(
                "schema_version: req/v2\n", encoding="utf-8")
            self.assertEqual(example_status(example)["status"], REQV2_COMPLETE)

    def test_typed_registry_with_legacy_blueprint_is_partial(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = EXAMPLES / "06-factory-mes-industrial"
            example = pathlib.Path(tmp) / "partial"
            shutil.copytree(source, example)
            blueprint = example / "output" / "designs" / "blueprint.yaml"
            blueprint.write_text(
                blueprint.read_text(encoding="utf-8").replace("CMP-01", "SYS-01", 1),
                encoding="utf-8")
            self.assertEqual(example_status(example)["status"], REQV2_PARTIAL)

    def test_cli_reports_every_example(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main([])
        self.assertEqual(code, 0)
        report = output.getvalue()
        for name in declared_statuses():
            self.assertIn(name, report)

    def test_scaffold_example_has_no_registry(self):
        for name in ("07-finance-core-banking", "08-telecom-bss"):
            path = EXAMPLES / name
            if path.is_dir():
                self.assertEqual(example_status(path)["status"], SCAFFOLD)


if __name__ == "__main__":
    unittest.main()
