"""Version consistency gate: package, manifests, and README move together."""

import json
import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_repo  # noqa: E402

ERRORS = check_repo.ERRORS
check_version_consistency = check_repo.check_version_consistency


class VersionConsistencyTests(unittest.TestCase):
    def test_released_version_is_consistent(self):
        ERRORS.clear()
        check_version_consistency()
        self.assertEqual(ERRORS, [])

    def test_package_version_matches_tag_format(self):
        init = (ROOT / "archharness" / "__init__.py").read_text(encoding="utf-8")
        version = re.search(r'__version__\s*=\s*"([^"]+)"', init).group(1)
        self.assertRegex(version, r"^\d+\.\d+\.\d+$")
        self.assertIn(f"archharness-{version}-py3-none-any.whl",
                      (ROOT / "README.md").read_text(encoding="utf-8"))

    def test_drift_is_reported(self):
        import shutil
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            mirror = pathlib.Path(tmp)
            shutil.copytree(ROOT / ".claude-plugin", mirror / ".claude-plugin")
            shutil.copytree(ROOT / "plugins", mirror / "plugins")
            shutil.copytree(ROOT / "archharness", mirror / "archharness")
            shutil.copy(ROOT / "README.md", mirror / "README.md")
            manifest = mirror / ".claude-plugin" / "marketplace.json"
            doc = json.loads(manifest.read_text(encoding="utf-8"))
            doc["plugins"][0]["version"] = "0.0.0-drift"
            manifest.write_text(json.dumps(doc), encoding="utf-8")
            previous, check_repo.ROOT = check_repo.ROOT, mirror
            ERRORS.clear()
            try:
                check_version_consistency()
            finally:
                check_repo.ROOT = previous
            self.assertTrue(any("0.0.0-drift" in error for error in ERRORS))
            ERRORS.clear()

    def test_manifest_versions_match_package(self):
        init = (ROOT / "archharness" / "__init__.py").read_text(encoding="utf-8")
        version = re.search(r'__version__\s*=\s*"([^"]+)"', init).group(1)
        for manifest in (ROOT / ".claude-plugin" / "marketplace.json",
                         ROOT / "plugins" / "archharness" / ".claude-plugin" / "plugin.json"):
            doc = json.loads(manifest.read_text(encoding="utf-8"))
            versions = [doc["version"]] if "version" in doc else []
            versions += [p["version"] for p in doc.get("plugins", [])]
            for item in versions:
                self.assertEqual(item, version)


if __name__ == "__main__":
    unittest.main()
