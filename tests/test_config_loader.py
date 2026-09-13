"""Tests for tools/config_loader.py — project-level config layering."""

import contextlib
import os
import pathlib
import sys
import unittest

TOOLS_DIR = pathlib.Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import config_loader  # noqa: E402
import yaml  # noqa: E402


@contextlib.contextmanager
def chdir(path: pathlib.Path):
    previous = pathlib.Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


ROOT_CONFIG = {
    "company": {"name": "Acme Corp", "classification_prefix": "Acme"},
    "datacenters": [
        {"id": "dc-cn-primary", "aliases": ["Primary DC"], "model": "three-tier",
         "zones": ["DMZ", "App Zone", "DB Zone"], "region": "APAC-CN"},
    ],
    "platforms": {
        "api_gateway": "WSO2 API Gateway",
        "message_bus": "Kafka",
        "k8s_platform": "Internal K8s Platform",
        "integration_platforms": ["WSO2 API Gateway", "Kafka"],
        "auth_internal": "ADFS",
        "auth_external": "Enterprise ID",
    },
}

PROJECT_CONFIG = {
    "company": {"name": "Example Corp"},
    "platforms": {"api_gateway": "Azure APIM"},
    "datacenters": [
        {"id": "azure-eastus", "aliases": ["East US"], "model": "hub-spoke",
         "zones": ["Hub", "Spoke"], "region": "NA"},
    ],
}


class ConfigLayeringTests(unittest.TestCase):
    def setUp(self):
        import tempfile
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = pathlib.Path(self._tmp.name).resolve()
        # ArchHarness resource root marker: config.yaml + tools/
        (self.root / "tools").mkdir()
        (self.root / "config.yaml").write_text(
            yaml.safe_dump(ROOT_CONFIG), encoding="utf-8")
        self.project = self.root / "examples" / "demo"
        self.project.mkdir(parents=True)
        (self.project / "config.yaml").write_text(
            yaml.safe_dump(PROJECT_CONFIG), encoding="utf-8")

    def test_project_config_overrides_base(self):
        with chdir(self.project):
            cfg = config_loader.load_config()
        # overridden by project config
        self.assertEqual(cfg.company.name, "Example Corp")
        self.assertEqual(cfg.platforms.api_gateway, "Azure APIM")
        # inherited from root config
        self.assertEqual(cfg.platforms.message_bus, "Kafka")
        self.assertEqual(cfg.platforms.auth_internal, "ADFS")
        self.assertEqual(cfg.company.classification_prefix, "Acme")

    def test_project_datacenters_replace_base_list(self):
        with chdir(self.project):
            cfg = config_loader.load_config()
        self.assertEqual([d.id for d in cfg.datacenters], ["azure-eastus"])
        self.assertEqual(cfg.datacenters[0].zones, ["Hub", "Spoke"])

    def test_paths_root_stays_at_resource_root(self):
        with chdir(self.project):
            cfg = config_loader.load_config()
        self.assertEqual(cfg.paths._root, self.root)
        self.assertTrue(str(cfg.paths.standards_path).endswith("standards"))

    def test_running_at_root_loads_base_only(self):
        with chdir(self.root):
            cfg = config_loader.load_config()
        self.assertEqual(cfg.company.name, "Acme Corp")
        self.assertEqual(cfg.platforms.api_gateway, "WSO2 API Gateway")
        self.assertEqual([d.id for d in cfg.datacenters], ["dc-cn-primary"])

    def test_chain_stops_at_resource_root(self):
        # a stray config.yaml above the resource root must be ignored
        stray = self.root.parent
        stray_config = stray / "config.yaml"
        self.addCleanup(lambda: stray_config.exists() and stray_config.unlink())
        stray_config.write_text(
            yaml.safe_dump({"company": {"name": "Stray"}}), encoding="utf-8")
        with chdir(self.project):
            chain = config_loader.find_config_chain()
        self.assertEqual(chain[-1], self.root / "config.yaml")
        self.assertEqual(len(chain), 2)

    def test_explicit_path_skips_layering(self):
        with chdir(self.project):
            cfg = config_loader.load_config(self.root / "config.yaml")
        self.assertEqual(cfg.company.name, "Acme Corp")

    def test_deep_merge_semantics(self):
        base = {"a": {"x": 1, "y": 2}, "lst": [1, 2], "s": "base"}
        overlay = {"a": {"y": 3}, "lst": [9], "n": "new"}
        merged = config_loader.deep_merge(base, overlay)
        self.assertEqual(merged, {
            "a": {"x": 1, "y": 3}, "lst": [9], "s": "base", "n": "new"})


if __name__ == "__main__":
    unittest.main()
