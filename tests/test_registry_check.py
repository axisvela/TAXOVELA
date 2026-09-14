"""Tests for systems-registry consistency validation."""

import contextlib
import io
import pathlib
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from archharness import registry as registry_check  # noqa: E402


REGISTRY = """# Registry

| 编号 | 源提示词名称 | 类型 | 位置 | 文档用名 | 备注 |
|------|--------------|------|------|----------|------|
| SYS-01 | Original One | backend | dc | Scrubbed One | test |
| SYS-02 | Original Two | database | dc | Scrubbed-Two | test |
| SYS-03 | Redis | cache | dc | Redis | generic |
"""


class RegistryCheckTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = pathlib.Path(self._tmp.name)
        (self.root / "input" / "documents").mkdir(parents=True)
        (self.root / "output" / "designs").mkdir(parents=True)
        (self.root / "input" / "systems-registry.md").write_text(
            REGISTRY, encoding="utf-8"
        )
        (self.root / "input" / "prompt.md").write_text(
            "Codes-only prompt: SYS-01 through SYS-03.\n",
            encoding="utf-8",
        )

    def run_check(self) -> tuple[int, str]:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = registry_check.check_example(self.root)
        return code, output.getvalue()

    def test_full_prompt_coverage_is_ok(self):
        (self.root / "input" / "prompt-indexed.md").write_text(
            "SYS-01 through SYS-03\n", encoding="utf-8"
        )
        code, output = self.run_check()
        self.assertEqual(code, 0, output)
        self.assertIn("OK (3 registry rows, 3 codes cited)", output)
        self.assertNotIn("WARN", output)

    def test_prompt_missing_registry_code_warns(self):
        (self.root / "input" / "prompt.md").write_text(
            "Codes-only prompt: SYS-01 only.\n", encoding="utf-8"
        )
        code, output = self.run_check()
        self.assertEqual(code, 0, output)
        self.assertIn("SYS-02", output)
        self.assertIn("not referenced by input/prompt.md", output)

    def test_literal_name_in_prompt_is_error(self):
        (self.root / "input" / "prompt.md").write_text(
            "Codes-only prompt: call Scrubbed-Two via SYS-01.\n", encoding="utf-8"
        )
        code, output = self.run_check()
        self.assertEqual(code, 1, output)
        self.assertIn("use the code", output)

    def test_unknown_code_is_error(self):
        (self.root / "input" / "prompt-indexed.md").write_text(
            "SYS-01 and SYS-99\n", encoding="utf-8"
        )
        code, output = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("SYS-99 cited but not in registry", output)

    def test_literal_name_in_consumer_is_error(self):
        (self.root / "input" / "prompt-indexed.md").write_text(
            "Call Scrubbed-Two through SYS-01.\n", encoding="utf-8"
        )
        code, output = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("literal doc-name 'Scrubbed-Two'", output)

    def test_generated_output_is_ignored(self):
        (self.root / "input" / "prompt-indexed.md").write_text(
            "SYS-01..SYS-03\n", encoding="utf-8"
        )
        (self.root / "output" / "designs" / "arch.yaml").write_text(
            "name: Scrubbed-Two\n", encoding="utf-8"
        )
        code, output = self.run_check()
        self.assertEqual(code, 0, output)

    def test_platform_values_are_ignored_but_notes_are_checked(self):
        (self.root / "input" / "prompt-indexed.md").write_text(
            "SYS-01–SYS-03\n", encoding="utf-8"
        )
        config = self.root / "config.yaml"
        config.write_text(
            "datacenters:\n  - notes: SYS-01\n"
            "platforms:\n  api_gateway: Scrubbed-Two\n",
            encoding="utf-8",
        )
        code, output = self.run_check()
        self.assertEqual(code, 0, output)
        config.write_text(
            "datacenters:\n  - notes: Scrubbed-Two\n"
            "platforms:\n  api_gateway: Scrubbed-Two\n",
            encoding="utf-8",
        )
        code, output = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("in config.yaml", output)

    def test_ip_address_is_error(self):
        (self.root / "input" / "prompt-indexed.md").write_text(
            "SYS-01..SYS-03\n", encoding="utf-8"
        )
        (self.root / "input" / "documents" / "requirements.md").write_text(
            "Host 192.0.2.10/24 must not appear.\n", encoding="utf-8"
        )
        code, output = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("IP address/CIDR", output)
        self.assertIn("192.0.2.10/24", output)


if __name__ == "__main__":
    unittest.main()
