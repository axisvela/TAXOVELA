"""Plugin mechanism: discovery, compatibility, capabilities, contract kit."""

import contextlib
import io
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from archharness.cli import main as cli_main  # noqa: E402
from archharness.plugins import (  # noqa: E402
    PLUGIN_API_VERSION,
    PluginContractTestCase,
    PluginError,
    capabilities,
    discover_plugins,
    has_capability,
    register_plugin,
    unregister_plugin,
)


class _FakePlugin:
    name = "test-extension"
    api_version = PLUGIN_API_VERSION
    capabilities = ["policy.enforcement", "connector.demo"]


class PluginMechanismTests(unittest.TestCase):
    def tearDown(self):
        unregister_plugin("test-extension")

    def test_register_and_discover(self):
        register_plugin(_FakePlugin())
        self.assertIn("test-extension", discover_plugins())
        self.assertTrue(has_capability("policy.enforcement"))
        self.assertFalse(has_capability("policy.unknown"))
        self.assertEqual(
            capabilities()["test-extension"],
            ["policy.enforcement", "connector.demo"],
        )

    def test_incompatible_major_rejected(self):
        bad = _FakePlugin()
        bad.api_version = "2.0"
        with self.assertRaises(PluginError):
            register_plugin(bad)
        self.assertNotIn("test-extension", discover_plugins())

    def test_malformed_plugin_rejected(self):
        with self.assertRaises(PluginError):
            register_plugin(object())

    def test_unregister(self):
        register_plugin(_FakePlugin())
        unregister_plugin("test-extension")
        self.assertNotIn("test-extension", discover_plugins())


class PluginContractKitTests(PluginContractTestCase):
    __test__ = True
    plugin = _FakePlugin()


class PluginsCliTests(unittest.TestCase):
    def test_plugins_lists_capabilities(self):
        register_plugin(_FakePlugin())
        try:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = cli_main(["plugins"])
            self.assertEqual(code, 0)
            self.assertIn("test-extension", output.getvalue())
            self.assertIn("policy.enforcement", output.getvalue())
        finally:
            unregister_plugin("test-extension")


if __name__ == "__main__":
    unittest.main()
