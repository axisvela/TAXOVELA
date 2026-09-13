"""End-to-end provenance: CSV -> req.yaml -> artifact manifest."""

import json
import pathlib
import sys
import tempfile
import unittest

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
READERS_DIR = ROOT / "tools" / "arch-req-readers"
sys.path.insert(0, str(READERS_DIR))
sys.path.insert(0, str(ROOT))

from archharness.artifacts import verify_manifest  # noqa: E402
from archharness.schemas import validate_final_req, validate_manifest  # noqa: E402
from req_reader import main as req_main  # noqa: E402


class ReqManifestE2ETests(unittest.TestCase):
    def test_csv_to_manifest_chain(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = pathlib.Path(tmp)
            csv_path = tmpdir / "cmdb.csv"
            csv_path.write_text(
                "name,datacenter,country,platform,zone,owner,language\n"
                "Payments App,Hohhot DC,CN,private_dc,App Zone,org_it,Java\n",
                encoding="utf-8",
            )
            out = tmpdir / "req-out.yaml"
            report = tmpdir / "gaps.md"
            manifest_path = tmpdir / "req-out.manifest.json"

            argv = [
                "req_reader",
                "--csv", str(csv_path),
                "-o", str(out),
                "--report", str(report),
                "--manifest", str(manifest_path),
            ]
            previous = sys.argv
            sys.argv = argv
            try:
                req_main()
            finally:
                sys.argv = previous

            doc = yaml.safe_load(out.read_text(encoding="utf-8"))
            self.assertEqual(doc["schema_version"], "req/v1")
            validate_final_req(doc)
            self.assertEqual(doc["requirements"]["applications"][0]["name"], "Payments App")

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            validate_manifest(manifest)
            self.assertEqual(manifest["schema"], "req/v1")
            self.assertEqual(manifest["type"], "requirements")
            self.assertTrue(
                any(str(entry).endswith("cmdb.csv") for entry in manifest["input_artifacts"])
            )
            self.assertTrue(verify_manifest(manifest))

            out.write_text("tampered\n", encoding="utf-8")
            self.assertFalse(verify_manifest(manifest))


if __name__ == "__main__":
    unittest.main()
