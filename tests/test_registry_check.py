"""Tests for req/v2 multi-table systems-registry consistency validation."""

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

## Infra nodes
| 编号 | 参考图原名 | node_kind | infra_type | network_type | 父节点 | 位置/国家 | 文档用名 | 备注 |
|---|---|---|---|---|---|---|---|---|
| INF-01 | EastUS Region | region | public_cloud | prod_network | - | US | azure-eastus | hub region |
| INF-02 | vNet-A | iaas_vpc_vnet | public_cloud | prod_network | INF-01 | US | vnet-a | spoke vnet |

## Systems
| 编号 | 参考图原名 | type | owner | vendor | 文档用名 | 备注 |
|---|---|---|---|---|---|---|
| APP-01 | Orders | new | org_it | - | orders-app | |

## Components
| 编号 | 参考图原名 | 所属系统 | 子系统 | kind | layer | component_role | 静态加密 | 文档用名 | 备注 |
|---|---|---|---|---|---|---|---|---|---|
| CMP-01 | Order API | APP-01 | order | service | be | backend_service | - | order-api | |
"""

LEGACY_REGISTRY = """# Registry

| 编号 | 源提示词名称 | 类型 | 位置 | 文档用名 | 备注 |
|------|--------------|------|------|----------|------|
| SYS-01 | Original One | backend | dc | Scrubbed One | test |
| SYS-02 | Original Two | database | dc | Scrubbed-Two | test |
"""


class RegistryCheckTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = pathlib.Path(self._tmp.name)
        (self.root / "input" / "documents").mkdir(parents=True)
        (self.root / "output" / "designs").mkdir(parents=True)
        self.write_registry(REGISTRY)
        (self.root / "input" / "prompt.md").write_text(
            "Codes-only prompt: INF-01, INF-02, APP-01, CMP-01.\n",
            encoding="utf-8",
        )

    def write_registry(self, text: str) -> None:
        (self.root / "input" / "systems-registry.md").write_text(text, encoding="utf-8")

    def run_check(self) -> tuple[int, str]:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = registry_check.check_example(self.root)
        return code, output.getvalue()

    def test_full_prompt_coverage_is_ok(self):
        (self.root / "input" / "prompt-indexed.md").write_text(
            "INF-01 through INF-02, APP-01, CMP-01\n", encoding="utf-8"
        )
        code, output = self.run_check()
        self.assertEqual(code, 0, output)
        self.assertIn("OK (4 registry rows", output)
        self.assertIn("4 codes cited", output)
        self.assertNotIn("WARN", output)

    def test_prompt_missing_registry_code_warns(self):
        (self.root / "input" / "prompt.md").write_text(
            "Codes-only prompt: INF-01, INF-02, CMP-01.\n", encoding="utf-8"
        )
        code, output = self.run_check()
        self.assertEqual(code, 0, output)
        self.assertIn("APP-01", output)
        self.assertIn("not referenced by input/prompt.md", output)

    def test_out_of_scope_row_is_exempt(self):
        self.write_registry(REGISTRY.replace(
            "| orders-app | |", "| orders-app | OUT-OF-SCOPE |"))
        (self.root / "input" / "prompt.md").write_text(
            "Codes-only prompt: INF-01, INF-02, CMP-01.\n", encoding="utf-8"
        )
        code, output = self.run_check()
        self.assertEqual(code, 0, output)
        self.assertNotIn("APP-01", output)

    def test_literal_name_in_prompt_is_error(self):
        (self.root / "input" / "prompt.md").write_text(
            "Codes-only prompt: call order-api via CMP-01.\n", encoding="utf-8"
        )
        code, output = self.run_check()
        self.assertEqual(code, 1, output)
        self.assertIn("use the code", output)

    def test_unknown_code_is_error(self):
        (self.root / "input" / "prompt-indexed.md").write_text(
            "CMP-01 and INF-99\n", encoding="utf-8"
        )
        code, output = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("INF-99 cited but not in registry", output)

    def test_unknown_prefix_in_registry_is_error(self):
        self.write_registry(REGISTRY.replace(
            "| CMP-01 | Order API",
            "| ZZZ-01 | Mystery | APP-01 | - | service | be | backend_service | - | mystery | |\n"
            "| CMP-01 | Order API",
        ))
        code, output = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("ZZZ-01: unknown entity prefix", output)

    def test_generated_output_is_ignored(self):
        (self.root / "input" / "prompt-indexed.md").write_text(
            "INF-01, INF-02, APP-01, CMP-01\n", encoding="utf-8"
        )
        (self.root / "output" / "designs" / "arch.yaml").write_text(
            "name: order-api\n", encoding="utf-8"
        )
        code, output = self.run_check()
        self.assertEqual(code, 0, output)

    def test_platform_values_are_ignored_but_notes_are_checked(self):
        (self.root / "input" / "prompt-indexed.md").write_text(
            "INF-01, INF-02, APP-01, CMP-01\n", encoding="utf-8"
        )
        config = self.root / "config.yaml"
        config.write_text(
            "datacenters:\n  - notes: INF-01\n"
            "platforms:\n  api_gateway: order-api\n",
            encoding="utf-8",
        )
        code, output = self.run_check()
        self.assertEqual(code, 0, output)
        config.write_text(
            "datacenters:\n  - notes: order-api\n"
            "platforms:\n  api_gateway: order-api\n",
            encoding="utf-8",
        )
        code, output = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("in config.yaml", output)

    def test_ip_address_is_error(self):
        (self.root / "input" / "prompt-indexed.md").write_text(
            "INF-01, INF-02, APP-01, CMP-01\n", encoding="utf-8"
        )
        (self.root / "input" / "documents" / "requirements.md").write_text(
            "Host 192.0.2.10/24 must not appear.\n", encoding="utf-8"
        )
        code, output = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("IP address/CIDR", output)
        self.assertIn("192.0.2.10/24", output)

    def test_relationship_rows_are_exempt_from_prompt_coverage(self):
        self.write_registry(REGISTRY + """
## Deployments
| 编号 | 参考图原名 | 组件 | 环境 | deployment_type | location_type | infra 节点 | runtime_type | 实例数 | 文档用名 | 备注 |
|---|---|---|---|---|---|---|---|---|---|---|
| DEP-01 | App VM | CMP-01 | prod | public_cloud | public_cloud_region | INF-02 | vm | 2 | order-api-eus | |
""")
        code, output = self.run_check()
        self.assertEqual(code, 0, output)
        self.assertNotIn("DEP-01", output)

    def test_legacy_sys_registry_still_parses(self):
        self.write_registry(LEGACY_REGISTRY)
        (self.root / "input" / "prompt.md").write_text(
            "Codes-only prompt: SYS-01 and SYS-02.\n", encoding="utf-8"
        )
        code, output = self.run_check()
        self.assertEqual(code, 0, output)
        self.assertIn("OK (2 registry rows", output)
        self.assertIn("2 legacy", output)


if __name__ == "__main__":
    unittest.main()
